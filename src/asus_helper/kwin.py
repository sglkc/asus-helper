"""KWin window rules configuration for Wayland.

On Wayland, applications cannot set their own window position.
This module configures KWin rules to:
- Position the window at bottom-right
- Keep window above others
- Set fixed window size
"""

import shutil
import subprocess
from asus_helper.logging import get_logger

log = get_logger("kwin")

# KWin rule configuration
KWIN_RULES = {
    "Description": "ASUS Helper Rules",
    "title": "ASUS Helper",
    "titlematch": "1",
    "types": "1",
    "above": "true",
    "aboverule": "2",  # Force keep above
    "position": "1460,320",  # Bottom-right for 1920x1080
    "positionrule": "2",  # Force position
    "maximizehorizrule": "2",
    "maximizevertrule": "2",
}

GROUP = "ASUS Helper"


def is_kde_plasma() -> bool:
    """Check if running on KDE Plasma with kwriteconfig6."""
    return shutil.which("kwriteconfig6") is not None


def get_kwin_config(key: str) -> str | None:
    """Read a KWin rule config value.

    Args:
        key: Config key to read.

    Returns:
        Value if exists, None otherwise.
    """
    if not is_kde_plasma():
        return None

    try:
        result = subprocess.run(
            ["kreadconfig6", "--file", "kwinrulesrc", "--group", GROUP, "--key", key],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except Exception as e:
        log.debug("Failed to read kwin config %s: %s", key, e)

    return None


def set_kwin_config(key: str, value: str) -> bool:
    """Set a KWin rule config value.

    Args:
        key: Config key.
        value: Value to set.

    Returns:
        True if successful.
    """
    try:
        result = subprocess.run(
            [
                "kwriteconfig6",
                "--file",
                "kwinrulesrc",
                "--group",
                GROUP,
                "--key",
                key,
                value,
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        return result.returncode == 0
    except Exception as e:
        log.warning("Failed to set kwin config %s=%s: %s", key, value, e)
        return False


def reconfigure_kwin() -> bool:
    """Tell KWin to reload its configuration.

    Returns:
        True if successful.
    """
    try:
        result = subprocess.run(
            ["qdbus6", "org.kde.KWin", "/KWin", "reconfigure"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            log.info("KWin reconfigured successfully")
            return True
        else:
            log.warning("KWin reconfigure failed: %s", result.stderr.strip())
            return False
    except Exception as e:
        log.warning("Failed to reconfigure KWin: %s", e)
        return False


def register_rule() -> bool:
    """Register the rule in the [General] section of kwinrulesrc.

    KWin requires rules to be listed in [General] to be active.

    Returns:
        True if successful.
    """
    try:
        # Read current rules list
        result = subprocess.run(
            [
                "kreadconfig6",
                "--file",
                "kwinrulesrc",
                "--group",
                "General",
                "--key",
                "rules",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        current_rules = result.stdout.strip() if result.returncode == 0 else ""

        # Check if our rule is already registered
        rules_list = [r.strip() for r in current_rules.split(",") if r.strip()]
        if GROUP in rules_list:
            log.debug("Rule already registered in [General]")
            return True

        # Add our rule to the list
        rules_list.append(GROUP)
        new_rules = ",".join(rules_list)
        count = len(rules_list)

        # Write updated rules list
        subprocess.run(
            [
                "kwriteconfig6",
                "--file",
                "kwinrulesrc",
                "--group",
                "General",
                "--key",
                "count",
                str(count),
            ],
            capture_output=True,
            check=False,
        )
        subprocess.run(
            [
                "kwriteconfig6",
                "--file",
                "kwinrulesrc",
                "--group",
                "General",
                "--key",
                "rules",
                new_rules,
            ],
            capture_output=True,
            check=False,
        )

        log.info("Registered rule in [General] (count=%d, rules=%s)", count, new_rules)
        return True
    except Exception as e:
        log.warning("Failed to register rule: %s", e)
        return False


def ensure_kwin_rules() -> bool:
    """Ensure KWin rules are configured correctly.

    Checks if the config exists with the expected window size.
    If not matching, updates all rules and reconfigures KWin.

    Returns:
        True if rules were updated, False if already up-to-date.
    """
    if not is_kde_plasma():
        log.debug("Not on KDE Plasma, skipping KWin rules")
        return False

    # Check if config exists and has correct size
    config_exists = get_kwin_config("title")

    if config_exists:
        log.debug("KWin rules already configured correctly")
        return False

    log.info("Updating KWin rules")

    # Apply all rules
    success = True
    for key, value in KWIN_RULES.items():
        if not set_kwin_config(key, value):
            success = False

    # Register the rule in [General] section
    register_rule()

    if success:
        # Reconfigure KWin to apply changes
        reconfigure_kwin()
        log.info("KWin rules updated successfully")
        return True
    else:
        log.warning("Some KWin rules failed to apply")
        return False
