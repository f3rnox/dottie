# Dottie

A small CLI dotfile manager that symlinks files from a dotfiles repository into your home directory (or another target path).

## Requirements

- Python 3.10+

## Install

From [PyPI](https://pypi.org/project/dottie/):

```bash
pip install dottie
```

The `dottie` command is registered on your `PATH`.

## Quick start

1. Point dottie at your dotfiles repository:

   ```bash
   dottie init /path/to/your/dotfiles
   ```

   On first run without a config file, dottie will prompt for the repo path instead.

2. Create symlinks from the repo into your target directory (default: your home directory):

   ```bash
   dottie link
   ```

   Use `dottie link --dry-run` to preview changes, or `dottie link --force` to replace conflicting files (originals are backed up).

3. Inspect state:

   ```bash
   dottie status
   dottie list
   dottie config
   ```

4. Remove symlinks that dottie created (dotfiles in the repo are not deleted):

   ```bash
   dottie unlink
   ```

## Configuration

Configuration lives at `~/.config/dottie/config.json`. You can set:

- **repo** — path to your dotfiles repository
- **target** — directory where symlinks are created (default: home)
- **ignore** — path segments to skip when collecting files (default includes `.git`, `.gitignore`, `README.md`, `LICENSE`)

Use `dottie config` to view the active values.

## License

MIT — see [LICENSE](LICENSE).
