# claude-dock

A floating status panel for [Claude Code](https://claude.com/claude-code) sessions. Shows what each session is doing (working, waiting, done), surfaces terminal titles as live labels, and lets you focus or hide terminals from one tray-like window.

## Download

Grab the binary for your OS from the [Releases page](https://github.com/alexmearns/claude-dock/releases):

- **Windows** — `Claude Dock.exe`
- **macOS** — `claude-dock-macos.zip` (unzip, drag `Claude Dock.app` to Applications)
- **Linux** — `claude-dock` (`chmod +x claude-dock && ./claude-dock`)

First launch shows a one-time consent dialog explaining what will be written to your Claude Code config.

### First-run warnings (unsigned binaries)

The binaries aren't code-signed, so:

- **Windows** — SmartScreen will say "Windows protected your PC." Click *More info* → *Run anyway*.
- **macOS** — Gatekeeper will block it. Right-click → *Open* → *Open* on first launch.
- **Linux** — No warning, just `chmod +x` and run.

## What this does to your machine

Transparency about every filesystem write the app performs:

| Where | What | When |
|---|---|---|
| `~/.claude-dock/config.json` | Your preferences (window position, terminal choice, folder) | Saved on dock move/resize or setup save |
| `~/.claude-dock/sessions/*.idle` | Empty marker file, signals a session went idle | Written by Claude Code Stop hook |
| `~/.claude-dock/sessions/*.running` | Empty marker file, signals a session is working | Written by Claude Code PreToolUse hook |
| `~/.claude-dock/sessions/*.{bat,ps1,sh}` | Launcher script for each terminal session | Written when you click + in the dock |
| `~/.claude/settings.json` | Two hook entries: Stop + PreToolUse, both invoking this binary with `--hook` | Written on first-launch consent, re-verified on every launch |

That's it. Nothing else is touched.

## Privacy

- **No network calls.** The app never contacts a server.
- **No analytics, no telemetry, no crash reporting.** None.
- **No keylogging.** On Windows, the app polls `GetAsyncKeyState` for the Enter key only, at ~20Hz, to detect when you send a message in a dock-owned terminal. It doesn't read key contents or inspect other windows. The source is ~20 lines — see `start_enter_watcher` in `dock.py`.
- **No hidden processes.** The only running process is the dock window itself, plus the terminal processes you explicitly start via the + button.
- **All config lives under `~/.claude-dock/` or `~/.claude/settings.json`.** You can read it, edit it, or delete it at any time.

If you don't trust the binary, build it yourself — see below.

## Uninstall

**From inside the app:** click the ⚙ gear, then the **Uninstall** button. Confirm, and the hooks + preferences are cleaned up.

**From a terminal:**

```
claude-dock --uninstall
```

Either path removes the hook entries from `~/.claude/settings.json` and deletes `~/.claude-dock/`. Then delete the binary itself.

## Build from source

Requires Python 3.10+ with tkinter. On Linux: `sudo apt-get install python3-tk`.

```
python build.py
```

Produces `Claude Dock.exe` / `Claude Dock.app` / `claude-dock` alongside the source.

## How it works

- On first launch (after consent), two hooks are registered in `~/.claude/settings.json`: `Stop` fires when Claude Code finishes responding, `PreToolUse` fires whenever Claude Code is about to invoke a tool. Both run this same binary with `--hook`, which short-circuits to a file-touch instead of launching the GUI. No Python is required on target machines.
- Each session card corresponds to a terminal window spawned by the dock. State is communicated via marker files (`.idle`, `.running`, `.done`) in `~/.claude-dock/sessions/`.
- Window detection and taskbar hiding use per-OS APIs: Win32 on Windows, AppleScript on macOS, and basic terminal-emulator spawning on Linux.

## License

MIT — see [LICENSE](LICENSE).
