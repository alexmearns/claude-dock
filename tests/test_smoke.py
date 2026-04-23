"""Smoke tests that don't require a display."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class SmokeTests(unittest.TestCase):
    def test_module_imports(self):
        """dock.py must import without side effects."""
        subprocess.check_call(
            [sys.executable, "-c", "import dock"],
            cwd=ROOT,
        )

    def test_version_flag(self):
        out = subprocess.check_output(
            [sys.executable, "dock.py", "--version"],
            cwd=ROOT,
            text=True,
        )
        self.assertIn("Claude Dock", out)

    def test_hook_stop_creates_idle_marker(self):
        with tempfile.TemporaryDirectory() as home:
            env = {**os.environ,
                   "HOME": home,
                   "USERPROFILE": home,
                   "CLAUDE_DOCK_SESSION_ID": "abc12345"}
            subprocess.check_call(
                [sys.executable, "dock.py", "--hook", "stop"],
                cwd=ROOT,
                env=env,
            )
            marker = Path(home) / ".claude-dock" / "sessions" / "abc12345.idle"
            self.assertTrue(marker.exists(), f"{marker} was not created")

    def test_hook_tool_creates_running_marker(self):
        with tempfile.TemporaryDirectory() as home:
            env = {**os.environ,
                   "HOME": home,
                   "USERPROFILE": home,
                   "CLAUDE_DOCK_SESSION_ID": "abc12345"}
            subprocess.check_call(
                [sys.executable, "dock.py", "--hook", "tool"],
                cwd=ROOT,
                env=env,
            )
            marker = Path(home) / ".claude-dock" / "sessions" / "abc12345.running"
            self.assertTrue(marker.exists())

    def test_hook_rejects_bad_session_id(self):
        """Path-traversal attempt must not create files outside sessions dir."""
        with tempfile.TemporaryDirectory() as home:
            env = {**os.environ,
                   "HOME": home,
                   "USERPROFILE": home,
                   "CLAUDE_DOCK_SESSION_ID": "../evil"}
            subprocess.check_call(
                [sys.executable, "dock.py", "--hook", "stop"],
                cwd=ROOT,
                env=env,
            )
            evil = Path(home) / "evil.idle"
            self.assertFalse(evil.exists())

    def test_uninstall_is_idempotent(self):
        with tempfile.TemporaryDirectory() as home:
            env = {**os.environ, "HOME": home, "USERPROFILE": home}
            # settings.json with our hook plus an unrelated one
            claude_dir = Path(home) / ".claude"
            claude_dir.mkdir()
            our_cmd = '"/some/path/claude-dock" --hook stop'
            other_cmd = 'echo unrelated'
            (claude_dir / "settings.json").write_text(json.dumps({
                "hooks": {
                    "Stop": [
                        {"matcher": "", "hooks": [{"type": "command", "command": our_cmd}]},
                        {"matcher": "", "hooks": [{"type": "command", "command": other_cmd}]},
                    ]
                }
            }))
            subprocess.check_call(
                [sys.executable, "dock.py", "--uninstall"],
                cwd=ROOT,
                env=env,
            )
            settings = json.loads((claude_dir / "settings.json").read_text())
            # Our hook gone, unrelated hook kept
            commands = [
                h["command"]
                for entry in settings.get("hooks", {}).get("Stop", [])
                for h in entry.get("hooks", [])
            ]
            self.assertIn(other_cmd, commands)
            self.assertNotIn(our_cmd, commands)


if __name__ == "__main__":
    unittest.main()
