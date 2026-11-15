from __future__ import annotations

import signal
import sys
from collections.abc import Sequence

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from tennis_coach_app.ui.main_window import MainWindow


def configure_application(app: QApplication) -> None:
    """Set stable user-facing application metadata."""
    app.setApplicationDisplayName("Tennis Coach")
    app.setApplicationName("Tennis Coach")
    app.setOrganizationName("Tennis Coach")


def build_application(arguments: Sequence[str] | None = None) -> QApplication:
    """Create the Qt application and set its user-facing metadata."""
    app = QApplication(list(arguments) if arguments is not None else sys.argv)
    configure_application(app)
    return app


def install_signal_handlers(app: QApplication) -> None:
    """Allow terminal interrupt and termination signals to close Qt cleanly."""
    signal.signal(signal.SIGINT, lambda *_: app.quit())
    signal.signal(signal.SIGTERM, lambda *_: app.quit())

    # Returning to Python periodically lets it dispatch signals while Qt owns the event loop.
    signal_timer = QTimer(app)
    signal_timer.setInterval(200)
    signal_timer.timeout.connect(lambda: None)
    signal_timer.start()


def main(arguments: Sequence[str] | None = None) -> int:
    """Launch the desktop application."""
    app = build_application(arguments)
    install_signal_handlers(app)
    window = MainWindow()
    window.show()
    return app.exec()
