import shutil

# Friendly name → list of real binary names to try (in order)
AI_ALIASES: dict[str, list[str]] = {
    "claude":      ["claude"],
    "chatgpt":     ["codex", "chatgpt"],
    "codex":       ["codex"],
    "gemini":      ["gemini", "antigravity"],
    "antigravity": ["antigravity"],
    "copilot":     ["copilot", "gh-copilot"],
    "cursor":      ["cursor-agent", "agent", "cursor"],
}

INSTALL_GUIDES: dict[str, str] = {
    "claude":       "npm install -g @anthropic-ai/claude-code",
    "codex":        "See https://learn.chatgpt.com/docs/codex/cli",
    "gemini":       "npm install -g @google/gemini-cli",
    "antigravity":  "npm install -g @google/antigravity-cli",
    "copilot":      "npm install -g @github/copilot",
    "cursor-agent": "curl https://cursor.com/install -fsS | bash",
}


def resolve_command(name: str) -> str | None:
    """Resolve a friendly name or direct command to the actual binary in PATH."""
    candidates = AI_ALIASES.get(name.lower(), [name])
    for cmd in candidates:
        if shutil.which(cmd):
            return cmd
    return None


def get_install_guide(name: str) -> str:
    key = name.lower()
    candidates = AI_ALIASES.get(key, [key])
    for c in candidates:
        if c in INSTALL_GUIDES:
            return INSTALL_GUIDES[c]
    return f"Install '{name}' and make sure it is in your PATH"


def get_all_known_tools() -> dict[str, list[str]]:
    return AI_ALIASES
