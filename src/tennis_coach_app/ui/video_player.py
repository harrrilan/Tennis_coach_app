from __future__ import annotations

import time
from pathlib import Path

from PySide6.QtCore import QObject, Qt, QThread, QTimer, Signal, Slot
from PySide6.QtGui import QImage, QPixmap, QResizeEvent
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from tennis_coach_app.media import MediaDecodeError, VideoReader
from tennis_coach_app.models import DecodedFrame


class VideoCanvas(QLabel):
    """Aspect-preserving canvas for an orientation-corrected RGB frame."""

    def __init__(self) -> None:
        super().__init__("Import a video to begin")
        self._source_pixmap: QPixmap | None = None
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(320, 180)
        self.setStyleSheet("background: #111; color: #ddd;")

    def set_frame(self, frame: DecodedFrame) -> None:
        height, width, channels = frame.rgb.shape
        bytes_per_line = width * channels
        image = QImage(
            frame.rgb.data,
            width,
            height,
            bytes_per_line,
            QImage.Format.Format_RGB888,
        ).copy()
        self._source_pixmap = QPixmap.fromImage(image)
        self.setText("")
        self._render_scaled_pixmap()

    def resizeEvent(self, event: QResizeEvent) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._render_scaled_pixmap()

    def _render_scaled_pixmap(self) -> None:
        if self._source_pixmap is None:
            return
        target_size = self.contentsRect().size()
        self.setPixmap(
            self._source_pixmap.scaled(
                target_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )


class FrameDecodeWorker(QObject):
    """Decode one requested frame at a time outside the GUI thread."""

    frame_ready = Signal(object, int)
    failed = Signal(str, int)

    def __init__(self) -> None:
        super().__init__()
        self._path: Path | None = None
        self._reader: VideoReader | None = None

    @Slot(str, str, float, int)
    def decode(self, path: str, operation: str, timestamp_seconds: float, request_id: int) -> None:
        try:
            video_path = Path(path)
            if self._reader is None or self._path != video_path:
                self._path = video_path
                self._reader = VideoReader(video_path)

            if operation == "before":
                frame = self._reader.frame_before(timestamp_seconds)
            elif operation == "after":
                frame = self._reader.frame_after(timestamp_seconds)
            else:
                frame = self._reader.frame_at_or_after(timestamp_seconds)
            self.frame_ready.emit(frame, request_id)
        except (MediaDecodeError, OSError, ValueError) as error:
            self.failed.emit(str(error), request_id)


class VideoPlayerWidget(QWidget):
    """Timestamp-based local video player with bounded asynchronous decoding."""

    decode_requested = Signal(str, str, float, int)
    error_occurred = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.video_path: Path | None = None
        self.duration_seconds = 0.0
        self.current_frame: DecodedFrame | None = None
        self._decode_thread: QThread | None = None
        self._decode_worker: FrameDecodeWorker | None = None
        self._request_sequence = 0
        self._active_request_id: int | None = None
        self._pending_request: tuple[str, float] | None = None
        self._playing = False
        self._play_anchor_seconds = 0.0
        self._play_anchor_clock = 0.0

        self.canvas = VideoCanvas()
        self.timeline = QSlider(Qt.Orientation.Horizontal)
        self.timeline.setObjectName("videoTimeline")
        self.timeline.setRange(0, 0)
        self.timeline.sliderPressed.connect(self.pause)
        self.timeline.sliderReleased.connect(self._seek_from_timeline)

        self.time_label = QLabel("0:00.000 / 0:00.000")
        self.time_label.setObjectName("videoTimeLabel")

        self.step_back_button = QPushButton("Previous frame")
        self.step_back_button.setObjectName("stepBackButton")
        self.step_back_button.clicked.connect(self.step_backward)

        self.play_button = QPushButton("Play")
        self.play_button.setObjectName("playButton")
        self.play_button.clicked.connect(self.toggle_playback)

        self.step_forward_button = QPushButton("Next frame")
        self.step_forward_button.setObjectName("stepForwardButton")
        self.step_forward_button.clicked.connect(self.step_forward)

        self.speed_selector = QComboBox()
        self.speed_selector.setObjectName("speedSelector")
        self.speed_selector.addItem("0.25×", 0.25)
        self.speed_selector.addItem("0.5×", 0.5)
        self.speed_selector.addItem("1×", 1.0)
        self.speed_selector.setCurrentIndex(2)
        self.speed_selector.currentIndexChanged.connect(self._restart_playback_clock)

        controls = QHBoxLayout()
        controls.addWidget(self.step_back_button)
        controls.addWidget(self.play_button)
        controls.addWidget(self.step_forward_button)
        controls.addStretch()
        controls.addWidget(QLabel("Speed"))
        controls.addWidget(self.speed_selector)
        controls.addWidget(self.time_label)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas, stretch=1)
        layout.addWidget(self.timeline)
        layout.addLayout(controls)
        self.setLayout(layout)

        self._playback_timer = QTimer(self)
        self._playback_timer.setInterval(15)
        self._playback_timer.timeout.connect(self._playback_tick)
        self._set_controls_enabled(False)

    def load_video(self, path: str | Path, duration_seconds: float) -> None:
        """Load a managed video and asynchronously display its first source frame."""
        self.pause()
        self.video_path = Path(path)
        self.duration_seconds = max(0.0, duration_seconds)
        self.current_frame = None
        self.timeline.setRange(0, max(1, round(self.duration_seconds * 1000)))
        self.timeline.setValue(0)
        self._update_time_label(0.0)
        self._set_controls_enabled(True)
        self._ensure_worker()
        self._request_frame("at_or_after", 0.0)

    def toggle_playback(self) -> None:
        if self._playing:
            self.pause()
        else:
            self.play()

    def play(self) -> None:
        if self.video_path is None or self.current_frame is None:
            return
        if self.current_frame.timestamp_seconds >= self.duration_seconds - 1e-6:
            self._request_frame("at_or_after", 0.0)
            self._play_anchor_seconds = 0.0
        else:
            self._play_anchor_seconds = self.current_frame.timestamp_seconds
        self._play_anchor_clock = time.monotonic()
        self._playing = True
        self.play_button.setText("Pause")
        self._playback_timer.start()

    def pause(self) -> None:
        self._playing = False
        self._playback_timer.stop()
        self.play_button.setText("Play")

    def step_forward(self) -> None:
        self.pause()
        if self.current_frame is not None:
            self._request_frame("after", self.current_frame.timestamp_seconds)

    def step_backward(self) -> None:
        self.pause()
        if self.current_frame is not None:
            self._request_frame("before", self.current_frame.timestamp_seconds)

    def shutdown(self) -> None:
        """Stop the decoder thread before this widget is destroyed."""
        self.pause()
        if self._decode_thread is not None:
            self._decode_thread.quit()
            self._decode_thread.wait(3000)
            self._decode_thread = None
            self._decode_worker = None

    def closeEvent(self, event) -> None:  # noqa: N802
        self.shutdown()
        super().closeEvent(event)

    def _ensure_worker(self) -> None:
        if self._decode_thread is not None:
            return
        thread = QThread(self)
        worker = FrameDecodeWorker()
        worker.moveToThread(thread)
        self.decode_requested.connect(worker.decode)
        worker.frame_ready.connect(self._frame_ready)
        worker.failed.connect(self._decode_failed)
        thread.finished.connect(worker.deleteLater)
        thread.start()
        self._decode_thread = thread
        self._decode_worker = worker

    def _request_frame(self, operation: str, timestamp_seconds: float) -> None:
        if self.video_path is None:
            return
        target = min(max(0.0, timestamp_seconds), self.duration_seconds)
        if self._active_request_id is not None:
            self._pending_request = (operation, target)
            return

        self._request_sequence += 1
        self._active_request_id = self._request_sequence
        self.decode_requested.emit(
            str(self.video_path), operation, target, self._active_request_id
        )

    @Slot(object, int)
    def _frame_ready(self, frame: DecodedFrame, request_id: int) -> None:
        if request_id != self._active_request_id:
            return
        self._active_request_id = None
        self.current_frame = frame
        self.canvas.set_frame(frame)
        self.timeline.setValue(round(frame.timestamp_seconds * 1000))
        self._update_time_label(frame.timestamp_seconds)
        self._dispatch_pending_request()

    @Slot(str, int)
    def _decode_failed(self, message: str, request_id: int) -> None:
        if request_id != self._active_request_id:
            return
        self._active_request_id = None
        self.pause()
        if not message.startswith("No frame is available"):
            self.error_occurred.emit(message)
        self._dispatch_pending_request()

    def _dispatch_pending_request(self) -> None:
        if self._pending_request is None:
            return
        operation, timestamp = self._pending_request
        self._pending_request = None
        self._request_frame(operation, timestamp)

    def _seek_from_timeline(self) -> None:
        self.pause()
        self._request_frame("at_or_after", self.timeline.value() / 1000)

    def _playback_tick(self) -> None:
        elapsed = time.monotonic() - self._play_anchor_clock
        target = self._play_anchor_seconds + elapsed * self._playback_speed()
        if target >= self.duration_seconds:
            self.pause()
            target = max(0.0, self.duration_seconds - 1e-9)
        self._request_frame("at_or_after", target)

    def _restart_playback_clock(self) -> None:
        if self._playing and self.current_frame is not None:
            self._play_anchor_seconds = self.current_frame.timestamp_seconds
            self._play_anchor_clock = time.monotonic()

    def _playback_speed(self) -> float:
        return float(self.speed_selector.currentData())

    def _update_time_label(self, current_seconds: float) -> None:
        self.time_label.setText(
            f"{_format_time(current_seconds)} / {_format_time(self.duration_seconds)}"
        )

    def _set_controls_enabled(self, enabled: bool) -> None:
        self.timeline.setEnabled(enabled)
        self.step_back_button.setEnabled(enabled)
        self.play_button.setEnabled(enabled)
        self.step_forward_button.setEnabled(enabled)
        self.speed_selector.setEnabled(enabled)


def _format_time(seconds: float) -> str:
    total_milliseconds = max(0, round(seconds * 1000))
    minutes, milliseconds_in_minute = divmod(total_milliseconds, 60_000)
    whole_seconds, milliseconds = divmod(milliseconds_in_minute, 1000)
    return f"{minutes}:{whole_seconds:02d}.{milliseconds:03d}"
