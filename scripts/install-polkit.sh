#!/bin/bash
# Install Polkit policy for ASUS Helper
# Run as root: sudo ./install-polkit.sh

set -e

POLICY_FILE="data/org.asus-helper.policy"
DEST="/usr/share/polkit-1/actions/org.asus-helper.policy"

if [ ! -f "$POLICY_FILE" ]; then
    echo "Error: Policy file not found: $POLICY_FILE"
    echo "Run this script from the project root directory."
    exit 1
fi

if [ "$EUID" -ne 0 ]; then
    echo "This script must be run as root."
    echo "Usage: sudo $0"
    exit 1
fi

echo "Installing Polkit policy..."
cp "$POLICY_FILE" "$DEST"
chmod 644 "$DEST"

echo "Done! ASUS Helper will now prompt for authentication when needed."
echo ""
echo "Note: You may need to log out and back in for changes to take effect."
