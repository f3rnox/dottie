"""Configuration management for dottie."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import typer
from rich import print as rprint

CONFIG_DIR = Path.home() / ".config" / "dottie"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULT_CONFIG: dict[str, Any] = {
    "repo": "",
    "target": str(Path.home()),
    "ignore": [".git", ".gitignore", "README.md", "LICENSE"],
}


def load_config() -> dict[str, Any]:
    """Load config from disk, prompting for repo path if it doesn't exist."""
    if not CONFIG_FILE.exists():
        return _init_config()

    with CONFIG_FILE.open() as f:
        cfg = json.load(f)

    merged = {**DEFAULT_CONFIG, **cfg}
    return merged


def save_config(cfg: dict[str, Any]) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with CONFIG_FILE.open("w") as f:
        json.dump(cfg, f, indent=2)
        f.write("\n")


def _init_config() -> dict[str, Any]:
    """Prompt the user for a dotfiles repo path and persist it."""
    rprint("[bold yellow]No config found.[/bold yellow] Let's set one up.\n")

    repo = typer.prompt(
        "Path to your dotfiles repo",
        type=str,
    )

    repo_path = Path(repo).expanduser().resolve()
    if not repo_path.is_dir():
        rprint(f"[red]Directory not found:[/red] {repo_path}")
        raise typer.Exit(code=1)

    cfg = {**DEFAULT_CONFIG, "repo": str(repo_path)}
    save_config(cfg)
    rprint(f"[green]Config saved to {CONFIG_FILE}[/green]\n")
    return cfg


def get_repo_path(cfg: dict[str, Any]) -> Path:
    repo = Path(cfg["repo"]).expanduser().resolve()
    if not repo.is_dir():
        rprint(f"[red]Dotfiles repo not found:[/red] {repo}")
        rprint("Run [bold]dottie init[/bold] to reconfigure.")
        raise typer.Exit(code=1)
    return repo


def get_target_path(cfg: dict[str, Any]) -> Path:
    return Path(cfg["target"]).expanduser().resolve()
