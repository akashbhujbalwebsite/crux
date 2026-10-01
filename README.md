# CRUX — Credential Runtime Unified eXecutor

> Store credentials encrypted on your machine. Auto-inject into any AI tool. Credentials never appear in chat transcripts.

---

## The Problem

Every day, developers paste passwords, API keys, and server credentials directly into AI chat tools to get help with tasks.

```
❌ You type in chat: "my server password is MyP@ssw0rd123, can you SSH in?"
```

That credential is now in the conversation — stored on Anthropic/OpenAI servers, visible in your transcript forever.

**Real numbers (2026):**
- 29 million secrets leaked on GitHub in 2025 — 34% YoY increase
- 1.27 million AI-specific keys exposed (OpenAI, Anthropic, Hugging Face)
- 3.2% secret-leak rate in AI-assisted commits vs 1.5% baseline

---

## The Solution

CRUX stores your credentials encrypted locally and auto-injects them as environment variables into any AI tool.

```
✅ You say in chat: "SSH into $VM_USER@$VM_IP using $VM_PASS"
```

Claude/ChatGPT sees the variable names — never the actual values.

---

## Install

**Linux / macOS (recommended):**
```bash
pipx install crux-inject
crux install
source ~/.bashrc
```

> **Ubuntu/Debian users:** `pip install` is blocked system-wide by default. Use `pipx` instead.
> Install pipx first if needed: `sudo apt install pipx && pipx ensurepath`

**Inside a virtual environment:**
```bash
pip install crux-inject
```

> **Platform support:** Linux and macOS only. Windows users: use WSL2.

---

## Quick Start

**1. Add credentials for a profile:**
```bash
crux add --profile my-server

# Adding credentials → profile: my-server
#   Key name: VM_IP
#   Value: 10.0.1.100
#   Key name: VM_USER
#   Value: admin
#   Key name: VM_PASS
#   Value: ••••••••••
```

**2. Switch to that profile:**
```bash
crux use my-server
source ~/.bashrc
```

**3. Your creds are now live as env vars:**
```bash
echo $VM_IP      # 10.0.1.100
echo $VM_USER    # admin
```

**4. Launch any AI tool with creds injected:**
```bash
crux run claude
```

Now tell Claude: *"SSH into $VM_USER@$VM_IP and check disk space"* — Claude runs the command, your password never enters the chat.

---

## Commands

| Command | What it does |
|---------|-------------|
| `crux install` | One-time setup — adds shell hook to `~/.bashrc` |
| `crux add --profile <name>` | Add credentials interactively (hidden input) |
| `crux list` | Show all profiles and their key names |
| `crux use <profile>` | Switch active profile |
| `crux run <tool>` | Launch any tool with credentials injected |
| `crux remove <key> --profile <name>` | Delete a credential |
| `crux status` | Show current active profile and keys |
| `crux doctor` | Health check — CRUX setup + AI tools |

---

## AI Tool Support

| You type | CRUX resolves to |
|----------|-----------------|
| `crux run claude` | `claude` |
| `crux run cursor` | `cursor-agent` |
| `crux run gemini` | `gemini-cli` |
| `crux run copilot` | `copilot` |
| `crux run <anything>` | any binary in PATH |

---

## Multi-Profile Workflow

Working across multiple environments? Create a profile per environment:

```bash
crux add --profile server-prod
crux add --profile server-staging
crux add --profile aws-dev

crux list
# Profiles: server-prod (active), server-staging, aws-dev

crux use server-staging
source ~/.bashrc
crux run claude       # Claude now gets staging creds
```

---

## How It Works

CRUX adds a shell hook to `~/.bashrc`:

```bash
eval "$(crux _hook)"
```

On every terminal open, this hook:
1. Exports credentials from the active profile as `export KEY=value`
2. Adds all credential key names to `HISTIGNORE` so they never appear in shell history
3. Runs `ulimit -c 0` to disable core dumps (prevents credentials leaking in crash files)

Credentials are stored encrypted at `~/.crux/store.enc` using **Fernet (AES-128)**. The encryption key is stored in your OS keyring (Linux Secret Service / macOS Keychain) with a file-based fallback at `~/.crux/.key` for headless servers.

---

## Security

**What CRUX protects:**
- Credentials never typed into AI chat
- Credentials never in shell history
- Credentials never in core dump files
- Encrypted at rest (AES-128 Fernet)
- OS keyring integration for key storage

**Golden Rules:**
1. Never ask AI to *reveal* a credential — ask it to *use* it: `ssh into $VM_USER@$VM_IP`
2. Rotate credentials you shared in AI chat before using CRUX
3. Use `sshpass -e` not `sshpass -p` (avoids password visible in `ps aux`)
4. Use `sudo -E` to preserve env vars when sudoing
5. Never commit `~/.crux/` to git — excluded by default in `.gitignore`

See [SECURITY.md](SECURITY.md) for full details.

---

## Requirements

- Python 3.10+
- Linux / macOS

---

## License

MIT © 2026 Akash Bhujbal
