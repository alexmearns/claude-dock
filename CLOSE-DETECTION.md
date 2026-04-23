# Session Close Detection — Original Five-Mechanism Approach

Documented before switching to poll()-only. Revert here if the simpler approach
proves unreliable.

## Why it was complex

When a Windows terminal (cmd.exe, PowerShell, etc.) is launched with
`CREATE_NEW_CONSOLE`, the dock holds a `subprocess.Popen` handle to the shell
process. Closing the console window should kill the process and make `poll()`
return non-None — but in practice this was not always caught fast enough, or
not caught at all, depending on console host configuration (classic conhost.exe
vs Windows Terminal). Five mechanisms were added incrementally to cover the
failure modes.

## The five mechanisms

### 1 & 2 — Marker files: `.running` and `.idle`

Not close-detection. These signal Claude Code's activity state via the Stop and
PreToolUse hooks. Kept in the simplified version.

### 3 — `.done` file

Written by the shell command appended to the session launch string:

```
cmd:        & type nul > "{done}"
powershell: New-Item -Path "{done}" -Force | Out-Null
bash/wsl:   touch "{done}"
```

Fires when the user exits the shell cleanly after `claude` finishes. Reliable for
normal exits; does not fire if the window is closed while `claude` is still running.

### 4 — `poll()` on `self._proc`

`watchable = self._proc if IS_WIN else None` — on Mac/Linux `self._proc` is the
osascript/terminal launcher which exits immediately, so it was excluded.

On Windows, `self._proc` is cmd.exe/powershell.exe directly. When the console
window is closed, Windows sends CTRL_CLOSE_EVENT to the process group, which
should terminate the shell and unblock `poll()`. This is the mechanism the
simplified version bets on being sufficient.

### 5 — `IsWindow()` (Win32 API)

```python
if IS_WIN and self._hwnd and not _u32.IsWindow(self._hwnd):
    break
```

Catches window destruction events (title-bar X, Alt+F4, taskbar thumbnail X)
faster than `poll()` can catch process termination. Requires `self._hwnd` to
have been captured by `_capture_hwnd` — if that thread missed the window, this
check is a no-op.

### 6 — Title-based window scan (belt-and-suspenders)

```python
if IS_WIN and time.time() - last_scan > 0.5:
    last_scan = time.time()
    found = _find_hwnd_by_title(self._title)
    if found:
        saw_window = True
        if self._hwnd is None:
            self._hwnd = found   # hwnd fallback if _capture_hwnd missed it
    elif saw_window:
        break
```

Polls `EnumWindows` every 500ms looking for a window whose title contains the
session ID string (`Claude-{id}`). Once it has seen the window and then stops
seeing it, the session is considered closed. Also served as a fallback hwnd
assignment if `_capture_hwnd` hit its 15-second deadline without finding the
window.

## What the simplified version relies on

`_watch()` after the change uses only mechanisms 3 and 4:

- `.done` file for clean exits
- `self._proc is not None and self._proc.poll() is not None` for all other closes

`self._proc` is `None` on Mac/Linux (never assigned in those launch branches),
so the poll check is a no-op there — Mac/Linux remain file-signal-only, same
behaviour as before.

## Known risk

If Windows does not propagate CTRL_CLOSE_EVENT to the shell process promptly (or
at all, in unusual console host configurations), `poll()` will not fire and the
dock card will hang open until the dock is restarted. The original `IsWindow()`
check (mechanism 5) was the safety net for this case.

If this is observed in testing, restore mechanisms 5 and 6 from this document.
