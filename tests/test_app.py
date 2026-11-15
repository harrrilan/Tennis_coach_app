import signal

from PySide6.QtCore import QTimer

from tennis_coach_app import __version__
from tennis_coach_app.app import configure_application, install_signal_handlers


def test_package_has_initial_version() -> None:
    assert __version__ == "0.1.0"


def test_application_metadata(qapp) -> None:
    configure_application(qapp)

    assert qapp.applicationDisplayName() == "Tennis Coach"
    assert qapp.applicationName() == "Tennis Coach"
    assert qapp.organizationName() == "Tennis Coach"


def test_signal_handlers_create_active_timer(qapp, monkeypatch) -> None:
    registered_signals = []
    monkeypatch.setattr(
        "tennis_coach_app.app.signal.signal",
        lambda signal_number, _handler: registered_signals.append(signal_number),
    )

    install_signal_handlers(qapp)

    assert registered_signals == [signal.SIGINT, signal.SIGTERM]
    assert any(timer.isActive() for timer in qapp.findChildren(QTimer))
