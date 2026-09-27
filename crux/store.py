import json
from pathlib import Path
from cryptography.fernet import Fernet
from crux.keyring_manager import get_key

CRUX_DIR = Path.home() / ".crux"
STORE_FILE = CRUX_DIR / "store.enc"


def _get_fernet() -> Fernet:
    return Fernet(get_key())


def get_store() -> dict:
    """Load and decrypt the store. Returns empty store if not found."""
    if not STORE_FILE.exists():
        return {"profiles": {}, "active_profile": None}

    try:
        f = _get_fernet()
        encrypted = STORE_FILE.read_bytes()
        decrypted = f.decrypt(encrypted)
        return json.loads(decrypted)
    except Exception:
        raise RuntimeError(
            "Store corrupted or key mismatch. Run: crux repair"
        )


def save_store(data: dict):
    """Encrypt and save the store."""
    CRUX_DIR.mkdir(mode=0o700, exist_ok=True)
    f = _get_fernet()
    plaintext = json.dumps(data).encode()
    encrypted = f.encrypt(plaintext)
    STORE_FILE.write_bytes(encrypted)
    STORE_FILE.chmod(0o600)


def add_credential(profile: str, key_name: str, value: str):
    data = get_store()
    if profile not in data["profiles"]:
        data["profiles"][profile] = {}
    data["profiles"][profile][key_name] = value
    if data["active_profile"] is None:
        data["active_profile"] = profile
    save_store(data)


def update_credential(profile: str, key_name: str, value: str):
    data = get_store()
    if profile not in data["profiles"]:
        raise ValueError(f"Profile '{profile}' not found")
    data["profiles"][profile][key_name] = value
    save_store(data)


def remove_credential(profile: str, key_name: str):
    data = get_store()
    if profile not in data["profiles"]:
        raise ValueError(f"Profile '{profile}' not found")
    if key_name not in data["profiles"][profile]:
        raise ValueError(f"Key '{key_name}' not found in profile '{profile}'")
    del data["profiles"][profile][key_name]
    save_store(data)


def remove_profile(profile: str):
    data = get_store()
    if profile not in data["profiles"]:
        raise ValueError(f"Profile '{profile}' not found")
    del data["profiles"][profile]
    if data["active_profile"] == profile:
        remaining = list(data["profiles"].keys())
        data["active_profile"] = remaining[0] if remaining else None
    save_store(data)


def get_profile_creds(profile: str) -> dict:
    data = get_store()
    return data["profiles"].get(profile, {})


def get_active_profile() -> str | None:
    data = get_store()
    return data.get("active_profile")


def set_active_profile(profile: str):
    data = get_store()
    if profile not in data["profiles"]:
        raise ValueError(f"Profile '{profile}' not found")
    data["active_profile"] = profile
    save_store(data)


def list_profiles() -> dict:
    data = get_store()
    return data["profiles"]
