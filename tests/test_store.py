import pytest
from unittest.mock import patch
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


def test_empty_store_returns_defaults():
    from crux.store import get_store
    data = get_store()
    assert data["profiles"] == {}
    assert data["active_profile"] is None


def test_add_and_retrieve_credential():
    from crux.store import add_credential, get_profile_creds
    add_credential("vm-prod", "VM_IP", "10.0.0.1")
    creds = get_profile_creds("vm-prod")
    assert creds["VM_IP"] == "10.0.0.1"


def test_add_multiple_credentials():
    from crux.store import add_credential, get_profile_creds
    add_credential("vm-prod", "VM_IP", "10.0.0.1")
    add_credential("vm-prod", "VM_USER", "admin")
    add_credential("vm-prod", "VM_PASS", "secret#123")
    creds = get_profile_creds("vm-prod")
    assert len(creds) == 3
    assert creds["VM_PASS"] == "secret#123"


def test_special_characters_in_value():
    from crux.store import add_credential, get_profile_creds
    add_credential("test", "PASS", "P@$$w0rd!#%^&*()")
    creds = get_profile_creds("test")
    assert creds["PASS"] == "P@$$w0rd!#%^&*()"


def test_overwrite_credential():
    from crux.store import add_credential, get_profile_creds
    add_credential("vm-prod", "VM_IP", "10.0.0.1")
    add_credential("vm-prod", "VM_IP", "10.0.0.2")
    creds = get_profile_creds("vm-prod")
    assert creds["VM_IP"] == "10.0.0.2"


def test_remove_credential():
    from crux.store import add_credential, remove_credential, get_profile_creds
    add_credential("vm-prod", "VM_IP", "10.0.0.1")
    remove_credential("vm-prod", "VM_IP")
    creds = get_profile_creds("vm-prod")
    assert "VM_IP" not in creds


def test_remove_nonexistent_profile_raises():
    from crux.store import remove_credential
    with pytest.raises(ValueError, match="not found"):
        remove_credential("nonexistent", "KEY")


def test_remove_nonexistent_key_raises():
    from crux.store import add_credential, remove_credential
    add_credential("vm-prod", "VM_IP", "10.0.0.1")
    with pytest.raises(ValueError, match="not found"):
        remove_credential("vm-prod", "NONEXISTENT_KEY")


def test_first_profile_becomes_active_automatically():
    from crux.store import add_credential, get_active_profile
    add_credential("vm-prod", "VM_IP", "10.0.0.1")
    assert get_active_profile() == "vm-prod"


def test_set_active_profile():
    from crux.store import add_credential, set_active_profile, get_active_profile
    add_credential("vm-prod", "VM_IP", "10.0.0.1")
    add_credential("vm-staging", "VM_IP", "10.0.0.2")
    set_active_profile("vm-staging")
    assert get_active_profile() == "vm-staging"


def test_set_active_nonexistent_profile_raises():
    from crux.store import set_active_profile
    with pytest.raises(ValueError, match="not found"):
        set_active_profile("nonexistent")


def test_list_profiles():
    from crux.store import add_credential, list_profiles
    add_credential("profile-a", "KEY1", "val1")
    add_credential("profile-b", "KEY2", "val2")
    profiles = list_profiles()
    assert "profile-a" in profiles
    assert "profile-b" in profiles


def test_get_nonexistent_profile_returns_empty():
    from crux.store import get_profile_creds
    creds = get_profile_creds("doesnotexist")
    assert creds == {}


def test_multiple_profiles_isolated():
    from crux.store import add_credential, get_profile_creds
    add_credential("prod", "KEY", "prod-value")
    add_credential("staging", "KEY", "staging-value")
    assert get_profile_creds("prod")["KEY"] == "prod-value"
    assert get_profile_creds("staging")["KEY"] == "staging-value"
