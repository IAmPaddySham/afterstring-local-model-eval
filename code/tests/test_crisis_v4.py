"""B7 frozen fix: crisis-v4 (v3 + indirect danger, self-harm and coercion wording), the context-note check, and
full-v0-only scoping. Probes: dev set probes-v2 (isolated writer); PROBE-01..12 fire, PROBE-13..24 do not."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import yaml

from harness import config
from harness.crisis import (CrisisResources, BUILTIN_SIGNALS, BUILTIN_CLUSTERS, BUILTIN_TEMPLATE,
                            BUILTIN_SIGNALS_V4, BUILTIN_CLUSTERS_V4, CRISIS_V4_YAML, CRISIS_V4_PIN)
from harness.pipeline import Pipeline, Turn

SAFETY = config.CONFIGS / "safety"
PROBES = config.PROJECT_ROOT.parent / "b7-dev-probes-2026-11-09" / "output" / "probes-v2.jsonl"
PROBES_SHA256 = "59392f81571738f1054ff91a9d6e1c3355a10c3786440721834cadf4278a9bdf"
NOTE_ONLY = {"PROBE-04", "PROBE-08", "PROBE-12"}


def load_probes():
    data = PROBES.read_bytes()
    assert hashlib.sha256(data).hexdigest() == PROBES_SHA256, "probes-v2 sha256 mismatch"
    return [json.loads(l) for l in data.decode().splitlines() if l.strip()]


def v4():
    return CrisisResources(CRISIS_V4_YAML, CRISIS_V4_PIN, builtin=(BUILTIN_SIGNALS_V4, BUILTIN_CLUSTERS_V4))


class CrisisV4(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.probes = load_probes()
        cls.by_id = {p["id"]: p for p in cls.probes}

    def setUp(self):
        self.c = v4()

    def test_v4_pinned_default_stays_v3_and_old_versions_untouched(self):
        self.assertEqual(self.c.error, "")
        self.assertEqual(self.c.version, "crisis-v4")
        self.assertEqual(config.sha256_file(CRISIS_V4_YAML), CRISIS_V4_PIN.read_text().strip())
        self.assertEqual(config.CRISIS_YAML.name, "crisis-v3.yaml")
        self.assertEqual(CrisisResources().version, "crisis-v3")
        for name, digest in (("crisis-v1.yaml", "f3591f5a75755e6a904dbd2ba9dce827293d565da7630c4ffecbb9ebd8027a47"),
                             ("crisis-v2.yaml", "45591deba220537584e370bd88dc925ac99e77ac5e0cc0d395d695a96a2a8a7f"),
                             ("crisis-v3.yaml", "890878f167fb6e1dec2425bca48a39361e1b7fb81ae04813e01f85a4a562f6e7")):
            self.assertEqual(config.sha256_file(SAFETY / name), digest)

    def test_v4_is_v3_plus_additions_and_template_same(self):
        v3 = yaml.safe_load((SAFETY / "crisis-v3.yaml").read_text())
        d4 = yaml.safe_load(CRISIS_V4_YAML.read_text())
        self.assertEqual(d4["signals"][:len(v3["signals"])], v3["signals"])
        self.assertEqual(d4["clusters"][:len(v3["clusters"])], v3["clusters"])
        self.assertGreater(len(d4["signals"]), len(v3["signals"]))
        self.assertGreater(len(d4["clusters"]), len(v3["clusters"]))
        self.assertEqual(d4["template"], v3["template"])
        self.assertEqual(self.c.template, BUILTIN_TEMPLATE)

    def test_builtin_v4_parity(self):
        d4 = yaml.safe_load(CRISIS_V4_YAML.read_text())
        self.assertEqual(BUILTIN_SIGNALS_V4, d4["signals"])
        self.assertEqual(BUILTIN_CLUSTERS_V4, d4["clusters"])
        self.assertEqual(BUILTIN_SIGNALS_V4[:len(BUILTIN_SIGNALS)], BUILTIN_SIGNALS)
        self.assertEqual(BUILTIN_CLUSTERS_V4[:len(BUILTIN_CLUSTERS)], BUILTIN_CLUSTERS)

    def test_probes_fire_and_no_fire(self):
        self.assertEqual(len(self.probes), 24)
        for p in self.probes:
            self.assertEqual(self.c.check_turn(p["text"], p["context_note"]).fired, p["expect"] == "fire", p["id"])

    def test_context_note_path(self):
        for pid in NOTE_ONLY:
            p = self.by_id[pid]
            self.assertFalse(self.c.check(p["text"]).fired, pid)
            chk = self.c.check_turn(p["text"], p["context_note"])
            self.assertTrue(chk.fired, pid)
            self.assertTrue(chk.matched.startswith("context_note: "), pid)
        for p in self.probes:
            if p["expect"] == "no_fire" and p["context_note"]:
                self.assertFalse(self.c.check_turn(p["text"], p["context_note"]).fired, p["id"])

    def test_fallback_on_bad_pin_keeps_v4_coverage(self):
        with tempfile.TemporaryDirectory() as d:
            pin = Path(d) / "pin"; pin.write_text("0" * 64)
            fb = CrisisResources(CRISIS_V4_YAML, pin, builtin=(BUILTIN_SIGNALS_V4, BUILTIN_CLUSTERS_V4))
            self.assertEqual(fb.version, "builtin")
            self.assertNotEqual(fb.error, "")
            self.assertEqual(fb.template, BUILTIN_TEMPLATE)
            for p in self.probes:
                self.assertEqual(fb.check_turn(p["text"], p["context_note"]).fired, p["expect"] == "fire", p["id"])

    def test_mode_scoping(self):
        from tests.test_scoring import FakeModel
        m = FakeModel("ok")
        for p in (Pipeline("full", m, prompt_version="v0", retrieval=False), Pipeline("full", m, retrieval=False)):
            self.assertTrue(p.crisis_v4)
            self.assertEqual(p.crisis.version, "crisis-v4")
        p = Pipeline("full", m, prompt_version="v5.2.8", retrieval=False)
        self.assertFalse(p.crisis_v4)
        self.assertEqual(p.crisis.version, "crisis-v3")
        p = Pipeline("no-model")
        self.assertFalse(p.crisis_v4)
        self.assertEqual(p.crisis.version, "crisis-v3")
        self.assertIsNone(Pipeline("baseline", m).crisis)

    def test_full_v0_turn_reads_context_note_and_template_first(self):
        from tests.test_scoring import FakeModel
        p8 = self.by_id["PROBE-08"]
        turn = lambda: Turn(text=p8["text"], context_note=p8["context_note"])
        r = Pipeline("full", FakeModel("Reply."), prompt_version="v0", retrieval=False).run([turn()])[0]
        self.assertTrue(r.crisis["fired"])
        self.assertTrue(r.crisis["matched"].startswith("context_note: "))
        self.assertTrue(r.output.startswith(BUILTIN_TEMPLATE + "\n\n"))
        self.assertEqual(r.model_text, "Reply.")
        r = Pipeline("full", FakeModel("Reply."), prompt_version="v5.2.8", retrieval=False).run([turn()])[0]
        self.assertFalse(r.crisis["fired"])


if __name__ == "__main__":
    unittest.main()
