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
    QComboBox,
    QFrame,
    QSizePolicy,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QCloseEvent

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
        self.label.setMinimumWidth(120)
        layout.addWidget(self.label)
        
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(min_val)
        self.slider.setMaximum(max_val)
        self.slider.valueChanged.connect(self._on_value_changed)
        layout.addWidget(self.slider, stretch=1)
        
        self.value_label = QLabel()
        self.value_label.setMinimumWidth(60)
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
        # Set a reasonable default size
        self.setMinimumWidth(320)
        self.resize(360, 500)
    
    def _setup_ui(self) -> None:
        """Build the UI."""
        central = QWidget()
        self.setCentralWidget(central)
        
        layout = QVBoxLayout(central)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Header with status
        header = QHBoxLayout()
        header.addWidget(QLabel("<b>ASUS Helper</b>"))
        header.addStretch()
        self.status_label = QLabel()
        header.addWidget(self.status_label)
        layout.addLayout(header)
        
        # Power Profile section (asusctl)
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
        
        # Profile selector at bottom
        layout.addWidget(self._create_profile_section())
    
    def _create_power_profile_section(self) -> QGroupBox:
        """Create power profile selection section."""
        group = QGroupBox("⚡ Power Profile")
        layout = QHBoxLayout(group)
        
        self.profile_buttons: dict[str, ModeButton] = {}
        
        for profile in ["quiet", "balanced", "performance"]:
            btn = ModeButton(profile.capitalize())
            btn.clicked.connect(lambda checked, p=profile: self._on_power_profile_clicked(p))
            self.profile_buttons[profile] = btn
            layout.addWidget(btn)
        
        return group
    
    def _create_gpu_mode_section(self) -> QGroupBox:
        """Create GPU mode selection section."""
        group = QGroupBox("🎮 GPU Mode")
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
        """Create CPU power control section."""
        group = QGroupBox("🔧 CPU (ryzenadj)")
        layout = QVBoxLayout(group)
        
        self.cpu_tdp_slider = SliderWithValue("Power Limit", 15, 80, "W")
        self.cpu_tdp_slider.valueChanged.connect(self._on_cpu_tdp_changed)
        layout.addWidget(self.cpu_tdp_slider)
        
        self.cpu_temp_slider = SliderWithValue("Temp Limit", 60, 100, "°C")
        self.cpu_temp_slider.valueChanged.connect(self._on_cpu_temp_changed)
        layout.addWidget(self.cpu_temp_slider)
        
        return group
    
    def _create_nvidia_section(self) -> QGroupBox:
        """Create NVIDIA GPU control section."""
        group = QGroupBox("🖥️ NVIDIA GPU")
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
        group = QGroupBox("⌨️ Keyboard")
        layout = QHBoxLayout(group)
        
        layout.addWidget(QLabel("Brightness"))
        
        self.kbd_brightness_slider = QSlider(Qt.Orientation.Horizontal)
        self.kbd_brightness_slider.setMinimum(0)
        self.kbd_brightness_slider.setMaximum(3)
        self.kbd_brightness_slider.valueChanged.connect(self._on_kbd_brightness_changed)
        layout.addWidget(self.kbd_brightness_slider, stretch=1)
        
        self.kbd_brightness_label = QLabel("2")
        layout.addWidget(self.kbd_brightness_label)
        
        return group
    
    def _create_profile_section(self) -> QWidget:
        """Create profile selector section."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        layout.addWidget(QLabel("Profile:"))
        
        self.profile_combo = QComboBox()
        self.profile_combo.addItems(self.config.get_profile_names())
        self.profile_combo.currentTextChanged.connect(self._on_profile_selected)
        layout.addWidget(self.profile_combo, stretch=1)
        
        apply_btn = QPushButton("Apply")
        apply_btn.clicked.connect(self._apply_current_profile)
        layout.addWidget(apply_btn)
        
        return widget
    
    def _load_current_state(self) -> None:
        """Load current state from hardware."""
        # Load power profile
        if self.asusctl.is_available:
            profile = self.asusctl.get_power_profile()
            if profile and profile in self.profile_buttons:
                self._set_active_button(self.profile_buttons, profile)
            
            state = self.asusctl.get_current_state()
            if state.get("keyboard_brightness") is not None:
                self.kbd_brightness_slider.setValue(state["keyboard_brightness"])
                self.kbd_brightness_label.setText(str(state["keyboard_brightness"]))
        
        # Load GPU mode
        if self.supergfxctl.is_available:
            mode = self.supergfxctl.get_gpu_mode()
            if mode and mode in self.gpu_buttons:
                self._set_active_button(self.gpu_buttons, mode)
        
        # Load CPU state
        if self.ryzenadj.is_available:
            state = self.ryzenadj.get_current_state()
            if state.get("stapm_limit"):
                self.cpu_tdp_slider.setValue(state["stapm_limit"])
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
        
        # Set current profile in combo
        current = self.config.get("general", "current_profile", default="balanced")
        idx = self.profile_combo.findText(current)
        if idx >= 0:
            self.profile_combo.setCurrentIndex(idx)
    
    def _set_active_button(self, buttons: dict[str, ModeButton], active_key: str) -> None:
        """Set one button as active (checked) in a group."""
        for key, btn in buttons.items():
            btn.setChecked(key == active_key)
    
    def _on_power_profile_clicked(self, profile: str) -> None:
        """Handle power profile button click."""
        self._set_active_button(self.profile_buttons, profile)
        self.asusctl.set_power_profile(profile)
    
    def _on_gpu_mode_clicked(self, mode: str) -> None:
        """Handle GPU mode button click."""
        self._set_active_button(self.gpu_buttons, mode)
        self.supergfxctl.set_gpu_mode(mode)
    
    def _on_cpu_tdp_changed(self, value: int) -> None:
        """Handle CPU TDP slider change."""
        self.ryzenadj.set_power_limit(value)
    
    def _on_cpu_temp_changed(self, value: int) -> None:
        """Handle CPU temp slider change."""
        self.ryzenadj.set_temp_limit(value)
    
    def _on_gpu_clock_changed(self, _: int) -> None:
        """Handle GPU clock slider change."""
        min_clock = self.gpu_clock_min_slider.value()
        max_clock = self.gpu_clock_max_slider.value()
        # Ensure min <= max
        if min_clock > max_clock:
            max_clock = min_clock
            self.gpu_clock_max_slider.setValue(max_clock)
        self.nvidia_smi.set_clock_limits(min_clock, max_clock)
    
    def _on_gpu_temp_changed(self, value: int) -> None:
        """Handle GPU temp slider change."""
        self.nvidia_smi.set_temp_limit(value)
    
    def _on_kbd_brightness_changed(self, value: int) -> None:
        """Handle keyboard brightness change."""
        self.kbd_brightness_label.setText(str(value))
        self.asusctl.set_keyboard_brightness(value)
    
    def _on_profile_selected(self, name: str) -> None:
        """Handle profile selection from combo box."""
        self.config.set_current_profile(name)
    
    def _apply_current_profile(self) -> None:
        """Apply the currently selected profile."""
        profile = self.config.get_current_profile()
        
        # Apply asusctl settings
        if self.asusctl.is_available:
            power_profile = profile.get("power_profile")
            if power_profile:
                self.asusctl.set_power_profile(power_profile)
                if power_profile in self.profile_buttons:
                    self._set_active_button(self.profile_buttons, power_profile)
        
        # Apply supergfxctl settings
        if self.supergfxctl.is_available:
            gpu_mode = profile.get("gpu_mode")
            if gpu_mode:
                self.supergfxctl.set_gpu_mode(gpu_mode)
                if gpu_mode in self.gpu_buttons:
                    self._set_active_button(self.gpu_buttons, gpu_mode)
        
        # Apply ryzenadj settings (overrides asusctl)
        if self.ryzenadj.is_available:
            if "cpu_tdp" in profile:
                self.cpu_tdp_slider.setValue(profile["cpu_tdp"])
                self.ryzenadj.set_power_limit(profile["cpu_tdp"])
            if "cpu_temp_limit" in profile:
                self.cpu_temp_slider.setValue(profile["cpu_temp_limit"])
                self.ryzenadj.set_temp_limit(profile["cpu_temp_limit"])
        
        # Apply nvidia-smi settings (overrides asusctl)
        if self.nvidia_smi.is_available:
            if "gpu_clock_min" in profile and "gpu_clock_max" in profile:
                self.gpu_clock_min_slider.setValue(profile["gpu_clock_min"])
                self.gpu_clock_max_slider.setValue(profile["gpu_clock_max"])
                self.nvidia_smi.set_clock_limits(
                    profile["gpu_clock_min"],
                    profile["gpu_clock_max"],
                )
            if "gpu_temp_limit" in profile:
                self.gpu_temp_slider.setValue(profile["gpu_temp_limit"])
                self.nvidia_smi.set_temp_limit(profile["gpu_temp_limit"])
    
    def closeEvent(self, event: QCloseEvent) -> None:
        """Handle window close - hide to tray instead of quitting."""
        event.ignore()
        self.hide()
        self.hide_requested.emit()
