import os
from pathlib import Path
from cryptography.fernet import Fernet

CRUX_DIR = Path.home() / ".crux"
KEY_FILE = CRUX_DIR / ".key"
SERVICE_NAME = "crux-cli"
USERNAME = "master-key"


def get_key() -> bytes:
    """Get encryption key from OS keyring, fallback to file."""
    try:
        import keyring
        key = keyring.get_password(SERVICE_NAME, USERNAME)
        if key:
            return key.encode()
    except Exception as e:
        import sys
        print(f"[crux] OS keyring unavailable ({e}), using file-based fallback.", file=sys.stderr)

    # Fallback: file-based key
    if KEY_FILE.exists():
        return KEY_FILE.read_bytes()

    # Generate new key if nothing found
    return _generate_key()


def set_key(key: bytes):
    """Store encryption key in OS keyring, fallback to file."""
    try:
        import keyring
        keyring.set_password(SERVICE_NAME, USERNAME, key.decode())
        return
    except Exception as e:
        import sys
        print(f"[crux] OS keyring write failed ({e}), storing key in file.", file=sys.stderr)

    # Fallback: file-based key
    CRUX_DIR.mkdir(mode=0o700, exist_ok=True)
    KEY_FILE.write_bytes(key)
    KEY_FILE.chmod(0o600)


def _generate_key() -> bytes:
    key = Fernet.generate_key()
    set_key(key)
    return key


def is_keyring_available() -> bool:
    try:
        import keyring
        keyring.get_password("crux-test", "crux-test")
        return True
    except Exception:
        return False
