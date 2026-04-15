"""Core symlinking logic for dottie."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from rich import print as rprint


class LinkState(str, Enum):
    LINKED = "linked"
    CONFLICT = "conflict"
    MISSING = "missing"


@dataclass
class DotfileEntry:
    source: Path
    target: Path
    rel_path: str
    state: LinkState = LinkState.MISSING

    @property
    def is_linked(self) -> bool:
        return (
            self.target.is_symlink() and self.target.resolve() == self.source.resolve()
        )


@dataclass
class LinkResult:
    created: list[DotfileEntry] = field(default_factory=list)
    skipped: list[DotfileEntry] = field(default_factory=list)
    conflicts: list[DotfileEntry] = field(default_factory=list)


def collect_dotfiles(
    repo: Path,
    target: Path,
    ignore: list[str],
) -> list[DotfileEntry]:
    """Walk the repo and build a list of DotfileEntry objects."""
    entries: list[DotfileEntry] = []

    for source in sorted(repo.rglob("*")):
        if source.is_dir():
            continue

        rel = source.relative_to(repo)

        if _should_ignore(rel, ignore):
            continue

        dest = target / rel
        entry = DotfileEntry(source=source, target=dest, rel_path=str(rel))

        if entry.is_linked:
            entry.state = LinkState.LINKED
        elif dest.exists() or dest.is_symlink():
            entry.state = LinkState.CONFLICT
        else:
            entry.state = LinkState.MISSING

        entries.append(entry)

    return entries


def link_dotfiles(
    entries: list[DotfileEntry],
    force: bool = False,
) -> LinkResult:
    result = LinkResult()

    for entry in entries:
        if entry.state == LinkState.LINKED:
            result.skipped.append(entry)
            continue

        if entry.state == LinkState.CONFLICT:
            if force:
                _backup_and_link(entry)
                result.created.append(entry)
            else:
                result.conflicts.append(entry)
            continue

        entry.target.parent.mkdir(parents=True, exist_ok=True)
        entry.target.symlink_to(entry.source)
        result.created.append(entry)

    return result


def unlink_dotfiles(entries: list[DotfileEntry]) -> list[DotfileEntry]:
    removed: list[DotfileEntry] = []

    for entry in entries:
        if entry.is_linked:
            entry.target.unlink()
            removed.append(entry)

    return removed


def print_status(entries: list[DotfileEntry]) -> None:
    for entry in entries:
        icon = {
            LinkState.LINKED: "[green]✔[/green]",
            LinkState.CONFLICT: "[yellow]✘[/yellow]",
            LinkState.MISSING: "[dim]○[/dim]",
        }[entry.state]
        rprint(f"  {icon} {entry.rel_path}")


def _should_ignore(rel: Path, ignore: list[str]) -> bool:
    for part in rel.parts:
        if part in ignore:
            return True
        for pattern in ignore:
            if rel.match(pattern):
                return True
    return False


def _backup_and_link(entry: DotfileEntry) -> None:
    backup = entry.target.with_suffix(entry.target.suffix + ".bak")
    if entry.target.is_symlink():
        entry.target.unlink()
    else:
        entry.target.rename(backup)
        rprint(f"  [yellow]backed up[/yellow] {entry.rel_path} → {backup.name}")
    entry.target.parent.mkdir(parents=True, exist_ok=True)
    entry.target.symlink_to(entry.source)
