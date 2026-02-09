"""System tray icon."""

from PyQt6.QtWidgets import (
    QSystemTrayIcon,
    QMenu,
)
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import pyqtSignal, QObject

from asus_helper.config import Config


class TrayIcon(QObject):
    """System tray icon with context menu."""

    # Signals
    show_requested = pyqtSignal()
    quit_requested = pyqtSignal()

    def __init__(self, config: Config, parent: QObject | None = None) -> None:
        super().__init__(parent)

        self.config = config
        self._tray = QSystemTrayIcon(self)

        self._setup_icon()
        self._setup_menu()
        self._connect_signals()

    def _setup_icon(self) -> None:
        """Set up the tray icon."""
        # Use a standard icon as placeholder
        # On KDE, this will use the system theme icon
        icon = QIcon.fromTheme("preferences-system-power-management")
        if icon.isNull():
            # Fallback to another common icon
            icon = QIcon.fromTheme("system-run")
        if icon.isNull():
            # Last resort - use application icon
            icon = QIcon.fromTheme("application-x-executable")

        self._tray.setIcon(icon)
        self._tray.setToolTip("ASUS Helper")

    def _setup_menu(self) -> None:
        """Set up the context menu."""
        menu = QMenu()

        # Show action
        show_action = QAction("Show", self)
        show_action.triggered.connect(self.show_requested.emit)
        menu.addAction(show_action)

        menu.addSeparator()

        # Profile submenu
        profile_menu = menu.addMenu("Profiles")
        for name in self.config.get_profile_names():
            action = QAction(name.capitalize(), self)
            action.triggered.connect(
                lambda checked, n=name: self._on_profile_selected(n)
            )
            profile_menu.addAction(action)

        menu.addSeparator()

        # Quit action
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.quit_requested.emit)
        menu.addAction(quit_action)

        self._tray.setContextMenu(menu)

    def _connect_signals(self) -> None:
        """Connect tray icon signals."""
        self._tray.activated.connect(self._on_activated)

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        """Handle tray icon activation."""
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            # Left click - toggle window
            self.show_requested.emit()
        elif reason == QSystemTrayIcon.ActivationReason.MiddleClick:
            # Middle click - could be used for quick action
            pass

    def _on_profile_selected(self, name: str) -> None:
        """Handle profile selection from menu."""
        self.config.set_current_profile(name)
        # TODO: Apply profile

    def show(self) -> None:
        """Show the tray icon."""
        self._tray.show()

    def hide(self) -> None:
        """Hide the tray icon."""
        self._tray.hide()

    def showMessage(self, title: str, message: str) -> None:
        """Show a notification message."""
        self._tray.showMessage(title, message)
