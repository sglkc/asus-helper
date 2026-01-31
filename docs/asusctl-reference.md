# asusctl CLI Reference

This document describes the asusctl command-line interface for ASUS Helper.

## Power Profiles

```bash
# List available profiles
asusctl profile list
# Output: LowPower, Balanced, Performance

# Get current profile
asusctl profile get
# Output: Active profile: LowPower

# Set profile (DO NOT AUTO-RUN)
asusctl profile set <LowPower|Balanced|Performance>
```

## Keyboard Brightness (LEDs)

```bash
# Get current brightness
asusctl leds get
# Output: Current keyboard led brightness: Off

# Set brightness (DO NOT AUTO-RUN)
asusctl leds set <off|low|med|high>
```

## Armoury / Firmware Attributes

Controls CPU power limits, GPU temp targets, and more.

```bash
# List all attributes
asusctl armoury list
# Output shows: ppt_pl1_spl, ppt_pl2_sppt, ppt_pl3_fppt, nv_temp_target, etc.

# Get specific attribute
asusctl armoury get <attribute>

# Set attribute (DO NOT AUTO-RUN)
asusctl armoury set <attribute> <value>
```

### Known Armoury Attributes

| Attribute | Description | Range |
|-----------|-------------|-------|
| `ppt_pl1_spl` | CPU sustained power limit | 15-35W |
| `ppt_pl2_sppt` | CPU short boost power limit | 25-35W |
| `ppt_pl3_fppt` | CPU fast boost power limit | 35-65W |
| `nv_temp_target` | NVIDIA GPU temp target | 75-87°C |
| `gpu_mux_mode` | GPU MUX switch | 0=dGPU, 1=iGPU |
| `boot_sound` | Boot sound | 0=off, 1=on |
| `charge_mode` | Charge mode | 0-2 |
| `dgpu_disable` | Disable dGPU | 0=enabled, 1=disabled |

## Fan Curves

```bash
# Get enabled fan profiles
asusctl fan-curve --get-enabled

# Get fan curve data for a profile
asusctl fan-curve --mod-profile Performance

# Set to default
asusctl fan-curve --default --mod-profile Performance

# Enable/disable custom curves for a profile
asusctl fan-curve --enable-fan-curves true --mod-profile Performance

# Set custom curve data (DO NOT AUTO-RUN)
asusctl fan-curve --mod-profile Performance --fan cpu --data "30c:1%,49c:2%,59c:10%,69c:30%,79c:50%,89c:70%,99c:100%"
```

## Battery

```bash
# Get current charge limit
asusctl battery info
# Output: Current battery charge limit: 60%

# Set charge limit (DO NOT AUTO-RUN)
asusctl battery limit <20-100>

# One-shot full charge
asusctl battery oneshot [percent]
```

## Aura Power (LED Zones)

Controls power states for different LED zones (keyboard, logo, lightbar, lid, rear-glow).

```bash
asusctl aura-power --help
asusctl aura-power keyboard --help
```

Zones: `keyboard`, `logo`, `lightbar`, `lid`, `rear-glow`, `ally`
