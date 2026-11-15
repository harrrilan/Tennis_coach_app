from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QFileDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from tennis_coach_app.models import MediaAsset
from tennis_coach_app.storage import Library, LibraryError
from tennis_coach_app.ui.video_player import VideoPlayerWidget


class MainWindow(QMainWindow):
    """Top-level window for the first application slice."""

    def __init__(self) -> None:
        super().__init__()
        self.library: Library | None = None
        self.setWindowTitle("Tennis Coach")
        self.resize(960, 640)

        heading = QLabel("Tennis Coach")
        heading.setObjectName("welcomeHeading")
        heading.setAlignment(Qt.AlignmentFlag.AlignCenter)

        description = QLabel(
            "Review your tennis movement, mark key moments, and keep a focused practice note."
        )
        description.setObjectName("welcomeDescription")
        description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        description.setWordWrap(True)

        self.library_label = QLabel("No library open")
        self.library_label.setObjectName("libraryLabel")
        self.library_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.library_label.setWordWrap(True)

        self.open_library_button = QPushButton("Open or create a library")
        self.open_library_button.setObjectName("openLibraryButton")
        self.open_library_button.clicked.connect(self._choose_library)

        self.import_video_button = QPushButton("Import video")
        self.import_video_button.setObjectName("importVideoButton")
        self.import_video_button.setEnabled(False)
        self.import_video_button.clicked.connect(self._choose_video)

        self.video_player = VideoPlayerWidget()
        self.video_player.setObjectName("videoPlayer")
        self.video_player.setVisible(False)
        self.video_player.error_occurred.connect(self.statusBar().showMessage)

        layout = QVBoxLayout()
        layout.addStretch()
        layout.addWidget(heading)
        layout.addWidget(description)
        layout.addSpacing(16)
        layout.addWidget(self.library_label)
        layout.addWidget(self.open_library_button, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.import_video_button, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.video_player, stretch=1)
        layout.addStretch()

        content = QWidget()
        content.setLayout(layout)
        self.setCentralWidget(content)
        self.statusBar().showMessage("No library open")

    def open_library(self, path: str | Path) -> Library:
        """Open an existing library or initialize an empty selected folder."""
        library = Library.open_or_create(path)
        self.library = library
        self.library_label.setText(str(library.root))
        self.import_video_button.setEnabled(True)
        media_assets = library.list_media()
        media_count = len(media_assets)
        self.statusBar().showMessage(self._library_status(media_count))
        if media_assets:
            self._load_asset(media_assets[-1])
        return library

    def import_video(self, path: str | Path) -> MediaAsset:
        """Import one local video into the active managed library."""
        if self.library is None:
            raise LibraryError("Open or create a library before importing a video.")

        asset = self.library.import_video(path)
        media_count = len(self.library.list_media())
        self.statusBar().showMessage(
            f"Imported {asset.original_filename} · {self._library_status(media_count)}"
        )
        self._load_asset(asset)
        return asset

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802
        self.video_player.shutdown()
        super().closeEvent(event)

    def _choose_library(self) -> None:
        selected_path = QFileDialog.getExistingDirectory(
            self,
            "Open or create a Tennis Coach library",
        )
        if not selected_path:
            return
        try:
            self.open_library(selected_path)
        except LibraryError as error:
            QMessageBox.critical(self, "Could not open library", str(error))

    def _choose_video(self) -> None:
        selected_path, _selected_filter = QFileDialog.getOpenFileName(
            self,
            "Import a tennis video",
            filter="Video files (*.mp4 *.MP4 *.mov *.MOV)",
        )
        if not selected_path:
            return
        try:
            self.import_video(selected_path)
        except LibraryError as error:
            QMessageBox.critical(self, "Could not import video", str(error))

    def _load_asset(self, asset: MediaAsset) -> None:
        if self.library is None or asset.duration_seconds is None:
            return
        self.video_player.setVisible(True)
        self.video_player.load_video(
            self.library.resolve_media_path(asset),
            asset.duration_seconds,
        )

    @staticmethod
    def _library_status(media_count: int) -> str:
        noun = "video" if media_count == 1 else "videos"
        return f"Library open · {media_count} {noun}"
