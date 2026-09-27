import shutil
from pathlib import Path
from crux.keyring_manager import is_keyring_available
from crux.store import STORE_FILE, CRUX_DIR
from crux.aliases import INSTALL_GUIDES

SHELL_CONFIGS = [
    Path.home() / ".bashrc",
    Path.home() / ".zshrc",
    Path.home() / ".config/fish/config.fish",
]

HOOK_MARKER = "crux _hook"

AI_TOOLS: dict[str, dict] = {
    "claude": {
        "commands": ["claude"],
        "install": INSTALL_GUIDES["claude"],
    },
    "codex (ChatGPT)": {
        "commands": ["codex"],
        "install": INSTALL_GUIDES["codex"],
    },
    "gemini": {
        "commands": ["gemini", "antigravity"],
        "install": INSTALL_GUIDES["gemini"],
    },
    "copilot": {
        "commands": ["copilot"],
        "install": INSTALL_GUIDES["copilot"],
    },
    "cursor": {
        "commands": ["cursor-agent", "agent"],
        "install": INSTALL_GUIDES["cursor-agent"],
    },
}


def check_all() -> dict:
    results: dict = {}

    # Shell hook check
    hook_found = False
    for config in SHELL_CONFIGS:
        if config.exists() and HOOK_MARKER in config.read_text():
            hook_found = True
            break
    results["shell_hook"] = hook_found

    # OS keyring
    results["os_keyring"] = is_keyring_available()

    # Store file
    results["store"] = STORE_FILE.exists()

    # Directory permissions
    if CRUX_DIR.exists():
        perms = oct(CRUX_DIR.stat().st_mode)[-3:]
        results["permissions"] = perms == "700"
    else:
        results["permissions"] = False

    # AI tool binaries
    tool_results: dict = {}
    for tool_name, info in AI_TOOLS.items():
        found_cmd = None
        for cmd in info["commands"]:
            if shutil.which(cmd):
                found_cmd = cmd
                break
        tool_results[tool_name] = {
            "found": found_cmd is not None,
            "command": found_cmd,
            "install": info["install"],
        }
    results["tools"] = tool_results

    return results
