from __future__ import annotations

from collections.abc import Iterator
from fractions import Fraction
from pathlib import Path

import av
import numpy as np
from av.container import InputContainer
from av.video.stream import VideoStream

from tennis_coach_app.models import DecodedFrame, MediaMetadata


class MediaDecodeError(Exception):
    """Raised when a video cannot provide reliable timestamped frames."""


def inspect_video(path: str | Path) -> MediaMetadata:
    """Inspect the primary video stream without decoding the whole file."""
    video_path = Path(path)
    try:
        with av.open(str(video_path), mode="r") as container:
            stream = _primary_video_stream(container)
            orientation = _orientation_degrees(stream)
            width, height = stream.width, stream.height
            if orientation in {90, 270}:
                width, height = height, width
            duration = _duration_seconds(container, stream)
    except (av.FFmpegError, OSError, ValueError) as error:
        raise MediaDecodeError(f"Could not read video metadata: {error}") from error

    if width <= 0 or height <= 0:
        raise MediaDecodeError("The video reports invalid dimensions.")
    if duration <= 0:
        raise MediaDecodeError("The video does not report a usable duration.")

    return MediaMetadata(
        width=width,
        height=height,
        duration_seconds=duration,
        orientation_degrees=orientation,
    )


class VideoReader:
    """Open-on-demand reader that selects frames by source presentation time."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.metadata = inspect_video(self.path)

    def frame_at_or_after(self, timestamp_seconds: float) -> DecodedFrame:
        """Return the first decoded frame at or after the requested source time."""
        if timestamp_seconds < 0:
            raise ValueError("timestamp_seconds must be non-negative")
        try:
            return next(self.iter_frames(start_seconds=timestamp_seconds))
        except StopIteration as error:
            raise MediaDecodeError(
                f"No frame is available at or after {timestamp_seconds:.3f} seconds."
            ) from error

    def frame_after(self, timestamp_seconds: float) -> DecodedFrame:
        """Return the decoded frame immediately following the supplied source time."""
        if timestamp_seconds < 0:
            raise ValueError("timestamp_seconds must be non-negative")
        for frame in self.iter_frames(start_seconds=timestamp_seconds):
            if frame.timestamp_seconds > timestamp_seconds + 1e-9:
                return frame
        raise MediaDecodeError(f"No frame is available after {timestamp_seconds:.3f} seconds.")

    def frame_before(self, timestamp_seconds: float) -> DecodedFrame:
        """Return the decoded frame immediately preceding the supplied source time."""
        if timestamp_seconds <= 0:
            raise MediaDecodeError("No frame is available before the start of the video.")

        try:
            with av.open(str(self.path), mode="r") as container:
                stream = _primary_video_stream(container)
                stream.thread_type = "AUTO"
                orientation = _orientation_degrees(stream)
                target_offset = int(Fraction(str(timestamp_seconds)) / stream.time_base)
                seek_offset = max(0, target_offset - 1)
                container.seek(seek_offset, stream=stream, backward=True, any_frame=False)

                previous: DecodedFrame | None = None
                for frame in container.decode(stream):
                    decoded = _decoded_frame(frame, orientation)
                    if decoded.timestamp_seconds >= timestamp_seconds - 1e-9:
                        break
                    previous = decoded
                if previous is not None:
                    return previous
        except MediaDecodeError:
            raise
        except (av.FFmpegError, OSError, ValueError) as error:
            raise MediaDecodeError(f"Could not decode the video: {error}") from error

        raise MediaDecodeError(f"No frame is available before {timestamp_seconds:.3f} seconds.")

    def iter_frames(
        self,
        *,
        start_seconds: float = 0.0,
        end_seconds: float | None = None,
    ) -> Iterator[DecodedFrame]:
        """Yield decoded frames in presentation order for a bounded source-time range."""
        if start_seconds < 0:
            raise ValueError("start_seconds must be non-negative")
        if end_seconds is not None and end_seconds < start_seconds:
            raise ValueError("end_seconds must be at or after start_seconds")

        try:
            with av.open(str(self.path), mode="r") as container:
                stream = _primary_video_stream(container)
                stream.thread_type = "AUTO"
                orientation = _orientation_degrees(stream)
                if start_seconds > 0:
                    seek_offset = int(Fraction(str(start_seconds)) / stream.time_base)
                    container.seek(seek_offset, stream=stream, backward=True, any_frame=False)

                for frame in container.decode(stream):
                    if frame.pts is None or frame.time_base is None:
                        raise MediaDecodeError(
                            "A decoded frame has no presentation timestamp; "
                            "precise review is unavailable."
                        )
                    timestamp = float(frame.pts * frame.time_base)
                    if timestamp + 1e-9 < start_seconds:
                        continue
                    if end_seconds is not None and timestamp > end_seconds + 1e-9:
                        break

                    yield _decoded_frame(frame, orientation)
        except MediaDecodeError:
            raise
        except (av.FFmpegError, OSError, ValueError) as error:
            raise MediaDecodeError(f"Could not decode the video: {error}") from error


def _primary_video_stream(container: InputContainer) -> VideoStream:
    if not container.streams.video:
        raise MediaDecodeError("The selected file contains no video stream.")
    return container.streams.video[0]


def _duration_seconds(container: InputContainer, stream: VideoStream) -> float:
    if stream.duration is not None and stream.time_base is not None:
        return float(stream.duration * stream.time_base)
    if container.duration is not None:
        return float(container.duration / av.time_base)
    raise MediaDecodeError("The video duration is unavailable.")


def _orientation_degrees(stream: VideoStream) -> int:
    raw_rotation = stream.metadata.get("rotate", stream.metadata.get("rotation", "0"))
    try:
        rotation = float(raw_rotation)
    except (TypeError, ValueError) as error:
        raise MediaDecodeError(f"Unsupported orientation metadata: {raw_rotation!r}") from error

    normalized = rotation % 360
    nearest_right_angle = int(round(normalized / 90) * 90) % 360
    difference = abs(normalized - nearest_right_angle)
    circular_difference = min(difference, 360 - difference)
    if circular_difference > 0.01:
        raise MediaDecodeError(f"Unsupported video rotation: {rotation} degrees")
    return nearest_right_angle


def _apply_orientation(image: np.ndarray, orientation_degrees: int) -> np.ndarray:
    if orientation_degrees == 90:
        return np.ascontiguousarray(np.rot90(image, k=3))
    if orientation_degrees == 180:
        return np.ascontiguousarray(np.rot90(image, k=2))
    if orientation_degrees == 270:
        return np.ascontiguousarray(np.rot90(image, k=1))
    return np.ascontiguousarray(image)


def _decoded_frame(frame: av.VideoFrame, orientation: int) -> DecodedFrame:
    if frame.pts is None or frame.time_base is None:
        raise MediaDecodeError(
            "A decoded frame has no presentation timestamp; precise review is unavailable."
        )
    image = _apply_orientation(frame.to_ndarray(format="rgb24"), orientation)
    return DecodedFrame(
        timestamp_seconds=float(frame.pts * frame.time_base),
        presentation_timestamp=frame.pts,
        time_base_numerator=frame.time_base.numerator,
        time_base_denominator=frame.time_base.denominator,
        rgb=image,
    )
