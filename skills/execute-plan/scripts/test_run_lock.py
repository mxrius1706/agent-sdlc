"""Tests fuer run-lock.py: Lock je Lauf, Aufruf als Unterprozess, synthetische Ordner."""
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "run-lock.py")


def dead_pid():
    proc = subprocess.Popen([sys.executable, "-I", "-c", "pass"])
    proc.wait()
    return proc.pid


class TestRunLock(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.lock = os.path.join(self.tmp.name, "run", "phase-2.lock")

    def lock_cmd(self, action, pid=None):
        cmd = [sys.executable, "-I", SCRIPT, action, self.lock]
        if pid is not None:
            cmd += ["--pid", str(pid)]
        return subprocess.run(cmd, capture_output=True, text=True)

    def test_first_acquire_succeeds(self):
        proc = self.lock_cmd("acquire", os.getpid())
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue(os.path.exists(self.lock))

    def test_second_acquire_refused(self):
        self.assertEqual(self.lock_cmd("acquire", os.getpid()).returncode, 0)
        proc = self.lock_cmd("acquire", os.getpid())
        self.assertEqual(proc.returncode, 1)
        self.assertTrue(proc.stdout + proc.stderr)

    def test_release_cleans_up_and_allows_new_acquire(self):
        self.lock_cmd("acquire", os.getpid())
        self.assertEqual(self.lock_cmd("release").returncode, 0)
        self.assertFalse(os.path.exists(self.lock))
        self.assertEqual(self.lock_cmd("acquire", os.getpid()).returncode, 0)

    def test_release_without_lock_is_harmless(self):
        self.assertEqual(self.lock_cmd("release").returncode, 0)

    def test_stale_lock_with_dead_process_is_detected(self):
        self.assertEqual(self.lock_cmd("acquire", dead_pid()).returncode, 0)
        proc = self.lock_cmd("acquire", os.getpid())
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("veraltet", proc.stdout + proc.stderr)

    def test_live_holder_is_not_stale(self):
        self.lock_cmd("acquire", os.getpid())
        proc = self.lock_cmd("acquire", os.getpid())
        self.assertEqual(proc.returncode, 1)
        self.assertNotIn("veraltet", proc.stdout + proc.stderr)


class TestRunLockShortLivedParent(unittest.TestCase):
    """Ohne --pid darf der Halter nicht die Kurzzeit-Shell eines Bash-Aufrufs sein."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.lock = os.path.join(self.tmp.name, "run", "phase-2.lock")

    def shell_acquire(self):
        # Zwei Befehle im bash -c: die Shell bleibt Elternprozess und stirbt danach.
        cmd = "%s -I %s acquire %s; rc=$?; true; exit $rc" % (sys.executable, SCRIPT, self.lock)
        return subprocess.run(["bash", "-c", cmd], capture_output=True, text=True)

    def test_second_start_refused_after_short_lived_shell(self):
        first = self.shell_acquire()
        self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
        second = self.shell_acquire()
        self.assertEqual(second.returncode, 1, second.stdout + second.stderr)
        self.assertNotIn("veraltet", second.stdout + second.stderr)


if __name__ == "__main__":
    unittest.main()
