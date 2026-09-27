# CRUX — Credential Runtime Unified eXecutor

Securely inject credentials into any AI tool. Credentials never appear in chat transcripts.

## Install
```bash
pip install crux-cli
crux install
```

## Usage
```bash
crux add --profile vm-prod      # add credentials
crux list                        # list profiles
crux use vm-prod                 # switch profile
crux run claude                  # launch with creds injected
crux status                      # show current state
crux doctor                      # health check
```
