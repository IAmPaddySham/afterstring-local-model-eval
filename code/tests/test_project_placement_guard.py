"""Guard (folder repair 2026-11-05): project code lives under council/inbox/projects/.

Root projects/ may hold only the four originals kept until Paddy names retirement.
archive/ is excluded: it is a dated safety net, not a project home.
When the originals are retired, empty PENDING_RETIREMENT.
"""
import unittest
from pathlib import Path

from harness.config import AFTERSTRING_ROOT

PENDING_RETIREMENT = {
    "local-model-eval",
    "2026-11-05-model-collapse-afterstring",
    "fail-close-governor",
    "afterstring-neuron",
}


class ProjectPlacementGuard(unittest.TestCase):
    def test_root_resolves_to_house(self):
        self.assertTrue((AFTERSTRING_ROOT / "council" / "inbox" / "projects").is_dir())

    def test_no_new_project_outside_council_projects(self):
        root_projects = AFTERSTRING_ROOT / "projects"
        if not root_projects.is_dir():
            return
        found = {p.name for p in root_projects.iterdir()
                 if p.is_dir() and not p.name.startswith(".")}
        stray = sorted(found - PENDING_RETIREMENT)
        self.assertEqual(stray, [], f"project folders outside council/inbox/projects/: {stray}")

    def test_this_repo_sits_in_council_projects(self):
        here = Path(__file__).resolve()
        self.assertNotIn("archive", here.relative_to(AFTERSTRING_ROOT).parts[:1])
        self.assertIn(AFTERSTRING_ROOT / "council" / "inbox" / "projects", here.parents)


if __name__ == "__main__":
    unittest.main()
