# ASUS Helper - Development Walkthrough

## Overview

ASUS Helper is a power management tool for ASUS laptops on Linux, built with PyQt6 and inspired by G-Helper (Windows).

## Architecture

```
src/asus_helper/
├── app.py              # Main application, Qt setup, signal handling
├── config.py           # TOML config at ~/.config/asus-helper/
├── logging.py          # Logging setup, --debug flag
├── single_instance.py  # Lock file at /tmp/asus-helper.lock
├── bridges/
│   ├── base.py         # Abstract Bridge class
│   ├── asusctl.py      # Power profiles, LEDs, battery, armoury
│   ├── supergfxctl.py  # GPU mode (Integrated/Hybrid/Dedicated)
│   ├── ryzenadj.py     # AMD CPU power/temp limits
│   └── nvidia_smi.py   # NVIDIA GPU clocks/temp
└── ui/
    ├── main_window.py  # Main popup window
    └── tray_icon.py    # System tray icon
```

## Key Decisions

### Native Qt Theming
Uses system Qt theme (Breeze Dark on KDE) instead of custom stylesheets. This ensures consistency with desktop.

### Bridge Pattern
Each CLI tool is wrapped in a Bridge class with:
- `is_available` - checks if tool exists
- `get_current_state()` - reads current values
- `apply_settings()` - applies changes

UI sections are hidden if their bridge isn't available.

### Single Instance
Uses file locking (`fcntl.flock`) with PID written to `/tmp/asus-helper.lock`. Second instance sends SIGUSR1 to show existing window.

### Wayland Compatibility
Window positioning doesn't work on Wayland. Instead, `scripts/install.sh` configures KWin rules for:
- Position: bottom-right
- Keep above
- Fixed size

## CLI Commands Reference

See [asusctl-reference.md](./asusctl-reference.md) for full CLI documentation.

Key commands:
```bash
# Power profiles
asusctl profile get              # LowPower, Balanced, Performance
asusctl profile set Performance

# Keyboard LEDs  
asusctl leds get                 # off, low, med, high
asusctl leds set high

# Battery
asusctl battery info             # Current limit %
asusctl battery limit 80

# Armoury (firmware attributes)
asusctl armoury list
asusctl armoury set ppt_pl1_spl 45
```

## Running

```bash
# Development
uv run asus-helper

# Debug mode (verbose logging)
uv run asus-helper --debug

# With root (for ryzenadj/nvidia-smi)
sudo uv run asus-helper
```

Log file: `~/.local/share/asus-helper/asus-helper.log`

## Known Issues

1. **Qt event methods must use camelCase**: `showEvent`, `closeEvent`, not snake_case
2. **Wayland window position**: Use KWin rules, not programmatic positioning
3. **Root required**: ryzenadj and nvidia-smi need root privileges
