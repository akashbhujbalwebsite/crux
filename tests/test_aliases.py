import pytest
from unittest.mock import patch
from crux.aliases import resolve_command, get_install_guide


def test_resolve_claude_direct():
    with patch("shutil.which", return_value="/usr/bin/claude"):
        assert resolve_command("claude") == "claude"


def test_resolve_chatgpt_alias_to_codex():
    def mock_which(cmd):
        return "/usr/bin/codex" if cmd == "codex" else None
    with patch("shutil.which", side_effect=mock_which):
        assert resolve_command("chatgpt") == "codex"


def test_resolve_cursor_alias_to_cursor_agent():
    def mock_which(cmd):
        return "/usr/local/bin/cursor-agent" if cmd == "cursor-agent" else None
    with patch("shutil.which", side_effect=mock_which):
        assert resolve_command("cursor") == "cursor-agent"


def test_resolve_gemini_falls_back_to_antigravity():
    def mock_which(cmd):
        return "/usr/bin/antigravity" if cmd == "antigravity" else None
    with patch("shutil.which", side_effect=mock_which):
        assert resolve_command("gemini") == "antigravity"


def test_resolve_unknown_command_returns_none():
    with patch("shutil.which", return_value=None):
        assert resolve_command("totally-unknown-tool-xyz") is None


def test_resolve_unknown_not_in_aliases_returns_none():
    with patch("shutil.which", return_value=None):
        assert resolve_command("notarealthing") is None


def test_get_install_guide_claude():
    guide = get_install_guide("claude")
    assert "npm" in guide.lower() or "anthropic" in guide.lower()


def test_get_install_guide_chatgpt():
    guide = get_install_guide("chatgpt")
    assert "codex" in guide.lower() or "openai" in guide.lower()


def test_get_install_guide_cursor():
    guide = get_install_guide("cursor")
    assert "cursor.com" in guide.lower()


def test_get_install_guide_unknown_mentions_tool():
    guide = get_install_guide("mytool")
    assert "mytool" in guide
