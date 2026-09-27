import pytest
from typer.testing import CliRunner
from unittest.mock import patch
from cryptography.fernet import Fernet
from crux.main import app

runner = CliRunner()
TEST_KEY = Fernet.generate_key()


@pytest.fixture(autouse=True)
def isolated_env(tmp_path, monkeypatch):
    monkeypatch.setattr("crux.store.CRUX_DIR", tmp_path / ".crux")
    monkeypatch.setattr("crux.store.STORE_FILE", tmp_path / ".crux" / "store.enc")
    monkeypatch.setattr("crux.keyring_manager.CRUX_DIR", tmp_path / ".crux")
    monkeypatch.setattr("crux.keyring_manager.KEY_FILE", tmp_path / ".crux" / ".key")
    monkeypatch.setattr("crux.main.CRUX_DIR", tmp_path / ".crux")
    with patch("crux.keyring_manager.get_key", return_value=TEST_KEY):
        yield


# ── crux list ─────────────────────────────────────────────────

def test_list_empty():
    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    assert "No profiles" in result.output


def test_list_shows_profiles_after_add(tmp_path):
    from crux.store import add_credential
    add_credential("vm-prod", "VM_IP", "10.0.0.1")
    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    assert "vm-prod" in result.output


# ── crux use ──────────────────────────────────────────────────

def test_use_nonexistent_profile():
    result = runner.invoke(app, ["use", "nonexistent"])
    assert result.exit_code != 0
    assert "not found" in result.output.lower()


def test_use_existing_profile():
    from crux.store import add_credential
    add_credential("vm-prod", "VM_IP", "10.0.0.1")
    result = runner.invoke(app, ["use", "vm-prod"])
    assert result.exit_code == 0
    assert "vm-prod" in result.output


# ── crux remove ───────────────────────────────────────────────

def test_remove_nonexistent_profile():
    result = runner.invoke(app, ["remove", "KEY", "--profile", "nonexistent"])
    assert result.exit_code != 0


def test_remove_nonexistent_key():
    from crux.store import add_credential
    add_credential("vm-prod", "VM_IP", "10.0.0.1")
    result = runner.invoke(app, ["remove", "NONEXISTENT", "--profile", "vm-prod"])
    assert result.exit_code != 0
    assert "not found" in result.output.lower()


def test_remove_existing_key():
    from crux.store import add_credential, get_profile_creds
    add_credential("vm-prod", "VM_IP", "10.0.0.1")
    result = runner.invoke(app, ["remove", "VM_IP", "--profile", "vm-prod"], input="y\n")
    assert result.exit_code == 0
    assert "Removed" in result.output
    assert "VM_IP" not in get_profile_creds("vm-prod")


# ── crux status ───────────────────────────────────────────────

def test_status_no_profile():
    result = runner.invoke(app, ["status"])
    assert result.exit_code == 0
    assert "none" in result.output.lower()


def test_status_with_active_profile():
    from crux.store import add_credential
    add_credential("vm-prod", "VM_IP", "10.0.0.1")
    result = runner.invoke(app, ["status"])
    assert result.exit_code == 0
    assert "vm-prod" in result.output


# ── crux run ──────────────────────────────────────────────────

def test_run_no_profile():
    result = runner.invoke(app, ["run", "claude"])
    assert result.exit_code != 0
    assert "No active profile" in result.output


def test_run_empty_profile():
    from crux.store import get_store, save_store, set_active_profile, add_credential, remove_credential
    add_credential("test", "TMP", "x")
    set_active_profile("test")
    data = get_store()
    data["profiles"]["test"] = {}
    save_store(data)
    result = runner.invoke(app, ["run", "claude"])
    assert result.exit_code != 0
    assert "no credentials" in result.output.lower()


def test_run_command_not_found():
    from crux.store import add_credential, set_active_profile
    add_credential("test", "KEY", "val")
    set_active_profile("test")
    with patch("shutil.which", return_value=None):
        result = runner.invoke(app, ["run", "totally-unknown-tool"])
        assert result.exit_code != 0
        assert "not found" in result.output.lower()


# ── crux doctor ───────────────────────────────────────────────

def test_doctor_runs():
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0
    assert "Health Check" in result.output
    assert "AI Tools" in result.output
