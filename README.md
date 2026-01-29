# ASUS Helper

A power management tool for ASUS laptops on Linux, inspired by G-Helper.

## Features

- **Power Profiles**: Switch between Quiet/Balanced/Performance modes (via asusctl)
- **GPU Modes**: Toggle between Integrated/Hybrid/Dedicated GPU (via supergfxctl)
- **CPU Control**: Adjust power and temperature limits (via ryzenadj)
- **GPU Control**: Set clock ranges and temperature limits (via nvidia-smi)  
- **Keyboard Backlight**: Control brightness (via asusctl)
- **Profiles**: Save and load complete configurations
- **System Tray**: Quick access from the tray icon

## Requirements

Install one or more of the following tools:

- [asusctl](https://gitlab.com/asus-linux/asusctl) - Power profiles, keyboard backlight
- [supergfxctl](https://gitlab.com/asus-linux/supergfxctl) - GPU mode switching
- [ryzenadj](https://github.com/FlyGoat/RyzenAdj) - AMD CPU power control
- nvidia-smi (from NVIDIA drivers) - NVIDIA GPU control

## Installation

```bash
# Using uv (recommended)
uv tool install .

# Or using pip
pip install .
```

## Usage

```bash
# Run directly with uv
uv run asus-helper

# Or if installed globally
asus-helper
```

The app will appear in your system tray. Click the tray icon to show/hide the popup.

### Running as Root

Some features (ryzenadj, nvidia-smi) require root privileges:

```bash
sudo uv run asus-helper
```

### Autostart with Systemd

```bash
# Copy the service file
mkdir -p ~/.config/systemd/user
cp systemd/asus-helper.service ~/.config/systemd/user/

# Enable autostart
systemctl --user enable asus-helper.service

# Start now
systemctl --user start asus-helper.service
```

## Configuration

Configuration is stored in `~/.config/asus-helper/config.toml`.

## Development

```bash
# Clone and enter directory
cd asus-helper

# Install dependencies
uv sync

# Run in development
uv run asus-helper
```

## License

MIT
