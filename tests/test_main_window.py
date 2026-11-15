from PySide6.QtWidgets import QPushButton

from tennis_coach_app.ui.main_window import MainWindow


def test_main_window_starts_in_empty_library_state(qtbot) -> None:
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()

    assert window.windowTitle() == "Tennis Coach"
    assert window.statusBar().currentMessage() == "No library open"

    open_library = window.findChild(QPushButton, "openLibraryButton")
    assert open_library is not None
    assert open_library.isEnabled()

    import_video = window.findChild(QPushButton, "importVideoButton")
    assert import_video is not None
    assert not import_video.isEnabled()


def test_window_opens_library_and_imports_video(qtbot, tmp_path, make_video) -> None:
    source = tmp_path / "forehand.mp4"
    make_video(source)
    window = MainWindow()
    qtbot.addWidget(window)

    library = window.open_library(tmp_path / "library")
    asset = window.import_video(source)

    assert window.library == library
    assert window.import_video_button.isEnabled()
    assert window.library_label.text() == str(library.root)
    assert library.resolve_media_path(asset).read_bytes() == source.read_bytes()
    assert window.statusBar().currentMessage() == "Imported forehand.mp4 · Library open · 1 video"
    qtbot.waitUntil(lambda: window.video_player.current_frame is not None, timeout=2000)
    assert window.video_player.isVisibleTo(window)
    window.close()
