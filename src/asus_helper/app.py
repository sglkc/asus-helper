"""Main application entry point."""

import signal
import sys

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

from asus_helper.config import Config
from asus_helper.single_instance import ensure_single_instance
from asus_helper.bridges import (
    AsusctlBridge,
    SupergfxctlBridge,
    RyzenadjBridge,
    NvidiaSMIBridge,
)
from asus_helper.ui import MainWindow, TrayIcon


class Application:
    """Main application class."""
    
    def __init__(self) -> None:
        self.instance_lock = ensure_single_instance()
        
        # Create Qt application
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("ASUS Helper")
        self.app.setQuitOnLastWindowClosed(False)  # Keep running in tray
        
        # Load config
        self.config = Config()
        
        # Initialize bridges
        self.asusctl = AsusctlBridge()
        self.supergfxctl = SupergfxctlBridge()
        self.ryzenadj = RyzenadjBridge()
        self.nvidia_smi = NvidiaSMIBridge()
        
        self._log_bridge_status()
        
        # Create UI
        self.window = MainWindow(
            self.config,
            self.asusctl,
            self.supergfxctl,
            self.ryzenadj,
            self.nvidia_smi,
        )
        
        self.tray = TrayIcon(self.config)
        
        # Connect signals
        self.tray.show_requested.connect(self._toggle_window)
        self.tray.quit_requested.connect(self._quit)
        self.window.hide_requested.connect(self._on_window_hidden)
        
        # Handle SIGUSR1 for single-instance activation
        self._setup_signal_handler()
    
    def _log_bridge_status(self) -> None:
        """Log which bridges are available."""
        bridges = [
            ("asusctl", self.asusctl),
            ("supergfxctl", self.supergfxctl),
            ("ryzenadj", self.ryzenadj),
            ("nvidia-smi", self.nvidia_smi),
        ]
        
        available = [name for name, bridge in bridges if bridge.is_available]
        unavailable = [name for name, bridge in bridges if not bridge.is_available]
        
        if available:
            print(f"Available: {', '.join(available)}")
        if unavailable:
            print(f"Not found: {', '.join(unavailable)}")
    
    def _setup_signal_handler(self) -> None:
        """Set up handler for SIGUSR1 (show window from another instance)."""
        def handle_sigusr1(signum, frame):
            # Use QTimer to safely call from signal handler
            QTimer.singleShot(0, self._show_window)
        
        signal.signal(signal.SIGUSR1, handle_sigusr1)
    
    def _toggle_window(self) -> None:
        """Toggle window visibility."""
        if self.window.isVisible():
            self.window.hide()
        else:
            self._show_window()
    
    def _show_window(self) -> None:
        """Show and raise the window."""
        self.window.show()
        self.window.raise_()
        self.window.activateWindow()
    
    def _on_window_hidden(self) -> None:
        """Handle window being hidden."""
        pass  # Could show a notification on first hide
    
    def _quit(self) -> None:
        """Quit the application."""
        self.instance_lock.release()
        self.app.quit()
    
    def run(self) -> int:
        """Run the application."""
        # Show tray icon
        self.tray.show()
        
        # Show window on first launch
        self._show_window()
        
        return self.app.exec()


def run_app() -> None:
    """Entry point."""
    try:
        app = Application()
        sys.exit(app.run())
    except KeyboardInterrupt:
        sys.exit(0)
