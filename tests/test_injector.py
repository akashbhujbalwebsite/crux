import pytest
from unittest.mock import patch, MagicMock
from cryptography.fernet import Fernet

TEST_KEY = Fernet.generate_key()


@pytest.fixture(autouse=True)
def isolated_store(tmp_path, monkeypatch):
    monkeypatch.setattr("crux.store.CRUX_DIR", tmp_path / ".crux")
    monkeypatch.setattr("crux.store.STORE_FILE", tmp_path / ".crux" / "store.enc")
    monkeypatch.setattr("crux.keyring_manager.CRUX_DIR", tmp_path / ".crux")
    monkeypatch.setattr("crux.keyring_manager.KEY_FILE", tmp_path / ".crux" / ".key")
    with patch("crux.keyring_manager.get_key", return_value=TEST_KEY):
        yield


def test_inject_no_profile_returns_error():
    from crux.injector import inject_and_run
    _, error = inject_and_run("claude", ())
    assert error == "no_profile"


def test_inject_empty_profile_returns_error():
    from crux.store import add_credential, set_active_profile, remove_credential
    from crux.injector import inject_and_run
    from crux.store import get_store, save_store
    # Create profile then manually empty it
    add_credential("empty-profile", "TEMP", "val")
    set_active_profile("empty-profile")
    data = get_store()
    data["profiles"]["empty-profile"] = {}
    save_store(data)
    _, error = inject_and_run("claude", ())
    assert error == "empty_profile"


def test_inject_command_not_found_returns_error():
    from crux.store import add_credential, set_active_profile
    from crux.injector import inject_and_run
    add_credential("test", "KEY", "val")
    set_active_profile("test")
    with patch("shutil.which", return_value=None):
        _, error = inject_and_run("nonexistent-tool", ())
        assert error is not None
        assert "not_found" in error


def test_hook_exports_contains_keys_and_values():
    from crux.store import add_credential, set_active_profile
    from crux.injector import get_hook_exports
    add_credential("vm-prod", "VM_IP", "10.0.0.1")
    add_credential("vm-prod", "VM_PASS", "secret")
    set_active_profile("vm-prod")
    exports = get_hook_exports()
    assert "VM_IP" in exports
    assert "VM_PASS" in exports
    assert "10.0.0.1" in exports


def test_hook_exports_special_characters_escaped():
    from crux.store import add_credential, set_active_profile
    from crux.injector import get_hook_exports
    add_credential("test", "PASS", "P@$$w0rd!#%")
    set_active_profile("test")
    exports = get_hook_exports()
    assert "PASS" in exports
    # Should be wrapped in single quotes
    assert "export PASS='" in exports


def test_hook_exports_empty_when_no_profile():
    from crux.injector import get_hook_exports
    exports = get_hook_exports()
    assert exports == ""


def test_inject_runs_subprocess():
    from crux.store import add_credential, set_active_profile
    from crux.injector import inject_and_run
    add_credential("test", "MY_KEY", "my_value")
    set_active_profile("test")

    mock_result = MagicMock()
    mock_result.returncode = 0

    with patch("shutil.which", return_value="/usr/bin/echo"), \
         patch("subprocess.run", return_value=mock_result) as mock_run:
        result, error = inject_and_run("echo", ("hello",))
        assert error is None
        assert mock_run.called
        # Verify creds were in the env passed to subprocess
        call_kwargs = mock_run.call_args
        env = call_kwargs[1]["env"] if "env" in call_kwargs[1] else call_kwargs.kwargs.get("env")
        assert env is not None
        assert env.get("MY_KEY") == "my_value"
