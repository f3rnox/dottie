"""Dottie CLI — dotfile manager powered by Typer."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Optional

import typer
from rich import print as rprint
from rich.table import Table

from dottie import __version__
from dottie.config import (
    CONFIG_FILE,
    get_repo_path,
    get_target_path,
    load_config,
    save_config,
)
from dottie.linker import (
    LinkState,
    collect_dotfiles,
    link_dotfiles,
    print_status,
    unlink_dotfiles,
)

app = typer.Typer(
    name="dottie",
    help="A friendly dotfile manager that symlinks files from your dotfiles repo.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)


def _version_callback(value: bool) -> None:
    if value:
        rprint(f"dottie [bold]{__version__}[/bold]")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        Optional[bool],
        typer.Option(
            "--version",
            "-v",
            callback=_version_callback,
            is_eager=True,
            help="Show version and exit.",
        ),
    ] = None,
) -> None:
    """Dottie — manage your dotfiles with symlinks."""


@app.command()
def init(
    repo: Annotated[
        Optional[str],
        typer.Argument(help="Path to your dotfiles repo."),
    ] = None,
) -> None:
    """Initialize or reconfigure the dotfiles repo path."""
    if repo is None:
        repo = typer.prompt("Path to your dotfiles repo")

    repo_path = Path(repo).expanduser().resolve()
    if not repo_path.is_dir():
        rprint(f"[red]Not a directory:[/red] {repo_path}")
        raise typer.Exit(code=1)

    cfg = load_config() if CONFIG_FILE.exists() else {}
    cfg["repo"] = str(repo_path)
    save_config(cfg)
    rprint(f"[green]Repo set to:[/green] {repo_path}")


@app.command()
def link(
    force: Annotated[
        bool,
        typer.Option(
            "--force", "-f", help="Overwrite conflicting files (backs up originals)."
        ),
    ] = False,
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run", "-n", help="Show what would be linked without making changes."
        ),
    ] = False,
) -> None:
    """Symlink dotfiles from the repo into your home directory."""
    cfg = load_config()
    repo = get_repo_path(cfg)
    target = get_target_path(cfg)
    ignore = cfg.get("ignore", [])

    entries = collect_dotfiles(repo, target, ignore)

    if not entries:
        rprint("[yellow]No dotfiles found in repo.[/yellow]")
        raise typer.Exit()

    if dry_run:
        rprint("[bold]Dry run — no changes will be made:[/bold]\n")
        print_status(entries)
        return

    result = link_dotfiles(entries, force=force)

    if result.created:
        rprint(f"[green]Linked {len(result.created)} file(s).[/green]")
    if result.skipped:
        rprint(f"[dim]Skipped {len(result.skipped)} already-linked file(s).[/dim]")
    if result.conflicts:
        rprint(
            f"[yellow]{len(result.conflicts)} conflict(s) — use --force to overwrite.[/yellow]"
        )
        for e in result.conflicts:
            rprint(f"  [yellow]✘[/yellow] {e.rel_path}")


@app.command()
def unlink() -> None:
    """Remove symlinks managed by dottie (does not delete originals)."""
    cfg = load_config()
    repo = get_repo_path(cfg)
    target = get_target_path(cfg)
    ignore = cfg.get("ignore", [])

    entries = collect_dotfiles(repo, target, ignore)
    removed = unlink_dotfiles(entries)

    if removed:
        rprint(f"[green]Removed {len(removed)} symlink(s).[/green]")
        for e in removed:
            rprint(f"  [dim]○[/dim] {e.rel_path}")
    else:
        rprint("[dim]No managed symlinks to remove.[/dim]")


@app.command()
def status() -> None:
    """Show the link state of each dotfile."""
    cfg = load_config()
    repo = get_repo_path(cfg)
    target = get_target_path(cfg)
    ignore = cfg.get("ignore", [])

    home_path = Path.home().resolve()
    meta = Table(show_header=False, box=None, pad_edge=False)
    meta.add_column(style="bold")
    meta.add_column()
    meta.add_row("Home:", str(home_path))
    meta.add_row("Dotfiles repo:", str(repo))
    rprint(meta)
    rprint()

    entries = collect_dotfiles(repo, target, ignore)

    if not entries:
        rprint("[yellow]No dotfiles found in repo.[/yellow]")
        raise typer.Exit()

    linked = sum(1 for e in entries if e.state == LinkState.LINKED)
    total = len(entries)

    rprint(f"[bold]Dotfiles status[/bold] ({linked}/{total} linked)\n")
    print_status(entries)


@app.command(name="list")
def list_files() -> None:
    """List all files in the dotfiles repo."""
    cfg = load_config()
    repo = get_repo_path(cfg)
    ignore = cfg.get("ignore", [])
    target = get_target_path(cfg)

    entries = collect_dotfiles(repo, target, ignore)

    if not entries:
        rprint("[yellow]No dotfiles found in repo.[/yellow]")
        raise typer.Exit()

    table = Table(title="Dotfiles", show_lines=False)
    table.add_column("File", style="cyan")
    table.add_column("State", justify="center")
    table.add_column("Target", style="dim")

    for entry in entries:
        state_label = {
            LinkState.LINKED: "[green]linked[/green]",
            LinkState.CONFLICT: "[yellow]conflict[/yellow]",
            LinkState.MISSING: "[dim]unlinked[/dim]",
        }[entry.state]
        table.add_row(entry.rel_path, state_label, str(entry.target))

    rprint(table)


@app.command()
def config() -> None:
    """Show the current configuration."""
    cfg = load_config()
    rprint(f"[bold]Config file:[/bold]  {CONFIG_FILE}")
    rprint(f"[bold]Repo:[/bold]         {cfg.get('repo', '[red]not set[/red]')}")
    rprint(f"[bold]Target:[/bold]       {cfg.get('target', '~')}")
    rprint(f"[bold]Ignore:[/bold]       {', '.join(cfg.get('ignore', []))}")
