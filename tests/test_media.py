import pytest

from tennis_coach_app.media import MediaDecodeError, VideoReader, inspect_video


def test_inspect_video_reads_primary_stream_metadata(tmp_path, make_video) -> None:
    source = make_video(tmp_path / "fixture.mp4", width=80, height=48)

    metadata = inspect_video(source)

    assert metadata.width == 80
    assert metadata.height == 48
    assert metadata.duration_seconds == pytest.approx(6 / 30)
    assert metadata.orientation_degrees == 0


def test_reader_yields_rgb_frames_with_source_timestamps(tmp_path, make_video) -> None:
    source = make_video(tmp_path / "fixture.mp4")
    reader = VideoReader(source)

    frames = list(reader.iter_frames())

    assert len(frames) == 6
    assert [frame.timestamp_seconds for frame in frames] == pytest.approx(
        [0, 1 / 30, 2 / 30, 3 / 30, 4 / 30, 5 / 30]
    )
    assert all(frame.rgb.shape == (48, 64, 3) for frame in frames)
    assert all(frame.rgb.dtype.name == "uint8" for frame in frames)


def test_reader_seeks_and_selects_first_frame_at_or_after_time(tmp_path, make_video) -> None:
    source = make_video(tmp_path / "fixture.mp4")
    reader = VideoReader(source)

    frame = reader.frame_at_or_after(0.05)
    bounded = list(reader.iter_frames(start_seconds=0.05, end_seconds=0.11))

    assert frame.timestamp_seconds == pytest.approx(2 / 30)
    assert [item.timestamp_seconds for item in bounded] == pytest.approx([2 / 30, 3 / 30])


def test_reader_navigates_actual_neighboring_frames(tmp_path, make_video) -> None:
    source = make_video(tmp_path / "fixture.mp4")
    reader = VideoReader(source)

    following = reader.frame_after(2 / 30)
    preceding = reader.frame_before(2 / 30)

    assert following.timestamp_seconds == pytest.approx(3 / 30)
    assert preceding.timestamp_seconds == pytest.approx(1 / 30)


def test_reader_uses_presentation_timestamps_for_variable_spacing(tmp_path, make_video) -> None:
    source = make_video(tmp_path / "variable.mp4", frame_pts=(0, 1, 3, 6))

    frames = list(VideoReader(source).iter_frames())

    assert [frame.timestamp_seconds for frame in frames] == pytest.approx(
        [0, 1 / 30, 3 / 30, 6 / 30]
    )


def test_inspection_rejects_corrupt_video(tmp_path) -> None:
    source = tmp_path / "corrupt.mp4"
    source.write_bytes(b"not an encoded video")

    with pytest.raises(MediaDecodeError, match="Could not read video metadata"):
        inspect_video(source)


def test_neighbor_navigation_reports_video_boundaries(tmp_path, make_video) -> None:
    source = make_video(tmp_path / "fixture.mp4")
    reader = VideoReader(source)

    with pytest.raises(MediaDecodeError, match="before the start"):
        reader.frame_before(0)
    with pytest.raises(MediaDecodeError, match="No frame is available after"):
        reader.frame_after(5 / 30)
