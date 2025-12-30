#!/usr/bin/env python3
"""compiler.py — PyInstaller wrapper for building BinaryBuild executables

Features:
- Detects PyInstaller installation and optionally installs it
- Auto-detects PySide6 plugins and adds them to --add-data so Qt apps work after packaging
- Supports --onefile, --windowed, --name, --icon and custom add-data/hidden-imports
- Shows the final PyInstaller command and runs it (or a dry-run)

Example:
    python compiler.py --onefile --name BinaryBuild --icon path/to/icon.ico

"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

WINDOWS = os.name == 'nt'

ADD_DATA_SEP = ';' if WINDOWS else ':'


def check_pyinstaller(install_if_missing=False):
    try:
        import PyInstaller  # noqa: F401
        return True
    except Exception:
        if install_if_missing:
            print('PyInstaller not found. Installing...')
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pyinstaller'])
            try:
                import PyInstaller  # noqa: F401
                return True
            except Exception:
                return False
        return False


def find_pyside6_plugins():
    """Return the path to the PySide6 plugins directory if available."""
    try:
        import PySide6
    except Exception:
        return None
    pyside_dir = Path(PySide6.__file__).resolve().parent
    # typical location: .../site-packages/PySide6/plugins
    plugins_dir = pyside_dir / 'plugins'
    if plugins_dir.exists():
        return str(plugins_dir)
    # fallback: check parent directories
    alt = pyside_dir.parent / 'plugins'
    if alt.exists():
        return str(alt)
    return None


def build_pyinstaller_cmd(args):
    entry = args.entry
    cmd = [sys.executable, '-m', 'PyInstaller', '--noconfirm']
    if args.clean:
        cmd.append('--clean')
    if args.onefile:
        cmd.append('--onefile')
    if args.windowed:
        cmd.append('--windowed')
    if args.name:
        cmd.extend(['--name', args.name])
    if args.icon:
        cmd.extend(['--icon', args.icon])
    if args.hidden_import:
        for hi in args.hidden_import:
            cmd.extend(['--hidden-import', hi])
    add_data_items = list(args.add_data or [])

    # Auto-add PySide6 plugins if PySide6 is installed
    plugins = find_pyside6_plugins()
    if plugins:
        dest = 'PySide6/plugins'  # place plugins in the executable's directory under PySide6/plugins
        add_data_items.append(f"{plugins}{ADD_DATA_SEP}{dest}")
        print(f"Auto-including PySide6 plugins from: {plugins}")

    for ad in add_data_items:
        cmd.extend(['--add-data', ad])

    # output dirs
    if args.distpath:
        cmd.extend(['--distpath', args.distpath])
    if args.workpath:
        cmd.extend(['--workpath', args.workpath])

    cmd.append(entry)
    return cmd


def ensure_entry_exists(entry):
    if not Path(entry).exists():
        print(f"Error: entry point '{entry}' not found.")
        sys.exit(2)


def parse_args(argv=None):
    p = argparse.ArgumentParser(description='Build BinaryBuild with PyInstaller (convenience wrapper)')
    p.add_argument('--entry', default='run.py', help='Entry script to package (default: run.py)')
    p.add_argument('--onefile', action='store_true', help='Create a single-file executable')
    p.add_argument('--windowed', action='store_true', help='Suppress console window on Windows')
    p.add_argument('--nogui', action='store_true', help='Alias for --windowed (suppress console window)')
    p.add_argument('--name', default='BinaryBuild', help='Name of the output executable')
    p.add_argument('--icon', help='Path to .ico (Windows) or .icns (macOS) icon file')
    p.add_argument('--add-data', action='append', help='Additional data to include. Format: SRC{}DEST'.format(ADD_DATA_SEP))
    p.add_argument('--hidden-import', action='append', help='Hidden import for PyInstaller (can be repeated)')
    p.add_argument('--distpath', help='Custom dist path')
    p.add_argument('--workpath', help='Custom work path')
    p.add_argument('--no-install', dest='install', action='store_false', help="Don't auto-install PyInstaller if missing")
    p.set_defaults(install=True)
    p.add_argument('--clean', action='store_true', help='Pass --clean to PyInstaller')
    p.add_argument('--dry-run', action='store_true', help='Print the PyInstaller command but do not execute')
    p.add_argument('--rebuild', action='store_true', help='Remove previous build/dist before building')
    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)

    # --nogui is an alias for --windowed
    if getattr(args, 'nogui', False):
        args.windowed = True

    if not check_pyinstaller(install_if_missing=args.install):
        print('PyInstaller is required but not available. Use --no-install to skip or install it manually.')
        sys.exit(1)

    ensure_entry_exists(args.entry)

    if args.rebuild:
        # default paths
        if args.distpath:
            dist = Path(args.distpath)
        else:
            dist = Path('dist')
        if args.workpath:
            build = Path(args.workpath)
        else:
            build = Path('build')
        for p in (dist, build):
            if p.exists():
                print(f'Removing {p}...')
                shutil.rmtree(p)

    cmd = build_pyinstaller_cmd(args)
    print('\nPyInstaller command:')
    print(' '.join([f'"{c}"' if ' ' in c else c for c in cmd]))

    if args.dry_run:
        print('Dry run: not executing')
        return 0

    try:
        subprocess.check_call(cmd)
        print('\nBuild succeeded. Check the dist/ folder (or the path you specified).')
        return 0
    except subprocess.CalledProcessError as e:
        print(f'Build failed with exit code {e.returncode}')
        return e.returncode


if __name__ == '__main__':
    sys.exit(main())
