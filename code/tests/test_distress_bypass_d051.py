"""D-051: distress/safety turns bypass retrieval on v1 and v2; v0 unchanged. Uses batch-1 practice items only."""
import unittest

from harness import config
from harness.retrieval import Retriever, DISTRESS, DOMAIN
from evals.items import parse
from evals.run import model_turns

PRACTICE = config.PROJECT_ROOT / "evals" / "practice" / "2026-10-26-manual-nine.md"
MIXED = "I don't feel safe right now. What does the governor do?"   # distress + a v0 DOMAIN term
DISTRESS_TURNS = ["I don't feel safe right now.", "I'm not safe at home.", "I am in danger.", "I feel suicidal.",
                  "I want to hurt myself.", "I want to die.", "I've been thinking about self-harm.",
                  "I'm having a panic attack.", "This is a crisis.", "My partner hits me.", "He threatened me.",
                  "My boyfriend is abusive.", "I'm scared for my life.", "It's an emergency.",
                  "I want to end my life.", "I took an overdose."]
PLAIN_TURNS = ["Give me 20 dinner ideas.", "Did my payment go through?", "What decisions can the governor return?",
               "Is Afterstring scientifically proven?", "Love doesn't take shortcuts. What does that mean to you?",
               "Is this a safe way to store my passwords?", "The game ended in a draw."]


def practice_turns():
    out = {}
    for it in parse(PRACTICE):
        turns, _, _ = model_turns(it)
        out[it["id"]] = turns[0].text
    return out


class DistressBypassTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.v0 = Retriever()
        cls.v1 = Retriever(str(config.RETRIEVAL_MANIFESTS["v1"]))
        cls.v2 = Retriever(str(config.RETRIEVAL_MANIFESTS["v2"]))
        cls.p = practice_turns()

    def test_flags_per_version(self):
        self.assertEqual((self.v0.distress_bypass, self.v1.distress_bypass, self.v2.distress_bypass),
                         (False, True, True))

    def test_detector_matches_distress_language(self):
        for t in DISTRESS_TURNS:
            self.assertTrue(DISTRESS.search(t), t)

    def test_detector_leaves_plain_turns(self):
        for t in PLAIN_TURNS:
            self.assertFalse(DISTRESS.search(t), t)

    def test_p7_bypasses_v1_and_v2(self):
        p7 = self.p["PRACTICE-P7"]
        self.assertIn("feel safe", p7)
        self.assertFalse(self.v1.applies(p7))
        self.assertFalse(self.v2.applies(p7))

    def test_only_p7_is_distress_in_batch1(self):
        self.assertEqual([k for k, t in self.p.items() if DISTRESS.search(t)], ["PRACTICE-P7"])

    def test_non_distress_practice_turns_follow_their_version(self):
        for k, t in self.p.items():
            if k == "PRACTICE-P7":
                continue
            self.assertTrue(self.v2.applies(t), k)                         # v2 gate "always"
            self.assertEqual(self.v1.applies(t), bool(DOMAIN.search(t)), k)  # v1 keyword gate
            self.assertEqual(self.v0.applies(t), bool(DOMAIN.search(t)), k)

    def test_mixed_turn(self):
        self.assertTrue(self.v0.applies(MIXED))     # v0 unchanged: DOMAIN still decides
        self.assertFalse(self.v1.applies(MIXED))
        self.assertFalse(self.v2.applies(MIXED))

    def test_v0_ignores_distress(self):
        for t in DISTRESS_TURNS + PLAIN_TURNS:
            self.assertEqual(self.v0.applies(t), bool(DOMAIN.search(t)), t)


if __name__ == "__main__":
    unittest.main()
