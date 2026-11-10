"""D-041: retrieval v1 = v0 + one pinned public X post. v0 stays the default and unchanged."""
import json
import unittest

from harness import config
from harness.retrieval import Retriever, read_allowlist, DENY_PATH

R = config.CONFIGS / "retrieval"
V0A, V0M, V1A, V1M = R / "allowlist-v0.txt", R / "manifest-v0.json", R / "allowlist-v1.txt", R / "manifest-v1.json"
NEW = "imported/x-profile-documents/text/2026-10-26_2114871021539090778.txt"
NEW_SHA = "2fad1927ef38ebc85fdf6af134c8934a01588f1d29db54bd3e4fee2751b94cd0"
V0M_SHA = "621be560f4acb068e77bd654853bc858bc9ac7121f5bbe011dade8db73ead1fa"   # recorded by prior runs
V0A_SHA = "c68f2093ebdf88a81b316faf1b32fb01e523942e854d7a867e750f8ed6e531ea"


class RetrievalV1Tests(unittest.TestCase):
    def test_v0_is_default_and_unchanged(self):
        self.assertEqual(config.RETRIEVAL_MANIFEST, V0M)
        self.assertEqual(config.RETRIEVAL_ALLOWLIST, V0A)
        self.assertEqual(config.sha256_file(V0M), V0M_SHA)
        self.assertEqual(config.sha256_file(V0A), V0A_SHA)

    def test_v1_allowlist_is_v0_plus_one_file(self):
        self.assertEqual(V1A.read_bytes(), V0A.read_bytes() + (NEW + "\n").encode())
        self.assertEqual(read_allowlist(V1A), read_allowlist(V0A) + [NEW])
        self.assertIsNone(DENY_PATH.search(NEW))

    def test_v1_manifest_is_v0_plus_one_entry(self):
        v0, v1 = json.load(open(V0M)), json.load(open(V1M))
        self.assertEqual(v1["version"], "retrieval-v1")
        self.assertEqual(v1["allowlist_sha256"], config.sha256_file(V1A))
        self.assertEqual(v1["files"][:-1], v0["files"])
        self.assertEqual(v1["files"][-1]["path"], NEW)
        self.assertEqual(v1["files"][-1]["sha256"], NEW_SHA)
        self.assertEqual(v1["chunks_total"], v0["chunks_total"] + v1["files"][-1]["chunks"])

    def test_v1_loads_clean(self):
        r = Retriever(str(V1M))
        self.assertEqual(r.error, "")
        self.assertEqual(r.skipped, [])
        self.assertTrue(any(c.path == NEW for c in r.chunks))


if __name__ == "__main__":
    unittest.main()
