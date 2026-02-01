"""Main popup window."""

from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QGroupBox,
    QPushButton,
    QSlider,
    QSizePolicy,
)
from typing import Any, Callable

from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QCloseEvent, QScreen

from asus_helper.config import Config
from asus_helper.bridges import (
    AsusctlBridge,
    SupergfxctlBridge,
    RyzenadjBridge,
    NvidiaSMIBridge,
)


class ModeButton(QPushButton):
    """A toggle button for mode selection (like Silent/Balanced/Turbo)."""
    
    def __init__(self, text: str, icon_text: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setText(text)
        self.setCheckable(True)
        self.setMinimumWidth(80)
        self.setMinimumHeight(50)


class SliderWithValue(QWidget):
    """A slider with a label showing the current value."""
    
    valueChanged = pyqtSignal(int)
    
    def __init__(
        self,
        label: str,
        min_val: int,
        max_val: int,
        unit: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.unit = unit
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.label = QLabel(label)
        self.label.setMinimumWidth(100)
        layout.addWidget(self.label)
        
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(min_val)
        self.slider.setMaximum(max_val)
        self.slider.valueChanged.connect(self._on_value_changed)
        layout.addWidget(self.slider, stretch=1)
        
        self.value_label = QLabel()
        self.value_label.setFixedWidth(70)
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self.value_label)
        
        self._update_value_label()
    
    def _on_value_changed(self, value: int) -> None:
        self._update_value_label()
        self.valueChanged.emit(value)
    
    def _update_value_label(self) -> None:
        self.value_label.setText(f"{self.slider.value()}{self.unit}")
    
    def value(self) -> int:
        return self.slider.value()
    
    def setValue(self, value: int) -> None:
        self.slider.setValue(value)


class Debouncer:
    """Debounce function calls using QTimer.
    
    Delays execution until a period of inactivity, avoiding spam
    when sliders are being dragged.
    """
    
    def __init__(self, delay_ms: int = 300) -> None:
        """Initialize debouncer.
        
        Args:
            delay_ms: Delay in milliseconds before executing.
        """
        self.delay_ms = delay_ms
        self._timers: dict[str, QTimer] = {}
        self._pending: dict[str, tuple] = {}
    
    def call(self, key: str, func: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
        """Schedule a debounced function call.
        
        Args:
            key: Unique key to identify this debounced action.
            func: Function to call after debounce period.
            *args, **kwargs: Arguments to pass to function.
        """
        # Store pending call
        self._pending[key] = (func, args, kwargs)
        
        # Create or restart timer
        if key not in self._timers:
            timer = QTimer()
            timer.setSingleShot(True)
            timer.timeout.connect(lambda: self._execute(key))
            self._timers[key] = timer
        
        # Reset timer
        self._timers[key].stop()
        self._timers[key].start(self.delay_ms)
    
    def _execute(self, key: str) -> None:
        """Execute the pending call for given key."""
        if key in self._pending:
            func, args, kwargs = self._pending.pop(key)
            func(*args, **kwargs)

class MainWindow(QMainWindow):
    """Main application window - popup style."""
    
    # Signal emitted when window wants to hide (close button)
    hide_requested = pyqtSignal()
    
    def __init__(
        self,
        config: Config,
        asusctl: AsusctlBridge,
        supergfxctl: SupergfxctlBridge,
        ryzenadj: RyzenadjBridge,
        nvidia_smi: NvidiaSMIBridge,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        
        self.config = config
        self.asusctl = asusctl
        self.supergfxctl = supergfxctl
        self.ryzenadj = ryzenadj
        self.nvidia_smi = nvidia_smi
        
        # Debouncer for slider commands (300ms delay)
        self._debouncer = Debouncer(delay_ms=300)
        
        self._setup_window()
        self._setup_ui()
        self._load_current_state()
    
    def _setup_window(self) -> None:
        """Configure window properties."""
        self.setWindowTitle("ASUS Helper")
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowStaysOnTopHint
        )
        # Set a reasonable default size - wider to fit labels
        self.setMinimumWidth(400)
        self.resize(420, 550)
    
    def _position_bottom_right(self) -> None:
        """Position the window at the bottom-right corner of the screen."""
        screen = self.screen()
        if screen is None:
            return
        
        screen_geometry = screen.availableGeometry()
        window_geometry = self.frameGeometry()
        
        # Calculate bottom-right position with some margin
        margin = 10
        x = screen_geometry.right() - window_geometry.width() - margin
        y = screen_geometry.bottom() - window_geometry.height() - margin
        
        self.move(x, y)
    
    # type: ignore
    def showEvent(self, event) -> None:
        """Handle show event to position window."""
        super().showEvent(event)
        self._position_bottom_right()
    
    def _setup_ui(self) -> None:
        """Build the UI."""
        central = QWidget()
        self.setCentralWidget(central)
        
        layout = QVBoxLayout(central)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Power Profile section (asusctl) - also serves as profile selector
        if self.asusctl.is_available:
            layout.addWidget(self._create_power_profile_section())
        
        # GPU Mode section (supergfxctl)
        if self.supergfxctl.is_available:
            layout.addWidget(self._create_gpu_mode_section())
        
        # CPU Power section (ryzenadj)
        if self.ryzenadj.is_available:
            layout.addWidget(self._create_cpu_section())
        
        # GPU Power section (nvidia-smi)
        if self.nvidia_smi.is_available:
            layout.addWidget(self._create_nvidia_section())
        
        # Keyboard section (asusctl)
        if self.asusctl.is_available:
            layout.addWidget(self._create_keyboard_section())
        
        # Battery section (asusctl)
        if self.asusctl.is_available:
            layout.addWidget(self._create_battery_section())
        
        # Show warning if no bridges available
        if not any([
            self.asusctl.is_available,
            self.supergfxctl.is_available,
            self.ryzenadj.is_available,
            self.nvidia_smi.is_available,
        ]):
            no_tools = QLabel(
                "⚠️ No control tools found.\n\n"
                "Install one or more of:\n"
                "• asusctl\n"
                "• supergfxctl\n"
                "• ryzenadj\n"
                "• nvidia-smi"
            )
            no_tools.setWordWrap(True)
            layout.addWidget(no_tools)
        
        layout.addStretch()
    
    def _create_power_profile_section(self) -> QGroupBox:
        """Create power profile selection section.
        
        Also serves as the main profile selector - clicking applies all settings.
        """
        group = QGroupBox("⚡ Profile")
        layout = QHBoxLayout(group)
        
        self.profile_buttons: dict[str, ModeButton] = {}
        
        # Use actual asusctl profile names
        for profile, label in [
            ("LowPower", "Silent"),
            ("Balanced", "Balanced"),
            ("Performance", "Turbo"),
        ]:
            btn = ModeButton(label)
            btn.clicked.connect(lambda checked, p=profile: self._on_power_profile_clicked(p))
            self.profile_buttons[profile] = btn
            layout.addWidget(btn)
        
        return group
    
    def _create_gpu_mode_section(self) -> QGroupBox:
        """Create GPU mode selection section."""
        group = QGroupBox("GPU Mode")
        layout = QHBoxLayout(group)
        
        self.gpu_buttons: dict[str, ModeButton] = {}
        
        for mode, label in [
            ("integrated", "Eco"),
            ("hybrid", "Hybrid"),
            ("dedicated", "dGPU"),
        ]:
            btn = ModeButton(label)
            btn.clicked.connect(lambda checked, m=mode: self._on_gpu_mode_clicked(m))
            self.gpu_buttons[mode] = btn
            layout.addWidget(btn)
        
        return group
    
    def _create_cpu_section(self) -> QGroupBox:
        """Create CPU power control section.
        
        Uses asusctl armoury attributes for min/max limits,
        but applies via ryzenadj for lower minimum power.
        """
        group = QGroupBox("⚡ CPU Power")
        layout = QVBoxLayout(group)
        
        # Get limits from asusctl armoury (min lowered by 5W)
        limits = self.asusctl.get_cpu_power_limits()
        
        # Sustained power limit (STAPM)
        sustained = limits.get("sustained", {"min": 10, "max": 35})
        self.cpu_sustained_slider = SliderWithValue(
            "Sustained", sustained["min"], sustained["max"], "W"
        )
        self.cpu_sustained_slider.valueChanged.connect(self._on_cpu_sustained_changed)
        layout.addWidget(self.cpu_sustained_slider)
        
        # Short boost power limit
        short = limits.get("short", {"min": 20, "max": 45})
        self.cpu_short_slider = SliderWithValue(
            "Short Boost", short["min"], short["max"], "W"
        )
        self.cpu_short_slider.valueChanged.connect(self._on_cpu_short_changed)
        layout.addWidget(self.cpu_short_slider)
        
        # Fast boost power limit
        fast = limits.get("fast", {"min": 30, "max": 65})
        self.cpu_fast_slider = SliderWithValue(
            "Fast Boost", fast["min"], fast["max"], "W"
        )
        self.cpu_fast_slider.valueChanged.connect(self._on_cpu_fast_changed)
        layout.addWidget(self.cpu_fast_slider)
        
        # Temperature limit
        self.cpu_temp_slider = SliderWithValue("Temp Limit", 60, 100, "°C")
        self.cpu_temp_slider.valueChanged.connect(self._on_cpu_temp_changed)
        layout.addWidget(self.cpu_temp_slider)
        
        return group
    
    def _create_nvidia_section(self) -> QGroupBox:
        """Create NVIDIA GPU control section."""
        group = QGroupBox("NVIDIA GPU")
        layout = QVBoxLayout(group)
        
        # GPU info
        state = self.nvidia_smi.get_current_state()
        if state.get("gpu_name"):
            layout.addWidget(QLabel(f"<i>{state['gpu_name']}</i>"))
        
        self.gpu_clock_min_slider = SliderWithValue("Min Clock", 200, 1500, " MHz")
        self.gpu_clock_min_slider.valueChanged.connect(self._on_gpu_clock_changed)
        layout.addWidget(self.gpu_clock_min_slider)
        
        self.gpu_clock_max_slider = SliderWithValue("Max Clock", 500, 2500, " MHz")
        self.gpu_clock_max_slider.valueChanged.connect(self._on_gpu_clock_changed)
        layout.addWidget(self.gpu_clock_max_slider)
        
        self.gpu_temp_slider = SliderWithValue("Temp Limit", 60, 95, "°C")
        self.gpu_temp_slider.valueChanged.connect(self._on_gpu_temp_changed)
        layout.addWidget(self.gpu_temp_slider)
        
        return group
    
    def _create_keyboard_section(self) -> QGroupBox:
        """Create keyboard backlight section."""
        group = QGroupBox("Keyboard")
        layout = QHBoxLayout(group)
        
        layout.addWidget(QLabel("Brightness"))
        
        # LED levels: off, low, med, high (0-3)
        self.kbd_brightness_slider = QSlider(Qt.Orientation.Horizontal)
        self.kbd_brightness_slider.setMinimum(0)
        self.kbd_brightness_slider.setMaximum(3)
        self.kbd_brightness_slider.valueChanged.connect(self._on_kbd_brightness_changed)
        layout.addWidget(self.kbd_brightness_slider, stretch=1)
        
        self.kbd_brightness_label = QLabel("off")
        self.kbd_brightness_label.setMinimumWidth(40)
        layout.addWidget(self.kbd_brightness_label)
        
        return group
    
    def _create_battery_section(self) -> QGroupBox:
        """Create battery charge limit section."""
        group = QGroupBox("Battery")
        layout = QVBoxLayout(group)
        
        # Charge limit slider
        limit_row = QHBoxLayout()
        limit_row.addWidget(QLabel("Charge Limit"))
        
        self.battery_limit_slider = QSlider(Qt.Orientation.Horizontal)
        self.battery_limit_slider.setMinimum(20)
        self.battery_limit_slider.setMaximum(100)
        self.battery_limit_slider.setSingleStep(5)
        self.battery_limit_slider.valueChanged.connect(self._on_battery_limit_changed)
        limit_row.addWidget(self.battery_limit_slider, stretch=1)
        
        self.battery_limit_label = QLabel("60%")
        self.battery_limit_label.setMinimumWidth(45)
        limit_row.addWidget(self.battery_limit_label)
        
        layout.addLayout(limit_row)
        
        # Oneshot button
        self.battery_oneshot_btn = QPushButton("⚡ Full Charge (One-Shot)")
        self.battery_oneshot_btn.setToolTip("Charge to 100% once, then return to normal limit")
        self.battery_oneshot_btn.clicked.connect(self._on_battery_oneshot_clicked)
        layout.addWidget(self.battery_oneshot_btn)
        
        return group
    
    def _get_current_profile_name(self) -> str:
        """Get the current profile name."""
        return self.config.get("general", "current_profile", default="Balanced")
    
    def _load_current_state(self) -> None:
        """Load current state from hardware."""
        # Load power profile and keyboard state
        if self.asusctl.is_available:
            profile = self.asusctl.get_power_profile()
            if profile and profile in self.profile_buttons:
                self._set_active_button(self.profile_buttons, profile)
            
            # LED brightness is a string: off, low, med, high
            led_level = self.asusctl.get_keyboard_brightness()
            if led_level:
                led_levels = ["off", "low", "med", "high"]
                if led_level in led_levels:
                    self.kbd_brightness_slider.setValue(led_levels.index(led_level))
                    self.kbd_brightness_label.setText(led_level)
            
            # Battery charge limit
            battery_limit = self.asusctl.get_battery_limit()
            if battery_limit is not None:
                self.battery_limit_slider.setValue(battery_limit)
                self.battery_limit_label.setText(f"{battery_limit}%")
        
        # Load GPU mode
        if self.supergfxctl.is_available:
            mode = self.supergfxctl.get_gpu_mode()
            if mode and mode in self.gpu_buttons:
                self._set_active_button(self.gpu_buttons, mode)
        
        # Load CPU state
        if self.ryzenadj.is_available:
            state = self.ryzenadj.get_current_state()
            if state.get("stapm_limit"):
                self.cpu_sustained_slider.setValue(state["stapm_limit"])
            if state.get("slow_limit"):
                self.cpu_short_slider.setValue(state["slow_limit"])
            if state.get("fast_limit"):
                self.cpu_fast_slider.setValue(state["fast_limit"])
            if state.get("tctl_temp"):
                self.cpu_temp_slider.setValue(state["tctl_temp"])
        
        # Load GPU state
        if self.nvidia_smi.is_available:
            state = self.nvidia_smi.get_current_state()
            # Set reasonable defaults from config
            profile = self.config.get_current_profile()
            self.gpu_clock_min_slider.setValue(profile.get("gpu_clock_min", 300))
            self.gpu_clock_max_slider.setValue(profile.get("gpu_clock_max", 1500))
            self.gpu_temp_slider.setValue(profile.get("gpu_temp_limit", 87))
    
    def _set_active_button(self, buttons: dict[str, ModeButton], active_key: str) -> None:
        """Set one button as active (checked) in a group."""
        for key, btn in buttons.items():
            btn.setChecked(key == active_key)
    
    def _on_power_profile_clicked(self, profile: str) -> None:
        """Handle power profile button click - loads and applies full profile."""
        self._set_active_button(self.profile_buttons, profile)
        
        # Set as current profile
        self.config.set_current_profile(profile)
        
        # Apply asusctl power profile
        self.asusctl.set_power_profile(profile)
        
        # Load and apply all profile settings
        self._apply_profile(profile)
    
    def _on_gpu_mode_clicked(self, mode: str) -> None:
        """Handle GPU mode button click."""
        self._set_active_button(self.gpu_buttons, mode)
        self.supergfxctl.set_gpu_mode(mode)
        self._save_to_current_profile("gpu_mode", mode)
    
    def _on_cpu_sustained_changed(self, value: int) -> None:
        """Handle CPU sustained power limit change."""
        self._debouncer.call("cpu_sustained", self.ryzenadj.set_sustained_limit, value)
        self._save_to_current_profile("cpu_sustained", value)
    
    def _on_cpu_short_changed(self, value: int) -> None:
        """Handle CPU short boost power limit change."""
        self._debouncer.call("cpu_short", self.ryzenadj.set_short_limit, value)
        self._save_to_current_profile("cpu_short", value)
    
    def _on_cpu_fast_changed(self, value: int) -> None:
        """Handle CPU fast boost power limit change."""
        self._debouncer.call("cpu_fast", self.ryzenadj.set_fast_limit, value)
        self._save_to_current_profile("cpu_fast", value)
    
    def _on_cpu_temp_changed(self, value: int) -> None:
        """Handle CPU temp slider change."""
        self._debouncer.call("cpu_temp", self.ryzenadj.set_temp_limit, value)
        self._save_to_current_profile("cpu_temp_limit", value)
    
    def _on_gpu_clock_changed(self, _: int) -> None:
        """Handle GPU clock slider change."""
        min_clock = self.gpu_clock_min_slider.value()
        max_clock = self.gpu_clock_max_slider.value()
        # Ensure min <= max
        if min_clock > max_clock:
            max_clock = min_clock
            self.gpu_clock_max_slider.setValue(max_clock)
        self._debouncer.call("gpu_clock", self.nvidia_smi.set_clock_limits, min_clock, max_clock)
        self._save_to_current_profile("gpu_clock_min", min_clock)
        self._save_to_current_profile("gpu_clock_max", max_clock)
    
    def _on_gpu_temp_changed(self, value: int) -> None:
        """Handle GPU temp slider change."""
        self._debouncer.call("gpu_temp", self.nvidia_smi.set_temp_limit, value)
        self._save_to_current_profile("gpu_temp_limit", value)
    
    def _on_kbd_brightness_changed(self, value: int) -> None:
        """Handle keyboard brightness change."""
        led_levels = ["off", "low", "med", "high"]
        if 0 <= value < len(led_levels):
            level = led_levels[value]
            self.kbd_brightness_label.setText(level)
            self._debouncer.call("kbd_brightness", self.asusctl.set_keyboard_brightness, level)
            self._save_to_current_profile("keyboard_brightness", level)
    
    def _on_battery_limit_changed(self, value: int) -> None:
        """Handle battery charge limit change."""
        self.battery_limit_label.setText(f"{value}%")
        self._debouncer.call("battery_limit", self.asusctl.set_battery_limit, value)
        self._save_to_current_profile("battery_limit", value)
    
    def _on_battery_oneshot_clicked(self) -> None:
        """Handle battery oneshot button click."""
        success = self.asusctl.battery_oneshot(100)
        if success:
            self.battery_oneshot_btn.setText("✓ One-Shot Enabled")
            self.battery_oneshot_btn.setEnabled(False)
    
    
    def _apply_profile(self, profile_name: str) -> None:
        """Apply all settings from a profile."""
        profile_data = self.config.get("profiles", profile_name, default={})
        
        # Apply supergfxctl settings
        if self.supergfxctl.is_available:
            gpu_mode = profile_data.get("gpu_mode")
            if gpu_mode:
                self.supergfxctl.set_gpu_mode(gpu_mode)
                if gpu_mode in self.gpu_buttons:
                    self._set_active_button(self.gpu_buttons, gpu_mode)
        
        # Apply ryzenadj settings
        if self.ryzenadj.is_available:
            if "cpu_sustained" in profile_data:
                self.cpu_sustained_slider.setValue(profile_data["cpu_sustained"])
                self.ryzenadj.set_sustained_limit(profile_data["cpu_sustained"])
            if "cpu_short" in profile_data:
                self.cpu_short_slider.setValue(profile_data["cpu_short"])
                self.ryzenadj.set_short_limit(profile_data["cpu_short"])
            if "cpu_fast" in profile_data:
                self.cpu_fast_slider.setValue(profile_data["cpu_fast"])
                self.ryzenadj.set_fast_limit(profile_data["cpu_fast"])
            if "cpu_temp_limit" in profile_data:
                self.cpu_temp_slider.setValue(profile_data["cpu_temp_limit"])
                self.ryzenadj.set_temp_limit(profile_data["cpu_temp_limit"])
        
        # Apply nvidia-smi settings
        if self.nvidia_smi.is_available:
            if "gpu_clock_min" in profile_data and "gpu_clock_max" in profile_data:
                self.gpu_clock_min_slider.setValue(profile_data["gpu_clock_min"])
                self.gpu_clock_max_slider.setValue(profile_data["gpu_clock_max"])
                self.nvidia_smi.set_clock_limits(
                    profile_data["gpu_clock_min"],
                    profile_data["gpu_clock_max"],
                )
            if "gpu_temp_limit" in profile_data:
                self.gpu_temp_slider.setValue(profile_data["gpu_temp_limit"])
                self.nvidia_smi.set_temp_limit(profile_data["gpu_temp_limit"])
        
        # Apply battery limit
        if self.asusctl.is_available and "battery_limit" in profile_data:
            self.battery_limit_slider.setValue(profile_data["battery_limit"])
            self.asusctl.set_battery_limit(profile_data["battery_limit"])
        
        # Apply keyboard brightness
        if self.asusctl.is_available and "keyboard_brightness" in profile_data:
            level = profile_data["keyboard_brightness"]
            led_levels = ["off", "low", "med", "high"]
            if level in led_levels:
                self.kbd_brightness_slider.setValue(led_levels.index(level))
                self.kbd_brightness_label.setText(level)
                self.asusctl.set_keyboard_brightness(level)
    
    def _save_to_current_profile(self, key: str, value) -> None:
        """Save a setting to the current profile."""
        profile_name = self._get_current_profile_name()
        self.config.set("profiles", profile_name, key, value)
    
    # type: ignore
    def closeEvent(self, event: QCloseEvent) -> None:
        """Handle window close - hide to tray instead of quitting."""
        event.ignore()
        self.hide()
        self.hide_requested.emit()
