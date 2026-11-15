import pytest

from tennis_coach_app.media import inspect_video
from tennis_coach_app.ui.video_player import VideoPlayerWidget


def test_player_loads_first_frame_and_exposes_review_controls(qtbot, tmp_path, make_video) -> None:
    source = make_video(tmp_path / "fixture.mp4")
    metadata = inspect_video(source)
    player = VideoPlayerWidget()
    qtbot.addWidget(player)
    player.show()

    player.load_video(source, metadata.duration_seconds)
    qtbot.waitUntil(lambda: player.current_frame is not None, timeout=2000)

    assert player.current_frame is not None
    assert player.current_frame.timestamp_seconds == pytest.approx(0)
    assert player.canvas.pixmap() is not None
    assert player.timeline.maximum() == 200
    assert player.play_button.isEnabled()
    assert [player.speed_selector.itemData(index) for index in range(3)] == [0.25, 0.5, 1.0]
    player.shutdown()


def test_player_steps_between_actual_neighboring_frames(qtbot, tmp_path, make_video) -> None:
    source = make_video(tmp_path / "fixture.mp4")
    metadata = inspect_video(source)
    player = VideoPlayerWidget()
    qtbot.addWidget(player)
    player.load_video(source, metadata.duration_seconds)
    qtbot.waitUntil(lambda: player.current_frame is not None, timeout=2000)

    player.step_forward()
    qtbot.waitUntil(
        lambda: player.current_frame is not None
        and player.current_frame.timestamp_seconds > 0,
        timeout=2000,
    )
    assert player.current_frame.timestamp_seconds == pytest.approx(1 / 30)

    player.step_backward()
    qtbot.waitUntil(
        lambda: player.current_frame is not None
        and player.current_frame.timestamp_seconds == pytest.approx(0),
        timeout=2000,
    )
    player.shutdown()


def test_player_advances_while_playing(qtbot, tmp_path, make_video) -> None:
    source = make_video(tmp_path / "fixture.mp4", frame_pts=tuple(range(30)))
    metadata = inspect_video(source)
    player = VideoPlayerWidget()
    qtbot.addWidget(player)
    player.load_video(source, metadata.duration_seconds)
    qtbot.waitUntil(lambda: player.current_frame is not None, timeout=2000)

    player.play()
    qtbot.waitUntil(
        lambda: player.current_frame is not None
        and player.current_frame.timestamp_seconds >= 2 / 30,
        timeout=2000,
    )
    player.pause()

    assert player.play_button.text() == "Play"
    player.shutdown()
