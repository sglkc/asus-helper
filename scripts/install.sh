#!/bin/bash
# ASUS Helper Installation Script
# Sets up KWin window rules for proper popup behavior on Wayland

set -e

echo "=== ASUS Helper Installation ==="

# Check if running on KDE Plasma
if ! command -v kwriteconfig6 &> /dev/null; then
    echo "Warning: kwriteconfig6 not found. KWin rules will not be configured."
    echo "If you're not on KDE Plasma 6, this is expected."
fi

# Install KWin window rules for Wayland
# (Wayland doesn't allow apps to set their own window position)
setup_kwin_rules() {
    echo "Setting up KWin window rules..."
    
    local GROUP="ASUS Helper"
    
    # Window matching
    kwriteconfig6 --file kwinrulesrc --group "$GROUP" --key "Description" "ASUS Helper Rules"
    kwriteconfig6 --file kwinrulesrc --group "$GROUP" --key "title" "ASUS Helper"
    kwriteconfig6 --file kwinrulesrc --group "$GROUP" --key "titlematch" "1"
    kwriteconfig6 --file kwinrulesrc --group "$GROUP" --key "types" "1"
    
    # Keep window above others (rule=2 means Force)
    kwriteconfig6 --file kwinrulesrc --group "$GROUP" --key "aboverule" "2"
    
    # Position: bottom-right corner (adjust these values for your screen)
    # Default assumes 1920x1080 screen
    kwriteconfig6 --file kwinrulesrc --group "$GROUP" --key "position" "1490,420"
    kwriteconfig6 --file kwinrulesrc --group "$GROUP" --key "positionrule" "2"
    
    # Window size
    kwriteconfig6 --file kwinrulesrc --group "$GROUP" --key "size" "420,650"
    kwriteconfig6 --file kwinrulesrc --group "$GROUP" --key "sizerule" "2"
    
    echo "KWin rules configured."
}

# Restart KWin to apply rules
restart_kwin() {
    echo "Restarting KWin to apply rules..."
    qdbus6 org.kde.KWin /KWin reconfigure
    echo "KWin reconfigured."
}

# Install systemd user service
install_systemd_service() {
    echo "Installing systemd user service..."
    
    local SERVICE_DIR="$HOME/.config/systemd/user"
    mkdir -p "$SERVICE_DIR"
    
    cat > "$SERVICE_DIR/asus-helper.service" << 'EOF'
[Unit]
Description=ASUS Helper Power Management
Documentation=https://github.com/sglkc/asus-helper
After=graphical-session.target

[Service]
Type=simple
ExecStart=/usr/bin/env python -m asus_helper
Restart=on-failure
RestartSec=5
Environment=QT_QPA_PLATFORM=wayland

[Install]
WantedBy=graphical-session.target
EOF
    
    echo "Systemd service installed to $SERVICE_DIR/asus-helper.service"
    echo ""
    echo "To enable autostart:"
    echo "  systemctl --user enable asus-helper.service"
    echo ""
    echo "To start now:"
    echo "  systemctl --user start asus-helper.service"
}

# Main installation
main() {
    # Setup KWin rules if available
    if command -v kwriteconfig6 &> /dev/null; then
        setup_kwin_rules
        restart_kwin
    fi
    
    # Install systemd service
    install_systemd_service
    
    echo ""
    echo "=== Installation Complete ==="
    echo ""
    echo "Run the app with: uv run asus-helper"
    echo "Or with root:     sudo uv run asus-helper"
}

main "$@"
