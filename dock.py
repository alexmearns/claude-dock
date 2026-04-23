#!/usr/bin/env python3
"""Claude Session Dock — floating status panel for Claude Code sessions."""

import atexit
import sys
import tkinter as tk
from tkinter import filedialog, messagebox
import subprocess
import threading
import json
import os
import shutil
import time
import uuid
import webbrowser
from datetime import datetime

REPO_URL = "https://github.com/alexmearns/claude-dock"

__version__ = "0.1.0"

IS_WIN   = sys.platform == "win32"
IS_MAC   = sys.platform == "darwin"
IS_LINUX = sys.platform.startswith("linux")

_FONT = "Segoe UI" if IS_WIN else ("SF Pro Text" if IS_MAC else "Sans")

# Anchor icon, base64-encoded PNG, 256x256.
# Embedded rather than loaded from disk so the binary has no runtime asset deps.
# Regenerate via assets/_generate.py if the icon changes.
_ANCHOR_PNG_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAQAAAAEACAYAAABccqhmAAAOBUlEQVR4nO3dC9Bu1RzH8V8uqxIq"
    "YhJhSu6JGLk0bqnEwpEzqJBDxCCqYSHlFlq5jWvlVhRhcstyyyWRe1GUOTOU+z3p0M2iMn+WmePM"
    "qfPs/ezLs5/1/cy802neZ++153ne/XvW2nut/5YAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACAhbbR2AeA4cSU"
    "bytpJ0l3knQLSTeRdLWkv0v6o6TVks4N3v2ez6UOBMCSiynbCb9K0qMk3WHGzc6X9BlJ7wve/azn"
    "Q8SICIAlFVPeXdIrJT1gjt1cI+kLko4I3p3V4eFhQRAASyamvJ2kYyTt0fGuT5J0cPDuoo73ixER"
    "AEskpnyApLdJ2rSnJuzkf3Lw7os97R8DIwCWQEz5+pKOlWQB0De7aPjS4N3RA7SFnhEAExdTdpI+"
    "IulxAzd9dPAuDNwmOna9rneI4cSULcBPGOHkNy+OKR82QrvoEAEwba+StM+I7R8ZU37CiO1jTgwB"
    "Jiqm/BBJX1mAEF8j6Z7Bu1+MfBxoYew/HrQQU7ar/McvyOe3uaT3jH0QaOcGLbfDuOzi2+1bbnu5"
    "pM+X2X6/K38D20jaWdJukm7YYp8PjymvCN59quUxYSQEwMTElLeUdGiLTf8s6XBJJwbvLr+WfW8h"
    "6VmSXla+2Zt4tSQCYGK4BjAxMeUjysW/Jj4taf/g3ZoZ27CFQh+SZNOJm3hU8O5zDbfBiBZhDIkZ"
    "xZTt83pmwzfsOEl7z3rym+Cd9Rb2ssVADdtqemwYGQEwLXbl/zYNXn+6pOcG72z2XiPBu6skPVvS"
    "VxtstlcZRmAiCIBp8Q1ee4Wk/cqJ3Erw7l+S9pV02YybbCzpYW3bw/AIgGl5aIPXvrOLwh7BOysU"
    "8tYGmzx43jYxHAJgImLKdntuxwabvLPD5t9RagPMwm4nYiIIgOmwdf626m8W53c5M6/0JH4448tn"
    "rTqEBUAATMe2DV77rR7a/+aMr9s6psz8kokgAKbDCnjOqo+inn9o8Nob99A+ekAATMcmDV478z3/"
    "Bi7p6VgxIgJgOuy23qy26qF9mx3Yx7FiRATAdPytwWtv10P7s+7T7hZc2kP76AEBMB1NrurvXqYN"
    "d1l5aM8ZX/6beSYfYVgEwHT8UtI/GnTXm0wa2pAHliXDs/hph+2iZwTARJRv1bMaLs/tSpN9fbfD"
    "dtEzAmBavtbgtQ+IKT9t3gZjyk9q2Js4Y942MRwCYFo+3vD1x8SUd2nbWEz5Xg2XBP+1rEDERBAA"
    "ExK8s+m45zW8H39aTPkRTduKKe9Wio7eqMFmpwTvctO2MB4CYHre0vD1N5WUYspviCnbv6+TvSam"
    "fFR5KKiVH1OD23/2WDJMCCXBprkq8Kct7/VbpZ8PSPqYpHP/920dU96krOJbKekpLScSnRq8e2yL"
    "7TAiAmCCYsqPt+72nLuxb+y/lBWGTb7p1+efku4RvFs9534wMIYAExS8s4uBqYPw36qDk9+8iZN/"
    "mgiA6VpV6vqP7fuSrFIxJogAmKjg3UWSVjSo19cHW3a8MnhnQwBMEAEwYcE7+/bdW9KVIzR/sVUB"
    "Dt79aoS20RECYOKCd6eVB3jYJJyh/FbSg4J35w7YJnpAACyB4N2Zku5TxuN9s+cE3Dt4Z88WxMQR"
    "AEsieHdhWbV3WHkAaB/1CF5ovY1SKhxLgHkASyimvG15wOeq8rCOeVxeHi8WOfGXDwGwxGLKt7Sn"
    "A0nax7rtDXp8V5VlvR+WdHLwzi74YQkRAAsipryDpO17bGLLMkS4a2nH/n8zSVeXW4k2K/ACe6ZA"
    "KSv+9x6PxaYh91G5GA1Rv31x7F/G70OzXsHm5We7ckfBxvp9svUGJ/XcBmbARUCgYgQAUDECAKgY"
    "AQBUjAAAKkYAABUjAICKEQBAxQgAoGLMBFwca8o6+y5tKulmc+7jT6XoZ5fGrGKEtbAWYImVx3qd"
    "POdu7hW8O6ejQ8KCYQgAVIwAACpGAAAVIwCAihEAQMUIAKBiBABQMQIAqBgBAFSMAAAqRgAAFSMA"
    "gIoRAEDFCACgYgQAUDECAKgYAQBUjAAAKkYAABUjAICKEQBAxQgAoGIEAFAxAgCoGAEAVIwAACpG"
    "AAAVIwCAihEAQMUIAKBiBABQMQIAqBgBAFSMAAAqRgAAFSMAgIoRAEDFCACgYgQAUDECAKgYAQBU"
    "jAAAKkYAABUjAICKEQBAxQgAoGIEAFAxAgCo2A1UsZjyRpKeIOkASXeTdKM5dneNpL9I+rqko4N3"
    "qzs81OrFlB8k6QWS7iPpppLss2vrUknnSXp38O4TNb+51QZATPn6kj4k6Ykd7nYLSdtL2jemvF/w"
    "7uMd7rtaMeWXSHp9h7vcXNKtJe0ZUz5R0qrg3VWqUM1DgNd0fPKvbWMLl5jyPXrafzViyo/u+ORf"
    "11MkHalKVRkAMeWbSTq452YsBI7ouY0avGKANg6JKW+tClUZAJIeImmTAdp5xABtLK2Yso31dx6g"
    "KSdpN1Wo1gDYZqB2Nosp32SgtpbRFnNe7GviNqpQrQEw1MXPf0q6bKC2ltGfJf1roLZuqArVGgBD"
    "OT14d/XYBzFVwbsrJJ0x9nEsMwKgP3Zb6dU97r+mi4CEaE8IgH5Yt/XA4N03e9p/Ncp7+DxCoB8E"
    "QHfjfJtd9mtJJ0vaJXj3vg72jf+GwDGSdpX0SUm/K++1veeZN2g+1c4E7JBN+d05eDfUxaoqBe++"
    "LWnvdWZyfm+g24RLix7A/HaUdGgH+0Ezh3Dyz48A6MYRMeXtOtoXNqC816/kjZofAdANW0X4wdIt"
    "RY9iyjZsPWnOlZsoCIDuPFDSYR3uD9d+W/D+vDndIAC6dXhM2YJgmT7fhfkbiSk/VNLLxj6OZbIw"
    "H+6SsO7pKTHlRZlXfosO9nFzLYCY8u0kfZS/2W4RABt2QsP31JaVfjKmPMRqww25VQf7GH2ZbEzZ"
    "xvufahFox/d0SEuDANiwIOlnDd9XK1t1Ykx57Pd3p45ucy5C5aZ7Ntz0g5JO7emwlsbYf6BTcLmk"
    "/VtMRV0p6V0aSUx5U0kP7mBXu2tcNgtwRcNtflPqB2IDag2Aa5q8Nnj3LTunWrRzYEy5z3JW1+Xh"
    "kiwE5rVTTHmo+gn/J6b8WknPbLiZBfXTg3eXNP2cVaFaA+BvDeb5Ww/AHC7pay3aeklM+U0aXlcl"
    "z6wgx/M1sJjykS2v+L8mePel8u81Dba7RBWqNQBsDvkszg7e/eeboVSNfVJZjNKm5tyxQ10TiCnf"
    "V5LdMuvKc4asbBRTPrrlnIovrbME+wcNFgx9RxWqMgCCd+dL+soML33HOtv9sTxHwHoGTR1Y7g5s"
    "ph6VkOm6x7F5qaLcq5iyiynblfsXtdjcVmLuu3YBluCd9fTeO8O2ZwTvzlaFqgyAYpWk317H7z8c"
    "vLOrz+tbn/6Mlm0+RtKZMeVt1Z9Dy9LZrh0UU96950rNp0l6WovN7UT3wbuL1vO7F2+gx/frUhq8"
    "StUGQPDOPvhdJH1inSv8l5aFJtf6RxG8s4dJvLxl03Y76+yYcucVg8ssxL6+qTcq6x126GnI8v2W"
    "dy1sGfbK4N2P1vfL4N1lZTj0dklXrvWrq8rEovuWv4UqDVVxdaHFlG22251K1/7HwbsrZ9zuOEnP"
    "atmsXVt4g411u6glEFO+X/kG7Xus/ntJD+vi0Wfl0WzWY3ndHEU57Yr/TBN+yvDLHgFncwtWB+/+"
    "qsoRAPOPtz8g6clz7OZcG1LMMwaNKT+2HIeN1Yeq1ntA8K71RJuY8p0lWYDaM//aOiR495Y5tq8e"
    "AdBNCJww5zjSuqNvlnRU8O7iBm1b3fy3SnqqxmHlz14YvPvTrBvElLe0bez2aHkgR1svCt69cY7t"
    "QQ+g0xA4voMT0YYep5Tad18uV7HX196O5ZbkcyTZCTWmK8q0WzvuM9c3fIop36o8jcmXsl7zrpMI"
    "wTu7VYg50QPoSBnPvrGUquqCXSO4oPysKePWrcoY1v67iKwn83NJF5frKXY94rblCT9d7f95wbtj"
    "O9pf9QiAjsWUX1C689XeYemJ9Sz2Cd7ZqkB0hADoQUzZurl2q5CyVd2w+/sreM5C9wiAnsSU717m"
    "GHR+37wyZ0l6fPDuV2MfyDKim9qT4N15pS4AXdb27OEqu3Ly94cewDAXBw+yW3wdXP2uhd39OCh4"
    "Z3Mb0CMCYCBl4suJpVeAa2dPA94/ePdL3qT+MQQYSJk6e/9S1vofQ7U7IZeVacE2zZiTfyD0AEYQ"
    "U95e0tskPXKM9heQTSI6OHhnpbwwIAJgRDHlFWVB0B1Up5+UE98WMWEEDAFGVCa13KUUC6np2+/C"
    "Umh1R07+cdEDWBDlOQLPLlOJ+ywYMqYLSo/n/cG7NlWV0DECYDEffrmyFPW0QhnL4OuSbNnuqWuX"
    "7ML4CIAFVop8PL3UIRxqrX+X03dPLt/254x9MFg/AmACykM+7ILhfpJ2W+AJRVZO7QvlST6fpZu/"
    "+AiAiSllrfaQ9GhJey3As/t+Ielzkj4j6fTgHXMcJoQAmLhSpHPX8mNFTu84R329WZbk2q27b0uy"
    "6sjf4N79tBEASyambCe/hcJdS6HTW5enBG9Tegs3LkOIjUuRkf8V2riy/FjxkT+U4p/2YxVzV5cT"
    "/0Iu4gFLdMehPH0XAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAALSA/g2TUyLcJYP/DgAAAABJRU5ErkJggg=="
)

# ── Window control ────────────────────────────────────────────────────────────

if IS_WIN:
    import ctypes
    _u32 = ctypes.windll.user32
    _WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

    def _all_hwnds():
        """Return set of all top-level window handles currently open."""
        hwnds = set()
        def cb(hwnd, _):
            hwnds.add(hwnd)
            return True
        _u32.EnumWindows(_WNDENUMPROC(cb), 0)
        return hwnds

    _GWL_EXSTYLE      = -20
    _WS_EX_TOOLWINDOW = 0x00000080
    _WS_EX_APPWINDOW  = 0x00040000
    _SWP_FLAGS = 0x0001 | 0x0002 | 0x0004 | 0x0010 | 0x0020

    def _hide_from_taskbar(hwnd):
        """Remove window from taskbar without closing or hiding it."""
        ex = _u32.GetWindowLongW(hwnd, _GWL_EXSTYLE)
        _u32.SetWindowLongW(hwnd, _GWL_EXSTYLE,
                            (ex & ~_WS_EX_APPWINDOW) | _WS_EX_TOOLWINDOW)
        _u32.SetWindowPos(hwnd, None, 0, 0, 0, 0, _SWP_FLAGS)
        # Kill minimize/restore animations so the minimize-guard's SW_HIDE
        # isn't preceded by a visible slide-to-corner animation flash.
        try:
            DWMWA_TRANSITIONS_FORCEDISABLED = 3
            val = ctypes.c_int(1)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, DWMWA_TRANSITIONS_FORCEDISABLED,
                ctypes.byref(val), ctypes.sizeof(val),
            )
        except Exception:
            pass

    def _show_in_taskbar(hwnd):
        """Restore a previously hidden window to the taskbar."""
        if not hwnd:
            return
        ex = _u32.GetWindowLongW(hwnd, _GWL_EXSTYLE)
        _u32.SetWindowLongW(hwnd, _GWL_EXSTYLE,
                            (ex & ~_WS_EX_TOOLWINDOW) | _WS_EX_APPWINDOW)
        _u32.SetWindowPos(hwnd, None, 0, 0, 0, 0, _SWP_FLAGS)

    def _disable_close_button(hwnd):
        """Gray out the X button so it can't accidentally close the terminal."""
        SC_CLOSE, MF_BYCOMMAND = 0xF060, 0x0000
        hmenu = _u32.GetSystemMenu(hwnd, False)
        if hmenu:
            _u32.DeleteMenu(hmenu, SC_CLOSE, MF_BYCOMMAND)
            _u32.DrawMenuBar(hwnd)

    def _is_iconic(hwnd):
        return bool(hwnd) and bool(_u32.IsIconic(hwnd))

    def _find_hwnd_by_title(title):
        """Return hwnd of the first top-level window whose title contains
        the given substring, or None."""
        if not title:
            return None
        buf = ctypes.create_unicode_buffer(256)
        result = [None]
        @_WNDENUMPROC
        def cb(hwnd, _):
            _u32.GetWindowTextW(hwnd, buf, 256)
            if buf.value and title in buf.value:
                result[0] = hwnd
                return False
            return True
        _u32.EnumWindows(cb, 0)
        return result[0]

    def _force_focus(hwnd):
        if not hwnd:
            return
        _u32.ShowWindow(hwnd, 5)
        _u32.ShowWindow(hwnd, 9)
        _u32.keybd_event(0x12, 0, 0, 0)
        _u32.SetForegroundWindow(hwnd)
        _u32.keybd_event(0x12, 0, 2, 0)

else:
    def _all_hwnds():                return set()
    def _hide_from_taskbar(hwnd):    pass
    def _show_in_taskbar(hwnd):      pass
    def _disable_close_button(hwnd): pass
    def _is_iconic(hwnd):            return False
    def _force_focus(hwnd):          pass
    def _find_hwnd_by_title(title):  return None

def _pid_alive(pid):
    """Return True if a process with the given PID is still running (Mac/Linux)."""
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True  # process exists but we can't signal it

# ── Notifications ─────────────────────────────────────────────────────────────

try:
    from plyer import notification as _plyer
    def _toast(title, body):
        _plyer.notify(title=title, message=body, app_name="Claude Dock", timeout=5)
except ImportError:
    def _toast(title, body):
        # Title/body may originate from terminal window titles, which are
        # attacker-influenceable. Pass them via env/argv, never interpolate
        # into shell scripts.
        try:
            if IS_WIN:
                script = (
                    "Add-Type -AssemblyName System.Windows.Forms;"
                    "$n=New-Object System.Windows.Forms.NotifyIcon;"
                    "$n.Icon=[System.Drawing.SystemIcons]::Information;"
                    "$n.Visible=$true;"
                    "$n.ShowBalloonTip(5000,$env:CLAUDE_DOCK_TOAST_TITLE,"
                    "$env:CLAUDE_DOCK_TOAST_BODY,"
                    "[System.Windows.Forms.ToolTipIcon]::Info)"
                )
                env = {**os.environ,
                       "CLAUDE_DOCK_TOAST_TITLE": title,
                       "CLAUDE_DOCK_TOAST_BODY":  body}
                subprocess.Popen(
                    ["powershell", "-WindowStyle", "Hidden", "-Command", script],
                    creationflags=0x08000000, env=env,
                )
            elif IS_MAC:
                subprocess.Popen(
                    ["osascript", "-e",
                     'on run argv\n'
                     '  display notification (item 2 of argv) '
                     'with title (item 1 of argv)\n'
                     'end run',
                     title, body],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                )
            else:
                subprocess.Popen(
                    ["notify-send", title, body],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                )
        except Exception:
            pass

# ── Constants ─────────────────────────────────────────────────────────────────

CONFIG_DIR   = os.path.join(os.path.expanduser("~"), ".claude-dock")
CONFIG_FILE  = os.path.join(CONFIG_DIR, "config.json")
SESSIONS_DIR = os.path.join(CONFIG_DIR, "sessions")

if IS_WIN:
    TERMINALS = {
        "cmd":        "Command Prompt",
        "powershell": "PowerShell",
        "git_bash":   "Git Bash",
        "wsl":        "WSL",
    }
    _PREFERRED_TERM = "cmd"
elif IS_MAC:
    TERMINALS = {
        "terminal": "Terminal",
        "iterm2":   "iTerm2",
    }
    _PREFERRED_TERM = "terminal"
else:
    TERMINALS = {
        "bash":           "Bash (xterm)",
        "gnome-terminal": "GNOME Terminal",
        "konsole":        "Konsole",
    }
    _PREFERRED_TERM = "gnome-terminal"

def _terminal_available(key):
    """Return True if the named terminal is installed on this machine."""
    from shutil import which
    if IS_WIN:
        if key == "cmd":
            return True  # always present on Windows
        if key == "powershell":
            return which("powershell") is not None or which("pwsh") is not None
        if key == "git_bash":
            paths = [r"C:\Program Files\Git\bin\bash.exe",
                     r"C:\Program Files (x86)\Git\bin\bash.exe"]
            return any(os.path.exists(p) for p in paths) or which("bash.exe") is not None
        if key == "wsl":
            return which("wsl") is not None
    elif IS_MAC:
        if key == "terminal":
            return True  # bundled with macOS
        if key == "iterm2":
            return os.path.exists("/Applications/iTerm.app")
    else:
        if key == "bash":
            return which("xterm") is not None
        if key == "gnome-terminal":
            return which("gnome-terminal") is not None
        if key == "konsole":
            return which("konsole") is not None
    return False

def _available_terminals():
    """{key: label} filtered to terminals actually installed."""
    return {k: v for k, v in TERMINALS.items() if _terminal_available(k)}

def _default_terminal():
    """Preferred terminal if installed, otherwise first available."""
    if _terminal_available(_PREFERRED_TERM):
        return _PREFERRED_TERM
    return next(iter(_available_terminals()), _PREFERRED_TERM)

_DEFAULT_TERM = _default_terminal()

def _claude_code_installed():
    """Detect Claude Code via PATH or the ~/.claude workspace."""
    from shutil import which
    if which("claude") is not None:
        return True
    claude_dir = os.path.join(os.path.expanduser("~"), ".claude")
    if os.path.isdir(claude_dir):
        for marker in ("settings.json", "projects", "history.jsonl", "skills"):
            if os.path.exists(os.path.join(claude_dir, marker)):
                return True
    return False

C = {   # Catppuccin Mocha
    "bg":      "#1E1E2E",
    "base":    "#181825",
    "surface": "#313244",
    "text":    "#CDD6F4",
    "dim":     "#6C7086",
    "muted":   "#45475A",
    "amber":   "#F9E2AF",
    "green":   "#A6E3A1",
    "blue":    "#89B4FA",
    "teal":    "#94E2D5",
}

# ── Claude Code Stop hook ─────────────────────────────────────────────────────

def _run_hook(action):
    """Hook-mode entry point. Invoked when the dock exe is called with --hook."""
    sid = os.environ.get("CLAUDE_DOCK_SESSION_ID", "")
    # Reject anything that isn't a bare hex token; the dock itself only
    # emits uuid4().hex[:8], but the env var is user-reachable.
    if not sid or not sid.isalnum() or len(sid) > 64:
        return
    os.makedirs(SESSIONS_DIR, exist_ok=True)
    idle_f = os.path.join(SESSIONS_DIR, sid + ".idle")
    run_f  = os.path.join(SESSIONS_DIR, sid + ".running")
    if action == "stop":
        open(idle_f, "a").close()
    elif action == "tool":
        if os.path.exists(idle_f):
            try: os.remove(idle_f)
            except Exception: pass
        open(run_f, "a").close()

def _is_our_hook_cmd(cmd):
    """Return True if a hook command string was installed by this app."""
    low = cmd.lower()
    if "on_hook.py" in cmd:
        return True
    if "--hook" in cmd and ("claude dock" in low or "claude-dock" in low or "dock.py" in low):
        return True
    return False

def _ensure_hooks():
    """
    Install Stop + PreToolUse hooks in ~/.claude/settings.json.
    Stop       → signals Claude finished responding  (.idle file)
    PreToolUse → signals Claude started working      (.running file)
    Hooks invoke the dock binary itself with --hook, so no external
    Python is required on the user's machine.
    """
    import sys as _sys

    if getattr(_sys, "frozen", False):
        exe = _sys.executable
        stop_cmd = f'"{exe}" --hook stop'
        tool_cmd = f'"{exe}" --hook tool'
    else:
        py     = _sys.executable
        script = os.path.abspath(__file__)
        stop_cmd = f'"{py}" "{script}" --hook stop'
        tool_cmd = f'"{py}" "{script}" --hook tool'

    settings_path = os.path.join(os.path.expanduser("~"), ".claude", "settings.json")
    settings = {}
    if os.path.exists(settings_path):
        try:
            with open(settings_path) as f:
                settings = json.load(f)
        except Exception:
            pass

    hooks = settings.setdefault("hooks", {})

    def _upsert(event, cmd):
        lst = hooks.setdefault(event, [])
        for entry in lst:
            for h in entry.get("hooks", []):
                if _is_our_hook_cmd(h.get("command", "")):
                    h["command"] = cmd
                    return
        lst.append({"matcher": "", "hooks": [{"type": "command", "command": cmd}]})

    _upsert("Stop", stop_cmd)
    _upsert("PreToolUse", tool_cmd)

    os.makedirs(os.path.dirname(settings_path), exist_ok=True)
    with open(settings_path, "w") as f:
        json.dump(settings, f, indent=2)

def _uninstall():
    """Remove hooks from ~/.claude/settings.json and delete ~/.claude-dock/."""
    settings_path = os.path.join(os.path.expanduser("~"), ".claude", "settings.json")
    removed = 0

    if os.path.exists(settings_path):
        try:
            with open(settings_path) as f:
                settings = json.load(f)
        except Exception:
            settings = None

        if isinstance(settings, dict):
            hooks = settings.get("hooks", {})
            for event in list(hooks.keys()):
                kept_entries = []
                for entry in hooks[event]:
                    kept_hooks = []
                    for h in entry.get("hooks", []):
                        if _is_our_hook_cmd(h.get("command", "")):
                            removed += 1
                        else:
                            kept_hooks.append(h)
                    if kept_hooks:
                        entry["hooks"] = kept_hooks
                        kept_entries.append(entry)
                if kept_entries:
                    hooks[event] = kept_entries
                else:
                    del hooks[event]
            if not hooks:
                settings.pop("hooks", None)

            try:
                with open(settings_path, "w") as f:
                    json.dump(settings, f, indent=2)
            except Exception as e:
                print(f"Warning: could not update {settings_path}: {e}")

    if os.path.isdir(CONFIG_DIR):
        shutil.rmtree(CONFIG_DIR, ignore_errors=True)

    print(f"Uninstalled. Removed {removed} hook(s) and deleted {CONFIG_DIR}.")
    print("Delete the binary itself to finish removal.")

# ── Config ────────────────────────────────────────────────────────────────────

class Config:
    _DEFAULTS = {"terminal": _DEFAULT_TERM, "folder": "", "x": None, "y": 100,
                 "width": 240, "height": 56, "consented": False,
                 "hide_terminals_from_taskbar": False}

    def __init__(self):
        os.makedirs(CONFIG_DIR, exist_ok=True)
        os.makedirs(SESSIONS_DIR, exist_ok=True)
        self._d = self._DEFAULTS.copy()
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE) as f:
                    self._d.update(json.load(f))
            except Exception:
                pass

    def __getitem__(self, k):     return self._d.get(k)
    def __setitem__(self, k, v):  self._d[k] = v
    def save(self):
        with open(CONFIG_FILE, "w") as f:
            json.dump(self._d, f, indent=2)
    def ready(self):
        f = self._d.get("folder", "")
        return bool(f) and os.path.isdir(f)

# ── Session ───────────────────────────────────────────────────────────────────

def _to_unix(win_path, style):
    """Convert a Windows path to Unix-style for Git Bash or WSL."""
    drive = win_path[0].lower()
    rest  = win_path[2:].replace("\\", "/")
    return f"/{drive}{rest}" if style == "git_bash" else f"/mnt/{drive}{rest}"

def _find_git_bash():
    for p in [r"C:\Program Files\Git\bin\bash.exe",
              r"C:\Program Files (x86)\Git\bin\bash.exe"]:
        if os.path.exists(p):
            return p
    return "bash.exe"

def _find_linux_terminal(preferred):
    """Return (cmd_prefix, gnome_style) for the first available Linux terminal."""
    from shutil import which
    options = {
        "gnome-terminal": (["gnome-terminal", "--"], True),
        "konsole":        (["konsole", "-e"],         False),
        "bash":           (["xterm", "-e"],            False),
    }
    for name in [preferred] + [k for k in options if k != preferred]:
        cmd, gnome = options.get(name, (["xterm", "-e"], False))
        if which(cmd[0]):
            return cmd, gnome
    return ["xterm", "-e"], False


class Session:
    def __init__(self, config: Config):
        self.id       = uuid.uuid4().hex[:8]
        self.label    = "Starting…"
        self._folder  = os.path.normpath(config["folder"] or "")
        term          = config["terminal"] or _DEFAULT_TERM
        self._term    = term if _terminal_available(term) else _default_terminal()
        self._hide_taskbar = bool(config["hide_terminals_from_taskbar"])
        self.status   = "running"
        self._start   = datetime.now()
        self._end     = None
        self._title   = f"Claude-{self.id}"
        self._done    = os.path.join(SESSIONS_DIR, f"{self.id}.done")
        self._idle    = os.path.join(SESSIONS_DIR, f"{self.id}.idle")
        self._running = os.path.join(SESSIONS_DIR, f"{self.id}.running")
        self._pidfile = os.path.join(SESSIONS_DIR, f"{self.id}.pid")
        self._proc    = None
        self._hwnd    = None
        self._done_cbs    = []
        self._idle_cbs    = []
        self._running_cbs = []
        self._label_cbs   = []

    def on_complete(self, cb):     self._done_cbs.append(cb)
    def on_idle(self, cb):         self._idle_cbs.append(cb)
    def on_running(self, cb):      self._running_cbs.append(cb)
    def on_label_change(self, cb): self._label_cbs.append(cb)

    def elapsed(self):
        sec = int(((self._end or datetime.now()) - self._start).total_seconds())
        if sec < 60:   return f"{sec}s"
        if sec < 3600: return f"{sec // 60}m"
        return f"{sec // 3600}h {(sec % 3600) // 60}m"

    def focus(self):    _force_focus(self._hwnd)

    def restore_to_taskbar(self):
        """Put this session's terminal window back in the taskbar. Safe to
        call when taskbar hiding was never applied (no-op)."""
        if self._hide_taskbar and self._hwnd:
            _show_in_taskbar(self._hwnd)

    def kill(self):
        """Close the terminal window and mark the session done."""
        # Graceful close first, so the shell has a chance to save state.
        try:
            if IS_WIN and self._hwnd:
                WM_CLOSE = 0x0010
                _u32.PostMessageW(self._hwnd, WM_CLOSE, 0, 0)
            elif IS_MAC:
                script = (
                    f'tell application "Terminal" to close '
                    f'(every window whose name contains "{self._title}")'
                )
                subprocess.Popen(
                    ["osascript", "-e", script],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                )
            else:
                from shutil import which
                if which("wmctrl"):
                    subprocess.Popen(
                        ["wmctrl", "-c", self._title],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    )
        except Exception:
            pass
        # Force-kill the backing process so we don't wait on Windows' 5-second
        # CTRL_CLOSE grace period when the user explicitly dismissed the card.
        try:
            if self._proc is not None and self._proc.poll() is None:
                self._proc.terminate()
        except Exception:
            pass
        # Nudge the watcher so status flips to done even if neither of the
        # above took effect (e.g. hwnd never captured, proc already gone).
        try:
            open(self._done, "a").close()
        except Exception:
            pass

    def launch(self):
        os.makedirs(SESSIONS_DIR, exist_ok=True)
        t = self._term

        if IS_WIN:
            before = _all_hwnds()

            if t == "cmd":
                # Inline command string (no .bat file) so closing the terminal
                # doesn't trigger Windows' "Terminate batch job (Y/N)?" prompt.
                # Passed as a string (not a list) so Python's list2cmdline doesn't
                # escape the inner quotes with \", which cmd.exe misparses as paths.
                cmd_line = (
                    f'title {self._title}'
                    f' & set "CLAUDE_DOCK_SESSION_ID={self.id}"'
                    f' & cd /d "{self._folder}"'
                    f' & claude'
                    f' & type nul > "{self._done}"'
                )
                self._proc = subprocess.Popen(
                    f'cmd.exe /K {cmd_line}',
                    creationflags=subprocess.CREATE_NEW_CONSOLE,
                )
            elif t == "powershell":
                # Single-quoted values avoid inner double quotes so the outer
                # -Command "..." wrapper passes through CreateProcess cleanly.
                ps_line = (
                    f"$host.ui.RawUI.WindowTitle = '{self._title}'; "
                    f"$env:CLAUDE_DOCK_SESSION_ID = '{self.id}'; "
                    f"Set-Location '{self._folder}'; "
                    f"& claude; "
                    f"New-Item -Path '{self._done}' -ItemType File -Force | Out-Null"
                )
                self._proc = subprocess.Popen(
                    f'powershell.exe -NoExit -ExecutionPolicy Bypass -Command "{ps_line}"',
                    creationflags=subprocess.CREATE_NEW_CONSOLE,
                )
            elif t == "git_bash":
                self._proc = subprocess.Popen(
                    [_find_git_bash(), "--login", "-i", self._sh()],
                    creationflags=subprocess.CREATE_NEW_CONSOLE,
                )
            elif t == "wsl":
                self._proc = subprocess.Popen(
                    ["wsl", "bash", self._sh()],
                    creationflags=subprocess.CREATE_NEW_CONSOLE,
                )

            threading.Thread(target=self._capture_hwnd, args=(before,), daemon=True).start()
            threading.Thread(target=self._poll_title, daemon=True).start()
            if self._hide_taskbar:
                threading.Thread(target=self._minimize_guard, daemon=True).start()

        elif IS_MAC:
            sh = self._sh()
            os.chmod(sh, 0o755)
            sh_esc = sh.replace('"', '\\"')
            if t == "iterm2":
                script = (f'tell application "iTerm2"\n'
                          f'  create window with default profile command "{sh_esc}"\n'
                          f'end tell')
            else:
                script = f'tell application "Terminal" to do script "{sh_esc}"'
            subprocess.Popen(
                ["osascript", "-e", script],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )

        else:  # Linux
            sh = self._sh()
            os.chmod(sh, 0o755)
            cmd, gnome_style = _find_linux_terminal(t)
            if gnome_style:
                subprocess.Popen(cmd + ["bash", sh])
            else:
                subprocess.Popen(cmd + [sh])

        threading.Thread(target=self._watch, daemon=True).start()

    def _capture_hwnd(self, before_hwnds):
        """Find and configure the new terminal window (Windows only)."""
        buf      = ctypes.create_unicode_buffer(256)
        deadline = time.time() + 15
        while time.time() < deadline:
            after = _all_hwnds()
            for hwnd in (after - before_hwnds):
                _u32.GetWindowTextW(hwnd, buf, 256)
                if buf.value:
                    self._hwnd = hwnd
                    if self._hide_taskbar:
                        _hide_from_taskbar(hwnd)
                        _disable_close_button(hwnd)
                    return
            time.sleep(0.3)

    def _minimize_guard(self):
        """Tool windows leave an orphan stub on the desktop when minimized.
        Watch for that state and replace it with a full SW_HIDE so the
        terminal simply disappears. Clicking the dock card restores it."""
        deadline = time.time() + 15
        while not self._hwnd and time.time() < deadline:
            time.sleep(0.1)
        while self.status != "done":
            try:
                if _is_iconic(self._hwnd):
                    _u32.ShowWindow(self._hwnd, 0)  # SW_HIDE
            except Exception:
                pass
            time.sleep(0.02)

    def _poll_title(self):
        """Continuously pull the terminal window title (Windows only)."""
        deadline = time.time() + 15
        while not self._hwnd and time.time() < deadline:
            time.sleep(0.5)
        if not self._hwnd:
            return

        buf      = ctypes.create_unicode_buffer(512)
        last     = ""
        suffixes = [" - Windows Terminal", " — Windows Terminal",
                    " - cmd.exe", " - Command Prompt"]

        while self.status != "done":
            _u32.GetWindowTextW(self._hwnd, buf, 512)
            raw   = buf.value
            clean = raw
            for s in suffixes:
                clean = clean.replace(s, "")
            clean = clean.strip()
            if clean and clean != last and clean != self._title:
                last       = clean
                self.label = clean
                for cb in self._label_cbs:
                    cb(clean)
            time.sleep(2)

    def _sh(self):
        """Shell script for Mac, Linux, Git Bash, and WSL."""
        p       = os.path.join(SESSIONS_DIR, f"{self.id}.sh")
        folder  = self._folder
        done    = self._done
        pidfile = self._pidfile

        if IS_WIN:
            style   = "git_bash" if self._term == "git_bash" else "wsl"
            folder  = _to_unix(folder,  style)
            done    = _to_unix(done,    style)
            pidfile = _to_unix(pidfile, style)

        with open(p, "w", newline="\n") as f:
            f.write("#!/bin/bash\n")
            f.write(f'printf "\\033]0;{self._title}\\007"\n')
            f.write(f'echo $$ > "{pidfile}"\n')
            f.write(f'export CLAUDE_DOCK_SESSION_ID="{self.id}"\n')
            f.write(f'cd "{folder}"\n')
            f.write("claude\n")
            f.write(f'touch "{done}"\n')
            f.write("exec bash\n")
        return p

    def _watch(self):
        shell_pid      = None
        last_pid_check = 0.0

        while True:
            if os.path.exists(self._running):
                try: os.remove(self._running)
                except Exception: pass
                self.status = "running"
                for cb in self._running_cbs: cb(self)

            if os.path.exists(self._idle):
                try: os.remove(self._idle)
                except Exception: pass
                self.status = "idle"
                for cb in self._idle_cbs: cb(self)

            if os.path.exists(self._done):
                break
            if self._proc is not None and self._proc.poll() is not None:
                break

            # Mac/Linux: poll the shell PID written by the script at startup.
            # os.kill(pid, 0) checks existence without sending a signal.
            if not IS_WIN and time.time() - last_pid_check > 1.0:
                last_pid_check = time.time()
                if shell_pid is None and os.path.exists(self._pidfile):
                    try:
                        shell_pid = int(open(self._pidfile).read().strip())
                    except (ValueError, OSError):
                        pass
                if shell_pid is not None and not _pid_alive(shell_pid):
                    break

            time.sleep(0.1)

        self.status = "done"
        self._end   = datetime.now()
        for cb in self._done_cbs: cb(self)

    def cleanup(self):
        for ext in (".done", ".idle", ".running", ".sh", ".pid"):
            f = os.path.join(SESSIONS_DIR, f"{self.id}{ext}")
            try:
                if os.path.exists(f): os.remove(f)
            except Exception:
                pass

# ── Card widget ───────────────────────────────────────────────────────────────

class Card(tk.Frame):
    _DOT = {"running": "●", "idle": "⏸", "done": "✓"}
    _CLR = {"running": "amber", "idle": "teal", "done": "green"}

    def __init__(self, parent, session: Session, dismiss_cb):
        super().__init__(parent, bg=C["bg"], padx=8, pady=6)
        self._s = session
        self._dismiss = dismiss_cb
        self._build()
        session.on_label_change(lambda l: self.after(0, lambda: self._update_label(l)))
        session.on_running(lambda s:  self.after(0, lambda: self._set_state("running")))
        session.on_idle(lambda s:     self.after(0, lambda: self._set_state("idle")))

    def _build(self):
        self._word = "open"

        row = tk.Frame(self, bg=C["bg"])
        row.pack(fill=tk.X)

        self._dot = tk.Label(row, text=self._DOT["running"],
                              fg=C[self._CLR["running"]], bg=C["bg"],
                              font=(_FONT, 10))
        self._dot.pack(side=tk.LEFT, padx=(0, 5))

        short = (self._s.label[:24] + "…") if len(self._s.label) > 24 else self._s.label
        self._lbl = tk.Label(row, text=short, fg=C["text"], bg=C["bg"],
                              font=(_FONT, 9), anchor="w")
        self._lbl.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self._x = tk.Label(row, text="×", fg=C["dim"], bg=C["bg"],
                            font=(_FONT, 13), cursor="hand2")
        self._x.pack(side=tk.RIGHT)
        self._x.bind("<Button-1>", lambda e: self._dismiss(self))

        self._sub = tk.Label(self, text=f"open · {self._s.elapsed()}",
                              fg=C["dim"], bg=C["bg"],
                              font=(_FONT, 8), anchor="w")
        self._sub.pack(fill=tk.X, padx=(22, 0))

        tk.Frame(self, bg=C["surface"], height=1).pack(fill=tk.X, pady=(5, 0))

        for w in [self, row, self._dot, self._lbl, self._sub]:
            w.bind("<Button-1>", lambda e: self._s.focus())
            w.configure(cursor="hand2")

        self._tick()

    def _tick(self):
        if not self.winfo_exists():
            return
        if self._s.status == "done":
            if self._word != "done":
                self._set_state("done")
            return
        self._sub.config(text=f"{self._word} · {self._s.elapsed()}")
        self.after(1000, self._tick)

    def _update_label(self, label):
        if not self.winfo_exists(): return
        short = (label[:24] + "…") if len(label) > 24 else label
        self._lbl.config(text=short)

    def _set_state(self, state):
        if not self.winfo_exists():
            return
        self._dot.config(text=self._DOT[state], fg=C[self._CLR[state]])
        if state == "running":
            self._word = "working"
            self._sub.config(text=f"working · {self._s.elapsed()}")
        elif state == "idle":
            self._word = "waiting"
            self._sub.config(text=f"waiting · {self._s.elapsed()}")
        elif state == "done":
            self._word = "done"
            self._sub.config(text=f"done · {self._s.elapsed()}")
            # Brief pause so the user sees the "done" checkmark before
            # the card vanishes.
            self.after(1200, lambda: self._dismiss(self))

# ── Dialogs ───────────────────────────────────────────────────────────────────

class SetupDlg(tk.Toplevel):
    def __init__(self, parent, config: Config):
        super().__init__(parent)
        self.config = config
        self.title("Setup")
        self.configure(bg=C["bg"])
        self.resizable(False, False)
        self.grab_set()
        self.transient(parent)
        f = tk.Frame(self, bg=C["bg"], padx=20, pady=16)
        f.pack()

        tk.Label(f, text="Claude Dock", fg=C["text"], bg=C["bg"],
                  font=(_FONT, 12, "bold")).pack(pady=(0, 2))
        link = tk.Label(f, text="github.com/alexmearns/claude-dock",
                         fg=C["blue"], bg=C["bg"],
                         font=(_FONT, 9, "underline"),
                         cursor="hand2")
        link.pack(pady=(0, 14))
        link.bind("<Button-1>", lambda e: webbrowser.open(REPO_URL))

        tk.Label(f, text="Default folder  (where you run claude)",
                  fg=C["text"], bg=C["bg"],
                  font=(_FONT, 9)).pack(anchor="w")
        row = tk.Frame(f, bg=C["bg"])
        row.pack(fill=tk.X, pady=(4, 12))
        self._fv = tk.StringVar(value=self.config["folder"] or "")
        tk.Entry(row, textvariable=self._fv, width=28,
                  font=(_FONT, 9), bg=C["surface"], fg=C["text"],
                  insertbackground=C["text"], relief="flat").pack(
                      side=tk.LEFT, fill=tk.X, expand=True)
        tk.Button(row, text="Browse", command=self._browse,
                   bg=C["surface"], fg=C["text"], relief="flat",
                   font=(_FONT, 9), cursor="hand2",
                   padx=8).pack(side=tk.RIGHT, padx=(6, 0))

        tk.Label(f, text="Terminal", fg=C["text"], bg=C["bg"],
                  font=(_FONT, 9)).pack(anchor="w")
        avail = _available_terminals()
        current = self.config["terminal"]
        if current not in avail:
            current = _default_terminal()
        self._tv = tk.StringVar(value=current)
        if avail:
            for k, v in avail.items():
                tk.Radiobutton(f, text=v, variable=self._tv, value=k,
                                bg=C["bg"], fg=C["text"],
                                selectcolor=C["surface"],
                                activebackground=C["bg"],
                                font=(_FONT, 9)).pack(anchor="w")
        else:
            tk.Label(f, text="No supported terminals installed",
                      fg=C["amber"], bg=C["bg"],
                      font=(_FONT, 9)).pack(anchor="w", pady=(0, 4))

        if IS_WIN:
            self._hv = tk.BooleanVar(value=bool(self.config["hide_terminals_from_taskbar"]))
            tk.Checkbutton(f, text="Hide terminals from taskbar",
                            variable=self._hv,
                            bg=C["bg"], fg=C["text"],
                            selectcolor=C["surface"],
                            activebackground=C["bg"],
                            font=(_FONT, 9)).pack(anchor="w", pady=(10, 0))
            tk.Label(f, text="Restored automatically if you close the dock.",
                      fg=C["dim"], bg=C["bg"],
                      font=(_FONT, 8)).pack(anchor="w", padx=(20, 0))
        else:
            self._hv = None

        btn_row = tk.Frame(f, bg=C["bg"])
        btn_row.pack(fill=tk.X, pady=(14, 0))

        tk.Button(btn_row, text="Save", command=self._save,
                   bg=C["blue"], fg=C["base"], relief="flat",
                   font=(_FONT, 9, "bold"), padx=16, pady=6,
                   cursor="hand2").pack(side=tk.LEFT)

        tk.Button(btn_row, text="Uninstall", command=self._uninstall,
                   bg=C["surface"], fg=C["amber"], relief="flat",
                   font=(_FONT, 9), padx=10, pady=6,
                   cursor="hand2").pack(side=tk.RIGHT)

        self.wait_window()

    def _browse(self):
        d = filedialog.askdirectory(initialdir=self._fv.get() or os.path.expanduser("~"))
        if d: self._fv.set(d)

    def _save(self):
        folder = self._fv.get().strip()
        if not os.path.isdir(folder): return
        self.config["folder"] = folder
        self.config["terminal"] = self._tv.get()
        if self._hv is not None:
            self.config["hide_terminals_from_taskbar"] = bool(self._hv.get())
        self.config.save()
        self.destroy()

    def _uninstall(self):
        ok = messagebox.askyesno(
            "Uninstall Claude Dock",
            "This will:\n\n"
            "  • Remove Claude Dock's hooks from ~/.claude/settings.json\n"
            "  • Delete ~/.claude-dock/ (your preferences + session state)\n\n"
            "Claude Code itself is not affected. You'll still need to "
            "delete the app binary yourself.\n\n"
            "Continue?",
            icon=messagebox.WARNING,
            parent=self,
        )
        if not ok:
            return
        _uninstall()
        messagebox.showinfo(
            "Uninstall complete",
            "Hooks and config removed. Close this window and delete the "
            "app binary to finish.",
            parent=self,
        )
        self.destroy()
        self.master.destroy()

# ── Enter key watcher — flip card back to running when user sends a message ───

def start_enter_watcher(get_cards):
    """
    Poll GetAsyncKeyState for Enter (~20 Hz) — Windows only.
    Detects leading edge (key-down transition) while one of our terminals is focused.
    """
    if not IS_WIN:
        return

    _VK_RETURN = 0x0D
    prev = [False]

    def _loop():
        while True:
            time.sleep(0.05)
            try:
                down = bool(_u32.GetAsyncKeyState(_VK_RETURN) & 0x8000)
                if down and not prev[0]:
                    focused = _u32.GetForegroundWindow()
                    for card in get_cards():
                        if card._s._hwnd == focused and card._s.status == "idle":
                            card._s.status = "running"
                            card.after(0, lambda c=card: c._set_state("running"))
                prev[0] = down
            except Exception:
                pass

    threading.Thread(target=_loop, daemon=True).start()

# ── Main dock ─────────────────────────────────────────────────────────────────

class Dock(tk.Tk):
    MIN_W = 200

    def __init__(self):
        super().__init__()
        self.cfg   = Config()
        self._cards: list[Card] = []
        self._geo_after = None
        self._claude_ok = _claude_code_installed()

        self.title(f"Claude Dock {__version__}")
        self.configure(bg=C["bg"])
        self.attributes("-topmost", True)
        self.resizable(True, True)
        self._set_window_icon()
        self._place()
        self.withdraw()  # hide until consent resolved

        if self._claude_ok and not self.cfg["consented"]:
            if not self._ask_consent():
                self.destroy()
                sys.exit(0)
            self.cfg["consented"] = True
            self.cfg.save()

        self.deiconify()
        self._build_ui()
        self.bind("<Configure>", self._on_configure)
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        atexit.register(self._restore_all_taskbars)

        if self._claude_ok and self.cfg["consented"]:
            _ensure_hooks()
        start_enter_watcher(lambda: self._cards)

        if not self.cfg.ready():
            self.after(200, self._setup)

    def _ask_consent(self):
        return messagebox.askokcancel(
            "Claude Dock — First-run setup",
            "Claude Dock will register two hooks in your Claude Code config "
            "(~/.claude/settings.json):\n\n"
            "  • Stop       — marks a session idle\n"
            "  • PreToolUse — marks a session working\n\n"
            "Both hooks run this app's binary with --hook, which touches "
            "empty marker files under ~/.claude-dock/sessions/. Nothing "
            "else is read, written, or sent anywhere.\n\n"
            "No network, no analytics, no telemetry.\n\n"
            "Continue?",
            icon=messagebox.QUESTION,
        )

    def _set_window_icon(self):
        try:
            # iconphoto works on all three OSes with in-memory PNG data,
            # so no filesystem lookup is needed at runtime.
            self._icon_img = tk.PhotoImage(data=_ANCHOR_PNG_B64)
            self.iconphoto(True, self._icon_img)
        except Exception:
            pass  # icon is cosmetic

    def _place(self):
        sw = self.winfo_screenwidth()
        x  = self.cfg["x"] or (sw - (self.cfg["width"] or 240) - 20)
        y  = self.cfg["y"] or 100
        w  = self.cfg["width"] or 240
        h  = self.cfg["height"] or 56
        self.geometry(f"{w}x{h}+{x}+{y}")
        self.minsize(self.MIN_W, 56)

    def _on_configure(self, event):
        if event.widget is not self:
            return
        if self._geo_after:
            self.after_cancel(self._geo_after)
        self._geo_after = self.after(400, self._save_geometry)

    def _save_geometry(self):
        self.cfg["x"]      = self.winfo_x()
        self.cfg["y"]      = self.winfo_y()
        self.cfg["width"]  = self.winfo_width()
        self.cfg["height"] = self.winfo_height()
        self.cfg.save()

    def _build_ui(self):
        hdr = tk.Frame(self, bg=C["base"], height=36)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)

        title_lbl = tk.Label(hdr, text="Claude Sessions", fg=C["text"],
                              bg=C["base"], font=(_FONT, 9, "bold"),
                              cursor="fleur")
        title_lbl.pack(side=tk.LEFT, padx=10)
        self._make_draggable(title_lbl)

        gear = tk.Label(hdr, text="⚙", fg=C["dim"], bg=C["surface"],
                         font=(_FONT, 9), cursor="hand2", padx=5)
        gear.pack(side=tk.RIGHT, padx=(0, 6), pady=6)
        gear.bind("<Button-1>", lambda e: self._setup())

        plus = tk.Label(hdr, text=" + ", fg=C["base"], bg=C["blue"],
                         font=(_FONT, 11, "bold"), cursor="hand2", padx=4)
        plus.pack(side=tk.RIGHT, padx=(0, 4), pady=6)
        plus.bind("<Button-1>", lambda e: self._new())

        self._body = tk.Frame(self, bg=C["bg"])
        self._body.pack(fill=tk.BOTH, expand=True)

        if not self._claude_ok:
            empty_text = "Claude Code not found.\nInstall it, then restart the dock."
            empty_fg = C["amber"]
        elif not _available_terminals():
            empty_text = "No supported terminal detected."
            empty_fg = C["amber"]
        else:
            empty_text = "Click + to start a session"
            empty_fg = C["muted"]

        self._empty = tk.Label(self._body, text=empty_text,
                                fg=empty_fg, bg=C["bg"],
                                font=(_FONT, 8), pady=12, justify="center")
        self._empty.pack()

    def _make_draggable(self, w):
        state = {}
        def start(e):
            state["ox"] = e.x_root - self.winfo_x()
            state["oy"] = e.y_root - self.winfo_y()
        def drag(e):
            self.geometry(f"+{e.x_root - state['ox']}+{e.y_root - state['oy']}")
        def stop(e):
            self.cfg["x"] = self.winfo_x()
            self.cfg["y"] = self.winfo_y()
            self.cfg.save()
        w.bind("<Button-1>", start)
        w.bind("<B1-Motion>", drag)
        w.bind("<ButtonRelease-1>", stop)

    def _new(self):
        if not self.cfg.ready():
            self._setup()
            return

        if self._empty.winfo_ismapped():
            self._empty.pack_forget()

        s = Session(self.cfg)
        s.on_idle(lambda _s:     _toast("Claude finished", f'"{_s.label[:40]}" is ready'))
        s.on_complete(lambda _s: _toast("Session closed",  f'"{_s.label[:40]}" terminal closed'))
        s.launch()

        card = Card(self._body, s, self._dismiss)
        card.pack(fill=tk.X)
        self._cards.append(card)
        self._fit()

    def _dismiss(self, card: Card):
        if card._s.status != "done":
            card._s.kill()
        card._s.cleanup()
        card.destroy()
        self._cards = [c for c in self._cards if c.winfo_exists()]
        if not self._cards:
            self._empty.pack()
        self._fit()

    def _setup(self):
        SetupDlg(self, self.cfg)

    def _fit(self):
        self.update_idletasks()
        min_h = max(self.winfo_reqheight(), 56)
        self.minsize(self.MIN_W, min_h)
        if self.winfo_height() < min_h:
            self.geometry(f"{self.winfo_width()}x{min_h}")

    def _restore_all_taskbars(self):
        """Re-add live sessions' terminals to the taskbar. Idempotent and
        safe to call during interpreter shutdown."""
        for card in getattr(self, "_cards", []):
            try:
                if card._s.status != "done":
                    card._s.restore_to_taskbar()
            except Exception:
                pass

    def _on_close(self):
        """Restore taskbar entries for any live sessions so terminals
        aren't orphaned off-screen when the dock goes away."""
        self._restore_all_taskbars()
        self.destroy()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        flag = sys.argv[1]
        if flag == "--hook":
            action = sys.argv[2] if len(sys.argv) > 2 else "stop"
            _run_hook(action)
            sys.exit(0)
        if flag in ("--uninstall", "-u"):
            _uninstall()
            sys.exit(0)
        if flag in ("--version", "-v"):
            print(f"Claude Dock {__version__}")
            sys.exit(0)
        if flag in ("--help", "-h"):
            print(
                f"Claude Dock {__version__}\n\n"
                "Usage: claude-dock [OPTIONS]\n\n"
                "  (no args)     Launch the dock\n"
                "  --hook ACT    Internal: fire a Claude Code hook\n"
                "  --uninstall   Remove hooks + ~/.claude-dock/\n"
                "  --version     Print version and exit\n"
                "  --help        Show this message\n"
            )
            sys.exit(0)
    Dock().mainloop()
