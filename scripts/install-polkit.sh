#!/bin/bash
# Install Polkit policy and rules for ASUS Helper
# Run as root: sudo ./install-polkit.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
POLICY_FILE="$SCRIPT_DIR/data/org.asus-helper.policy"
RULES_FILE="$SCRIPT_DIR/data/50-asus-helper.rules"
POLICY_DEST="/usr/share/polkit-1/actions/org.asus-helper.policy"
RULES_DEST="/etc/polkit-1/rules.d/50-asus-helper.rules"

if [ "$EUID" -ne 0 ]; then
    echo "This script must be run as root."
    echo "Usage: sudo $0"
    exit 1
fi

echo "Installing Polkit policy..."
if [ -f "$POLICY_FILE" ]; then
    cp "$POLICY_FILE" "$POLICY_DEST"
    chmod 644 "$POLICY_DEST"
    echo "  ✓ Installed policy: $POLICY_DEST"
else
    echo "  ⚠ Policy file not found: $POLICY_FILE"
fi

echo "Installing Polkit rules (wheel group = no password)..."
if [ -f "$RULES_FILE" ]; then
    cp "$RULES_FILE" "$RULES_DEST"
    chmod 644 "$RULES_DEST"
    echo "  ✓ Installed rules: $RULES_DEST"
else
    echo "  ⚠ Rules file not found: $RULES_FILE"
fi

echo ""
echo "Done! Users in the 'wheel' group can now use ASUS Helper without password prompts."
echo "Other users will be prompted for admin authentication."

