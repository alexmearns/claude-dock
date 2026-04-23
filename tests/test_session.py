"""Lifecycle tests: drive Session's state machine without launching a real terminal."""
import os
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _fresh_dock(home):
    """Re-import dock.py so CONFIG_DIR/SESSIONS_DIR resolve under a temp HOME."""
    os.environ["HOME"] = str(home)
    os.environ["USERPROFILE"] = str(home)
    if "dock" in sys.modules:
        del sys.modules["dock"]
    import dock
    return dock


def _wait_until(predicate, timeout=3.0, step=0.05):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if predicate():
            return True
        time.sleep(step)
    return False


class SessionLifecycleTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._home = Path(self._tmp.name)
        self.dock = _fresh_dock(self._home)

    def tearDown(self):
        self._tmp.cleanup()

    def _spawn_watched_session(self):
        cfg = self.dock.Config()
        session = self.dock.Session(cfg)
        watcher = threading.Thread(target=session._watch, daemon=True)
        watcher.start()
        return session, watcher

    def test_new_session_starts_running(self):
        session, _ = self._spawn_watched_session()
        self.assertEqual(session.status, "running")

    def test_idle_marker_flips_status_to_idle(self):
        session, _ = self._spawn_watched_session()
        Path(session._idle).touch()
        self.assertTrue(
            _wait_until(lambda: session.status == "idle"),
            f"status stayed {session.status!r}",
        )

    def test_running_marker_after_idle_flips_back(self):
        session, _ = self._spawn_watched_session()
        Path(session._idle).touch()
        self.assertTrue(_wait_until(lambda: session.status == "idle"))
        Path(session._running).touch()
        self.assertTrue(_wait_until(lambda: session.status == "running"))

    def test_done_marker_ends_watch_and_fires_callback(self):
        session, watcher = self._spawn_watched_session()
        seen = []
        session.on_complete(lambda s: seen.append(s.id))
        Path(session._done).touch()
        watcher.join(timeout=2)
        self.assertEqual(session.status, "done")
        self.assertEqual(seen, [session.id])

    def test_kill_triggers_done_transition(self):
        session, watcher = self._spawn_watched_session()
        session.kill()
        watcher.join(timeout=2)
        self.assertEqual(session.status, "done")

    def test_cleanup_removes_all_markers(self):
        session, _ = self._spawn_watched_session()
        for ext in (".idle", ".running", ".done"):
            (Path(self.dock.SESSIONS_DIR) / f"{session.id}{ext}").touch()
        session.cleanup()
        leftovers = list(Path(self.dock.SESSIONS_DIR).glob(f"{session.id}.*"))
        self.assertEqual(leftovers, [])

    def test_elapsed_grows_after_start(self):
        session, _ = self._spawn_watched_session()
        first = session.elapsed()
        time.sleep(1.1)
        self.assertNotEqual(first, session.elapsed())


if __name__ == "__main__":
    unittest.main()
