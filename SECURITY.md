# CRUX Security Guide

## What CRUX Protects

- Credentials are never typed by you in AI chat ✅
- Credentials are never in your chat history ✅
- Credentials never appear as text you pasted ✅
- Credentials encrypted at rest (Fernet AES + OS keyring) ✅
- Shell history never logs credential key names (HISTIGNORE) ✅
- Core dumps disabled on every session (ulimit -c 0) ✅
- Unsafe patterns warned at runtime (sshpass -p, sudo) ✅

---

## What CRUX Cannot Protect

- If you ask AI *"what is $VM_IP"* — the AI reads and reveals the value in its response. That response is on the AI provider's servers.
- Credentials that were shared in AI chat **before** you set up CRUX — those are already in past transcripts.
- AI tools that automatically log environment variables to debug files.
- Someone with root access reading `/proc/<pid>/environ`.
- A shared terminal session (tmux/screen) where others can see your screen.

---

## The Golden Rules

### Rule 1 — Never ask AI to reveal a credential
❌ Wrong:
```
what is $VM_IP?
what is my database password?
show me $API_KEY
```

✅ Correct:
```
ssh into $VM_USER@$VM_IP and check disk space
connect to $DB_HOST using $DB_PASS and list tables
use $API_KEY to call the weather API
```

Ask AI to **use** the variable — never to **reveal** it.

---

### Rule 2 — Rotate credentials you already shared
If you typed credentials into AI chat before using CRUX:

1. Change the password / regenerate the API key on the provider side
2. Update CRUX with the new value: `crux add --profile <name>`
3. Start a fresh AI conversation

CRUX protects going forward. It cannot erase past conversations.

---

### Rule 3 — Keep profiles minimal
Only add credentials a specific task needs.

```bash
# Good — separate profiles per context
crux add --profile storage-vm     # only storage VM creds
crux add --profile api-keys       # only API keys
crux add --profile database       # only DB creds

# Bad — one profile with everything
crux add --profile everything     # all creds in one place
```

If one profile is compromised, others stay safe.

---

### Rule 4 — Use -e not -p with sshpass
❌ Wrong — password visible in process list:
```bash
sshpass -p $SSHPASS ssh user@host
```

✅ Correct — password read from env var privately:
```bash
sshpass -e ssh user@host
```

CRUX will warn you automatically if you use `-p`.

---

### Rule 5 — sudo drops env vars
```bash
# Wrong — CRUX creds not passed to sudo
crux run sudo somecommand

# Correct — preserve env vars
sudo -E somecommand
```

CRUX will warn you automatically when sudo is detected.

---

### Rule 6 — Never share your ~/.crux directory
Your `~/.crux/store.enc` is encrypted but your `~/.crux/.key` file (fallback when OS keyring is unavailable) holds the decryption key. Never:
- Upload `~/.crux/` to cloud storage
- Share it with anyone
- Commit it to git

Add to your `.gitignore`:
```
.crux/
```

---

## What Goes in v2

These security features are planned for CRUX v2:

| Feature | Description |
|---------|-------------|
| `crux scan` | Pre-commit hook to detect credentials in staged files |
| `crux log` | Audit log — which profile was used, when, with which tool |
| `crux rotate` | Guided credential rotation with provider links |
| Short-lived tokens | Integration with HashiCorp Vault / AWS Secrets Manager |

---

## Reporting a Vulnerability

If you find a security issue in CRUX, please open a GitHub issue marked `[SECURITY]` or email directly. Do not post credential-related vulnerabilities publicly.

---

*CRUX — Credential Runtime Unified eXecutor*
*Built to keep your credentials out of AI chat transcripts.*
