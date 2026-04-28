#!/usr/bin/env python3
"""Rebuild the Claude Dock binary from source. Cross-platform.

Windows  -> Claude Dock.exe
macOS    -> Claude Dock.app
Linux    -> claude-dock

Usage: python build.py
"""
import os
import shutil
import subprocess
import sys

DIR    = os.path.dirname(os.path.abspath(__file__))
NAME   = "Claude Dock"
EXE    = "claude-dock"
IS_WIN = sys.platform == "win32"
IS_MAC = sys.platform == "darwin"


def run(cmd):
    print("$", " ".join(cmd))
    subprocess.check_call(cmd, cwd=DIR)


def _artifact_paths():
    dist = os.path.join(DIR, "dist")
    if IS_WIN:
        return os.path.join(dist, f"{EXE}.exe"), os.path.join(DIR, f"{EXE}.exe")
    if IS_MAC:
        return os.path.join(dist, f"{NAME}.app"), os.path.join(DIR, f"{NAME}.app")
    return os.path.join(dist, NAME), os.path.join(DIR, "claude-dock")


def main():
    deps = ["pyinstaller", "plyer"]
    if IS_WIN:
        deps.append("pywin32")
    run([sys.executable, "-m", "pip", "install", "-q", *deps])

    args = [
        sys.executable, "-m", "PyInstaller",
        "--onefile", "--windowed",
        "--name", EXE if IS_WIN else NAME,
    ]
    if IS_WIN:
        # Bakes the anchor into the PE file-header icon resource so Explorer
        # shows the right thumbnail. Runtime window icon is embedded as
        # base64 PNG directly in dock.py, so no --add-data is needed.
        args += ["--icon", "assets/anchor.ico"]
    # macOS wants .icns (not shipped); Linux ignores --icon. Window icon
    # at runtime is handled in dock.py for all three platforms.
    args += ["dock.py"]
    run(args)

    src, dst = _artifact_paths()

    if os.path.exists(dst):
        (shutil.rmtree if os.path.isdir(dst) else os.remove)(dst)
    shutil.move(src, dst)

    for junk in ["dist", "build", f"{'claude-dock' if IS_WIN else NAME}.spec"]:
        p = os.path.join(DIR, junk)
        if os.path.isdir(p):
            shutil.rmtree(p)
        elif os.path.isfile(p):
            os.remove(p)

    print(f"\nBuilt: {dst}")


if __name__ == "__main__":
    main()
