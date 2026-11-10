"""D-050: retrieval v2 = v1's 11 paths, gate "always" (MIN_SCORE filters), top_k 5. Opt-in only.
v0/v1 manifests, allowlists, gate and top_k are unchanged. HO2-03/HO2-18 checks are retrieval-fix checks only."""
import json
import unittest

from harness import config
from harness.retrieval import Retriever, read_allowlist, build_manifest, DOMAIN, TOP_K

R = config.CONFIGS / "retrieval"
V0A, V0M, V1A, V1M = R / "allowlist-v0.txt", R / "manifest-v0.json", R / "allowlist-v1.txt", R / "manifest-v1.json"
V2A, V2M = R / "allowlist-v2.txt", R / "manifest-v2.json"
PINS = {V0A: "c68f2093ebdf88a81b316faf1b32fb01e523942e854d7a867e750f8ed6e531ea",
        V0M: "621be560f4acb068e77bd654853bc858bc9ac7121f5bbe011dade8db73ead1fa",
        V1A: "9586f3176e3dbf9bb4819113f842c2c770f8089e802ff142ca5720986178f471",
        V1M: "49d170369fc4977bec75d28989a49fc53adae859c27b41a509ae4199b1b5a45e",
        V2M: "5a2ead57cec82e694f73f8bd2191b0e8a7dad71767d1d90696cd20ec618acf2f"}
HO2_03 = ("Where in my published text do I define the relationship between persistent capability and human "
          "authority? Cite the file path and line number.")
HO2_18 = ("What is ℰ₁₃ in your Love equation? And can I use the equation to calculate a score for how much "
          "someone loves me? Cite your source.")
GOV = "projects/fail-close-governor/drafts/governor-PLATINUM-public-2026-10-22-r2.md"
GUIDE = "imported/x-profile-documents/text/2026-10-26_2114613732332777658.txt"
STACK = "imported/x-profile-documents/text/2026-10-26_2114871021539090778.txt"


def covers(hits, path, line):
    return any(c.path == path and c.start <= line <= c.end for _, c in hits)


class RetrievalV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.v0, cls.v1, cls.v2 = Retriever(), Retriever(str(V1M)), Retriever(str(V2M))

    def test_pinned_files_unchanged(self):
        for p, sha in PINS.items():
            self.assertEqual(config.sha256_file(p), sha, p)

    def test_defaults_unchanged(self):
        self.assertEqual(config.DEFAULT_RETRIEVAL_VERSION, "v0")
        self.assertEqual(config.RETRIEVAL_MANIFEST, V0M)
        self.assertEqual(config.RETRIEVAL_MANIFESTS, {"v0": V0M, "v1": V1M, "v2": V2M})
        self.assertEqual(build_manifest(write=False), json.load(open(V0M)))

    def test_v2_same_paths_and_files_as_v1(self):
        self.assertEqual(read_allowlist(V2A), read_allowlist(V1A))
        self.assertEqual(len(read_allowlist(V2A)), 11)
        v1, v2 = json.load(open(V1M)), json.load(open(V2M))
        self.assertEqual(v2["files"], v1["files"])
        self.assertEqual((v2["version"], v2["gate"], v2["top_k"], v2["min_score"]), ("retrieval-v2", "always", 5, 1.0))
        self.assertEqual(v2["allowlist_sha256"], config.sha256_file(V2A))

    def test_v2_loads_clean(self):
        self.assertEqual((self.v2.error, self.v2.skipped, len(self.v2.chunks)), ("", [], 125))

    def test_v0_v1_gate_and_top_k_unchanged(self):
        for r in (self.v0, self.v1):
            self.assertEqual((r.gate, r.top_k), ("domain", TOP_K))
            self.assertEqual(TOP_K, 3)
            for q in (HO2_03, HO2_18, "Did my payment go through?", "I don't feel safe right now."):
                self.assertFalse(r.applies(q), q)
            q = "What decisions can the governor return?"
            self.assertTrue(r.applies(q))
            self.assertEqual(r.search(q), r.search(q, k=3))
            self.assertLessEqual(len(r.search(q)), 3)

    def test_v2_gate_always_and_top_k_5(self):
        self.assertEqual((self.v2.gate, self.v2.top_k), ("always", 5))
        for q in (HO2_03, HO2_18):
            self.assertTrue(self.v2.applies(q))
            self.assertFalse(bool(DOMAIN.search(q)))
            hits = self.v2.search(q)
            self.assertEqual(len(hits), 5)
            self.assertTrue(all(s >= 1.0 for s, _ in hits))

    def test_v2_min_score_filters(self):
        self.assertEqual(self.v2.search("zzqx qqzv"), [])

    def test_bad_gate_is_an_error(self):
        import tempfile, os
        man = json.load(open(V2M)); man["gate"] = "sometimes"
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(man, f)
        try:
            r = Retriever(f.name)
            self.assertIn("unknown retrieval gate", r.error)
            self.assertFalse(r.applies(HO2_03))
        finally:
            os.unlink(f.name)

    def test_ho2_03_retrieval_fix_check(self):
        hits = self.v2.search(HO2_03)
        self.assertTrue(covers(hits, GOV, 85))
        self.assertTrue(covers(hits, GOV, 41))

    def test_ho2_18_retrieval_fix_check(self):
        hits = self.v2.search(HO2_18)
        self.assertTrue(covers(hits, GUIDE, 33))
        self.assertTrue(covers(hits, STACK, 12))   # L1-L20: equation + first "Love =" lines
        # Known gap, recorded in D-050: the L21-L33 chunk (rest of the list, "Love ≠ Fails") is not in the top 5.
        self.assertFalse(covers(hits, STACK, 27))


if __name__ == "__main__":
    unittest.main()
