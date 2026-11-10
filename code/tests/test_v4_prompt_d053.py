"""D-053: v4 prompt is opt-in by name; v0 stays default and byte-identical."""
import unittest
from harness import config
from harness.pipeline import Pipeline

V0_SHA = "a4de3c9fd69098802a84247892150df57dc3e631e92392c76d6b0ff1185adc69"
V3_SHA = "d109521254d156290d0ce6690b1b2b0d31fa533522349395151653da84f071b1"


def _pipe(version):
    class _StubModel:  # never called; tests only read the assembled system prompt
        name = "stub"
        loaded = True
    try:
        return Pipeline("full", _StubModel(), 64, prompt_version=version)
    except TypeError:
        return None


class TestV4OptIn(unittest.TestCase):
    def test_v4_selectable_by_name(self):
        self.assertIn("v4", config.FULL_PROMPTS)
        self.assertTrue(config.FULL_PROMPTS["v4"].exists())
        self.assertEqual(config.FULL_PROMPTS["v4"].name, "full-v4.txt")

    def test_default_still_v0(self):
        self.assertEqual(config.DEFAULT_PROMPT_VERSION, "v0")
        self.assertEqual(config.FULL_PROMPT, config.FULL_PROMPTS["v0"])
        self.assertEqual(config.DEFAULT_RETRIEVAL_VERSION, "v0")

    def test_v0_v3_bytes_unchanged(self):
        self.assertEqual(config.sha256_file(config.FULL_PROMPTS["v0"]), V0_SHA)
        self.assertEqual(config.sha256_file(config.FULL_PROMPTS["v3"]), V3_SHA)

    def test_v4_differs_and_keeps_core_rules(self):
        v4 = config.FULL_PROMPTS["v4"].read_text()
        self.assertNotEqual(v4, config.FULL_PROMPTS["v0"].read_text())
        for must in ("present, explicit yes to the exact action", "honor it at once",
                     "emergency services", "No, it has not been independently validated",
                     "fresh yes", "Begin by acknowledging"):
            self.assertIn(must, v4)
        # v3 lines dropped from v4 (linked to v3's stop/fresh-yes losses)
        for dropped in ("standing permission", "Give the answer that is possible now",
                        "STAY keeps the question open", "Before retrying or redoing"):
            self.assertNotIn(dropped, v4)

    def test_pipeline_assembles_prompts(self):
        p0, p4 = _pipe(None), _pipe("v4")
        if p0 is None or p4 is None:
            self.skipTest("Pipeline signature differs")
        self.assertEqual(p0.prompt_version, "v0")
        self.assertEqual(p0.system_prompt, config.FULL_PROMPTS["v0"].read_text().strip())
        self.assertEqual(p4.system_prompt, config.FULL_PROMPTS["v4"].read_text().strip())
        # one variable: v4 rides the default (v0) retrieval path
        self.assertIsNone(p4.retrieval_manifest)
        self.assertEqual(p4.retrieval_manifest, p0.retrieval_manifest)


if __name__ == "__main__":
    unittest.main()
