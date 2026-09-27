import os
import re
import subprocess
from crux.store import get_active_profile, get_profile_creds
from crux.aliases import resolve_command

# Key names must be safe shell identifiers — alphanumeric + underscore + hyphen only
_SAFE_KEY_RE = re.compile(r'^[A-Za-z0-9_-]+$')


def _sanitize_value(value: str) -> str:
    """
    Strip null bytes and control characters that could break shell export statements.
    Newlines are replaced with a space — credentials should never contain them.
    """
    value = value.replace('\x00', '')          # strip null bytes
    value = re.sub(r'[\r\n]', ' ', value)      # collapse newlines → space
    value = re.sub(r'[\x01-\x1f\x7f]', '', value)  # strip other control chars
    return value


def _shell_single_quote(value: str) -> str:
    """
    Wrap value in single quotes with proper escaping.
    Inside single quotes nothing is interpreted — the only character
    that can break out is ' itself, which we replace with '\''.
    """
    return "'" + value.replace("'", "'\\''") + "'"


def inject_and_run(command: str, args: tuple) -> tuple:
    """
    Inject credentials from the active profile as env vars and run the command.
    Returns (subprocess.CompletedProcess | None, error_string | None).
    """
    profile = get_active_profile()

    if not profile:
        return None, "no_profile"

    creds = get_profile_creds(profile)

    if not creds:
        return None, "empty_profile"

    resolved = resolve_command(command)
    if not resolved:
        return None, f"not_found:{command}"

    # Merge: system env + sanitized profile credentials
    env = os.environ.copy()
    env.update({k: _sanitize_value(v) for k, v in creds.items()})

    full_cmd = [resolved] + list(args)

    try:
        result = subprocess.run(full_cmd, env=env)
        return result, None
    except FileNotFoundError:
        return None, f"not_found:{resolved}"
    except KeyboardInterrupt:
        return None, "interrupted"


def get_hook_exports() -> str:
    """
    Output shell export statements for the active profile.
    Called by the shell hook: eval "$(crux _hook)"

    Also outputs:
    - HISTIGNORE patterns for every credential key (fix 1)
    - ulimit -c 0 to disable core dumps (fix 4)
    """
    profile = get_active_profile()
    if not profile:
        return ""

    creds = get_profile_creds(profile)
    if not creds:
        return ""

    lines = []

    # Export each credential — sanitized + single-quote escaped
    for key, value in creds.items():
        if not _SAFE_KEY_RE.match(key):
            continue  # skip any key that somehow has unsafe characters
        safe_value = _shell_single_quote(_sanitize_value(value))
        lines.append(f"export {key}={safe_value}")

    # Fix 1: Dynamically extend HISTIGNORE with every credential key name
    # so commands containing these var names are never saved to history
    histignore_patterns = ":".join(f"*{key}*" for key in creds.keys())
    lines.append(f'export HISTIGNORE="${{HISTIGNORE}}:{histignore_patterns}"')

    # Fix 4: Disable core dumps to prevent credentials leaking into crash files
    lines.append("ulimit -c 0")

    return "\n".join(lines)
