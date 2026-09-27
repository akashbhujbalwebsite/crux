import os
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from crux.store import (
    add_credential,
    remove_credential,
    get_profile_creds,
    get_active_profile,
    set_active_profile,
    list_profiles,
    CRUX_DIR,
)
from crux.keyring_manager import get_key, is_keyring_available
from crux.injector import inject_and_run, get_hook_exports
from crux.aliases import resolve_command, get_install_guide
from crux.doctor import check_all

app = typer.Typer(
    name="crux",
    help="CRUX — Credential Runtime Unified eXecutor\n\nSecurely inject credentials into any AI tool.",
    add_completion=False,
    no_args_is_help=True,
)
console = Console()

SHELL_CONFIGS = {
    "bash": Path.home() / ".bashrc",
    "zsh": Path.home() / ".zshrc",
    "fish": Path.home() / ".config/fish/config.fish",
}
HOOK_LINE = '\n# CRUX — Credential Runtime Unified eXecutor\neval "$(crux _hook)"\n'
HOOK_MARKER = "crux _hook"


def _detect_shell() -> str:
    shell = os.environ.get("SHELL", "")
    if "zsh" in shell:
        return "zsh"
    if "fish" in shell:
        return "fish"
    return "bash"


# ─────────────────────────────────────────
# crux install
# ─────────────────────────────────────────
@app.command()
def install():
    """One-time setup: add shell hook for automatic credential injection."""
    shell = _detect_shell()
    config_file = SHELL_CONFIGS[shell]

    if config_file.exists() and HOOK_MARKER in config_file.read_text():
        console.print(f"[green]✓[/green] CRUX already installed ({config_file})")
        console.print("  Run [bold]crux status[/bold] to see current state")
        return

    config_file.parent.mkdir(parents=True, exist_ok=True)
    with open(config_file, "a") as f:
        f.write(HOOK_LINE)

    CRUX_DIR.mkdir(mode=0o700, exist_ok=True)
    get_key()  # generate + store encryption key

    console.print("[green]✓[/green] CRUX installed")
    console.print(f"[green]✓[/green] Shell hook added to [bold]{config_file}[/bold]")
    console.print("[green]✓[/green] Encryption key initialized")
    console.print()
    console.print(f"[yellow]→[/yellow] Restart terminal or run: [bold]source {config_file}[/bold]")
    console.print("[yellow]→[/yellow] Add credentials:         [bold]crux add --profile my-profile[/bold]")


# ─────────────────────────────────────────
# crux add
# ─────────────────────────────────────────
@app.command()
def add(
    profile: str = typer.Option(..., "--profile", "-p", help="Profile name (e.g. vm-prod)"),
):
    """Add credentials to a profile interactively."""
    console.print(f"\n[bold]Adding credentials → profile:[/bold] [cyan]{profile}[/cyan]")
    console.print("  Press [bold]Enter[/bold] on empty key name to finish\n")

    count = 0
    while True:
        key_name = typer.prompt("  Key name (e.g. VM_IP)", default="", show_default=False)

        if not key_name:
            break

        if " " in key_name:
            console.print(
                f"  [red]✗[/red] No spaces allowed. Try: [bold]{key_name.replace(' ', '_').upper()}[/bold]"
            )
            continue

        if not key_name.replace("_", "").replace("-", "").isalnum():
            console.print("  [red]✗[/red] Key name must only use letters, numbers, underscores")
            continue

        existing = get_profile_creds(profile)
        if key_name in existing:
            overwrite = typer.confirm(f"  '{key_name}' already exists. Overwrite?")
            if not overwrite:
                continue

        value = typer.prompt(f"  Value for {key_name}", hide_input=True)

        if not value:
            console.print("  [red]✗[/red] Value cannot be empty")
            continue

        add_credential(profile, key_name, value)
        console.print(f"  [green]✓[/green] Saved [bold]{key_name}[/bold]")
        count += 1

    if count > 0:
        console.print(f"\n[green]✓[/green] {count} credential(s) added to [bold]{profile}[/bold]")
        active = get_active_profile()
        if not active:
            set_active_profile(profile)
            console.print(f"[green]✓[/green] Active profile set to [bold]{profile}[/bold]")
    else:
        console.print("\n[yellow]No credentials added.[/yellow]")


# ─────────────────────────────────────────
# crux list
# ─────────────────────────────────────────
@app.command(name="list")
def list_cmd():
    """List all profiles and their stored keys."""
    profiles = list_profiles()
    active = get_active_profile()

    if not profiles:
        console.print("[yellow]No profiles found.[/yellow]")
        console.print("  Run: [bold]crux add --profile my-profile[/bold]")
        return

    table = Table(title="CRUX Profiles", show_header=True, header_style="bold cyan")
    table.add_column("", width=2)
    table.add_column("Profile", style="bold")
    table.add_column("Count", justify="right")
    table.add_column("Keys", style="dim")

    for name, creds in profiles.items():
        marker = "[green]●[/green]" if name == active else " "
        keys = ", ".join(creds.keys()) if creds else "[dim italic]empty[/dim italic]"
        count = str(len(creds))
        table.add_row(marker, name, count, keys)

    console.print(table)
    console.print("[dim]● = active profile[/dim]")


# ─────────────────────────────────────────
# crux use
# ─────────────────────────────────────────
@app.command()
def use(profile: str = typer.Argument(..., help="Profile name to activate")):
    """Switch the active profile."""
    profiles = list_profiles()

    if profile not in profiles:
        console.print(f"[red]✗[/red] Profile '[bold]{profile}[/bold]' not found")
        if profiles:
            console.print(f"  Available: {', '.join(profiles.keys())}")
        console.print(f"  Create it: [bold]crux add --profile {profile}[/bold]")
        raise typer.Exit(1)

    set_active_profile(profile)
    creds = get_profile_creds(profile)

    console.print(f"[green]✓[/green] Active profile: [bold cyan]{profile}[/bold cyan]")
    if creds:
        console.print(f"  Injecting: {', '.join(creds.keys())}")
    else:
        console.print(
            f"  [yellow]⚠[/yellow]  Profile is empty — add keys: [bold]crux add --profile {profile}[/bold]"
        )


# ─────────────────────────────────────────
# crux run
# ─────────────────────────────────────────
@app.command(
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True}
)
def run(
    ctx: typer.Context,
    command: str = typer.Argument(..., help="Tool to launch (e.g. claude, codex, cursor)"),
):
    """Launch any tool with credentials injected as environment variables."""
    extra_args = ctx.args

    profile = get_active_profile()
    if not profile:
        console.print("[red]✗[/red] No active profile set")
        console.print("  Run: [bold]crux use <profile>[/bold]")
        raise typer.Exit(1)

    creds = get_profile_creds(profile)
    if not creds:
        console.print(f"[red]✗[/red] Profile '[bold]{profile}[/bold]' has no credentials")
        console.print(f"  Run: [bold]crux add --profile {profile}[/bold]")
        raise typer.Exit(1)

    resolved = resolve_command(command)
    if not resolved:
        console.print(f"[red]✗[/red] Command '[bold]{command}[/bold]' not found in PATH")
        console.print(f"  Install: [bold]{get_install_guide(command)}[/bold]")
        console.print("  Or run:  [bold]crux doctor[/bold]")
        raise typer.Exit(1)

    if resolved != command:
        console.print(f"[dim]→ '{command}' mapped to '{resolved}'[/dim]")

    # Fix 2: warn if sshpass -p flag is used (exposes password in process list)
    if resolved == "sshpass" and "-p" in extra_args:
        console.print("[yellow]⚠[/yellow]  Warning: [bold]-p[/bold] passes the password as a command argument.")
        console.print("  Anyone running [bold]ps aux[/bold] can see it in the process list.")
        console.print("  Use [bold]-e[/bold] instead — reads password from SSHPASS env var safely:")
        console.print(f"  [bold]crux run sshpass -- -e ssh $VM_USER@$VM_IP[/bold]")
        if not typer.confirm("  Continue anyway?", default=False):
            raise typer.Exit(0)

    # Fix 3: warn if sudo is used — it drops env vars by default
    if resolved == "sudo" or "sudo" in extra_args:
        console.print("[yellow]⚠[/yellow]  Warning: [bold]sudo[/bold] drops environment variables by default.")
        console.print("  Your CRUX credentials will NOT be passed to the sudo command.")
        console.print("  Use [bold]sudo -E[/bold] to preserve env vars (use with caution on production systems).")
        if not typer.confirm("  Continue anyway?", default=False):
            raise typer.Exit(0)

    console.print(f"[green]✓[/green] Profile  : [bold]{profile}[/bold]")
    console.print(f"[green]✓[/green] Injecting: {len(creds)} credential(s)")
    console.print(f"[green]✓[/green] Launching: [bold]{resolved}[/bold]\n")

    _, error = inject_and_run(command, tuple(extra_args))

    if error and "not_found" in error:
        console.print(f"[red]✗[/red] Launch failed — command not found: {resolved}")
        raise typer.Exit(1)


# ─────────────────────────────────────────
# crux remove
# ─────────────────────────────────────────
@app.command()
def remove(
    key_name: str = typer.Argument(..., help="Key name to remove"),
    profile: str = typer.Option(..., "--profile", "-p", help="Profile name"),
):
    """Remove a credential from a profile."""
    existing = get_profile_creds(profile)

    if not existing:
        console.print(f"[red]✗[/red] Profile '[bold]{profile}[/bold]' not found or empty")
        raise typer.Exit(1)

    if key_name not in existing:
        console.print(f"[red]✗[/red] Key '[bold]{key_name}[/bold]' not found in profile '[bold]{profile}[/bold]'")
        console.print(f"  Available keys: {', '.join(existing.keys())}")
        raise typer.Exit(1)

    confirmed = typer.confirm(f"Remove '{key_name}' from profile '{profile}'?")
    if not confirmed:
        console.print("Cancelled.")
        return

    remove_credential(profile, key_name)
    console.print(f"[green]✓[/green] Removed [bold]{key_name}[/bold] from [bold]{profile}[/bold]")


# ─────────────────────────────────────────
# crux status
# ─────────────────────────────────────────
@app.command()
def status():
    """Show current CRUX state — active profile, injected vars, shell hook."""
    active = get_active_profile()
    profiles = list_profiles()

    console.print("\n[bold]CRUX Status[/bold]")
    console.print("─" * 42)

    if active:
        console.print(f"  Active profile  : [green bold]{active}[/green bold]")
        creds = get_profile_creds(active)
        if creds:
            console.print(f"  Injected vars   : [cyan]{', '.join(creds.keys())}[/cyan]")
        else:
            console.print("  Injected vars   : [yellow]none (profile is empty)[/yellow]")
    else:
        console.print("  Active profile  : [yellow]none — run: crux use <profile>[/yellow]")

    # Shell hook check
    hook_found = any(
        p.exists() and "crux _hook" in p.read_text()
        for p in [Path.home() / ".bashrc", Path.home() / ".zshrc"]
    )
    hook_status = "[green]✓ active[/green]" if hook_found else "[yellow]not installed — run: crux install[/yellow]"
    console.print(f"  Shell hook      : {hook_status}")

    keyring_status = "[green]✓ OS keyring[/green]" if is_keyring_available() else "[yellow]file-based fallback[/yellow]"
    console.print(f"  Encryption      : {keyring_status}")
    console.print(f"  Total profiles  : {len(profiles)}")
    console.print("─" * 42 + "\n")


# ─────────────────────────────────────────
# crux doctor
# ─────────────────────────────────────────
@app.command()
def doctor():
    """Health check — CRUX setup and AI tool availability."""
    console.print("\n[bold]CRUX Health Check[/bold]")
    console.print("─" * 52)

    results = check_all()

    def ok(msg: str) -> str:
        return f"[green]✓[/green] {msg}"

    def fail(msg: str) -> str:
        return f"[red]✗[/red] {msg}"

    def warn(msg: str) -> str:
        return f"[yellow]⚠[/yellow]  {msg}"

    console.print(
        ok("Shell hook        active")
        if results["shell_hook"]
        else fail("Shell hook        not installed → run: crux install")
    )
    console.print(
        ok("OS keyring        available")
        if results["os_keyring"]
        else warn("OS keyring        unavailable — using encrypted file fallback")
    )
    console.print(
        ok("Store             intact")
        if results["store"]
        else warn("Store             not found — run: crux add --profile <name>")
    )
    console.print(
        ok("Permissions       secure (700)")
        if results["permissions"]
        else warn("Permissions       check ~/.crux directory permissions")
    )

    console.print()
    console.print("[bold]AI Tools:[/bold]")
    for tool_name, info in results["tools"].items():
        if info["found"]:
            msg = f"{tool_name:<22} found ({info['command']})"
            console.print(f"  {ok(msg)}")
        else:
            msg = f"{tool_name:<22} not found → {info['install']}"
            console.print(f"  {fail(msg)}")

    console.print("─" * 52 + "\n")


# ─────────────────────────────────────────
# crux _hook  (internal — used by shell)
# ─────────────────────────────────────────
@app.command(name="_hook", hidden=True)
def hook():
    """Internal: emit shell exports for the active profile (used by shell hook)."""
    exports = get_hook_exports()
    if exports:
        print(exports)


if __name__ == "__main__":
    app()
