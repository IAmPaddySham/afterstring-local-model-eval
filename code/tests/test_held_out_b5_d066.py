import unittest
from evals import held_out_b5 as hb


class TestB5Loader(unittest.TestCase):
    def test_loads_sealed(self):
        hs = hb.load()
        self.assertEqual(len(hs), 18)
        self.assertEqual([i["id"] for i in hs][:3], ["B5-01", "B5-02", "B5-03"])

    def test_no_retrieval_ids(self):
        hs = hb.load()
        none_ids = {i["id"] for i in hs if i["manifest"] == "none"}
        self.assertEqual(none_ids, {"B5-03", "B5-07"})
        self.assertEqual(hb.N_ITEMS, 18)

    def test_sealed_pin_present(self):
        self.assertTrue(hb.SEALED_SHA.exists())


if __name__ == "__main__":
    unittest.main()
