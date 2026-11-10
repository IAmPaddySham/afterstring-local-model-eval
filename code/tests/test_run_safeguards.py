"""D-022: dirty-tree refusal, dirty-state capture, gate_cli exit code, pinned requirements."""
import os, re, tempfile, unittest
from pathlib import Path
from harness import config
from harness.gate_adapter import GateRb, HOLD
from evals import run as runmod


class DirtyTreeTests(unittest.TestCase):
    def test_run_folders_alone_are_not_dirty(self):
        self.assertEqual(runmod.code_changes("?? runs/20261027-070000-full/\n"), [])

    def test_code_change_is_dirty(self):
        ch = runmod.code_changes(" M harness/optics.py\n?? runs/x/\n?? configs/prompts/new.txt\n")
        self.assertEqual(ch, [" M harness/optics.py", "?? configs/prompts/new.txt"])

    def test_refuses_dirty_without_flag(self):
        git = {"commit": "abc", "dirty": True, "changes": [" M harness/optics.py"]}
        self.assertIn("refusing to run", runmod.check_tree(git, allow_dirty=False))
        self.assertIsNone(runmod.check_tree(git, allow_dirty=True))
        self.assertIsNone(runmod.check_tree({"commit": "abc", "dirty": False, "changes": []}, False))

    def test_git_info_records_head(self):
        g = runmod.git_info()
        self.assertRegex(g["commit"], r"^[0-9a-f]{40}$")
        self.assertIn("dirty", g); self.assertIn("changes", g); self.assertTrue(g["head"])

    def test_save_dirty_state_writes_files(self):
        d = Path(tempfile.mkdtemp())
        runmod.save_dirty_state(d, {"changes": [" M harness/optics.py"]})
        self.assertTrue((d / "git-diff.patch").exists())
        self.assertTrue((d / "git-untracked.txt").exists())


class GateExitCodeTests(unittest.TestCase):
    def test_nonzero_exit_is_hold_even_if_it_printed_proceed(self):
        if not os.path.exists("/usr/bin/ruby"):
            self.skipTest("no /usr/bin/ruby")
        with tempfile.NamedTemporaryFile("w", suffix=".rb", delete=False) as f:
            f.write('puts "PROCEED"\nexit 3\n')
        try:
            word, raw, _ = GateRb(cli=f.name, root=tempfile.gettempdir()).ask("payment", 3, True)
            self.assertEqual(word, HOLD)
            self.assertTrue(raw.startswith("EXIT_MISMATCH(exit 3)"), raw)
        finally:
            os.unlink(f.name)


    def test_crash_without_output_is_hold(self):
        if not os.path.exists("/usr/bin/ruby"):
            self.skipTest("no /usr/bin/ruby")
        with tempfile.NamedTemporaryFile("w", suffix=".rb", delete=False) as f:
            f.write('raise "boom"\n')
        try:
            word, _, _ = GateRb(cli=f.name, root=tempfile.gettempdir()).ask("payment", 3, True)
            self.assertEqual(word, HOLD)
        finally:
            os.unlink(f.name)


class RequirementsLockTests(unittest.TestCase):
    def test_lock_pins_exact_versions(self):
        lines = [l for l in (config.PROJECT_ROOT / "requirements.lock").read_text().splitlines()
                 if l.strip() and not l.startswith("#")]
        self.assertTrue(lines)
        for l in lines:
            self.assertRegex(l, r"^[A-Za-z0-9_.\-\[\]]+==[^=\s]+$", l)
        names = {l.split("==")[0].lower() for l in lines}
        self.assertTrue({"mlx", "mlx-lm", "pyyaml", "numpy"} <= names)


if __name__ == "__main__":
    unittest.main()
