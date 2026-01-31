"""Main application entry point."""

import argparse
import signal
import sys

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

from asus_helper.config import Config
from asus_helper.logging import setup_logging, get_logger
from asus_helper.single_instance import ensure_single_instance
from asus_helper.bridges import (
    AsusctlBridge,
    SupergfxctlBridge,
    RyzenadjBridge,
    NvidiaSMIBridge,
)
from asus_helper.ui import MainWindow, TrayIcon


log = get_logger("app")


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        prog="asus-helper",
        description="Power management tool for ASUS laptops on Linux"
    )
    parser.add_argument(
        "-d", "--debug",
        action="store_true",
        help="Enable debug logging to console"
    )
    parser.add_argument(
        "-v", "--version",
        action="version",
        version="%(prog)s 0.1.0"
    )
    return parser.parse_args()


class Application:
    """Main application class."""
    
    def __init__(self, debug: bool = False) -> None:
        log.info("Starting ASUS Helper")
        
        self.instance_lock = ensure_single_instance()
        log.debug("Single instance lock acquired")
        
        # Create Qt application
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("ASUS Helper")
        self.app.setQuitOnLastWindowClosed(False)  # Keep running in tray
        
        # Load config
        self.config = Config()
        log.debug("Config loaded from %s", self.config.config_file)
        
        # Initialize bridges
        log.debug("Initializing bridges...")
        self.asusctl = AsusctlBridge()
        self.supergfxctl = SupergfxctlBridge()
        self.ryzenadj = RyzenadjBridge()
        self.nvidia_smi = NvidiaSMIBridge()
        
        self._log_bridge_status()
        
        # Create UI
        log.debug("Creating UI...")
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
        
        log.info("Application initialized")
    
    def _log_bridge_status(self) -> None:
        """Log which bridges are available."""
        bridges = [
            ("asusctl", self.asusctl),
            ("supergfxctl", self.supergfxctl),
            ("ryzenadj", self.ryzenadj),
            ("nvidia-smi", self.nvidia_smi),
        ]
        
        for name, bridge in bridges:
            status = "available" if bridge.is_available else "not found"
            log.info("Bridge %s: %s", name, status)
    
    def _setup_signal_handler(self) -> None:
        """Set up handler for SIGUSR1 (show window from another instance)."""
        def handle_sigusr1(signum, frame):
            log.debug("Received SIGUSR1 - showing window")
            # Use QTimer to safely call from signal handler
            QTimer.singleShot(0, self._show_window)
        
        signal.signal(signal.SIGUSR1, handle_sigusr1)
    
    def _toggle_window(self) -> None:
        """Toggle window visibility."""
        if self.window.isVisible():
            log.debug("Hiding window")
            self.window.hide()
        else:
            self._show_window()
    
    def _show_window(self) -> None:
        """Show and raise the window."""
        log.debug("Showing window")
        self.window.show()
        self.window.raise_()
        self.window.activateWindow()
    
    def _on_window_hidden(self) -> None:
        """Handle window being hidden."""
        log.debug("Window hidden")
    
    def _quit(self) -> None:
        """Quit the application."""
        log.info("Quitting application")
        self.instance_lock.release()
        self.app.quit()
    
    def run(self) -> int:
        """Run the application."""
        # Show tray icon
        self.tray.show()
        log.debug("Tray icon shown")
        
        # Show window on first launch
        self._show_window()
        
        log.info("Entering main event loop")
        return self.app.exec()


def run_app() -> None:
    """Entry point."""
    args = parse_args()
    
    # Setup logging before anything else
    setup_logging(debug=args.debug)
    
    try:
        app = Application(debug=args.debug)
        sys.exit(app.run())
    except KeyboardInterrupt:
        log.info("Interrupted by user")
        sys.exit(0)
    except Exception as e:
        log.exception("Unhandled exception: %s", e)
        sys.exit(1)
