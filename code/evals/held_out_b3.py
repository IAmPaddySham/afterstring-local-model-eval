"""Loader for held-out batch 3 (D-052; 18 items B3-01..B3-18, Gemini pass 2, approved by Paddy 2026-11-01,
t1233u-t1251u; wiring named at t1253u).

Kept separate from batches 1 and 2: `held_out.py` and `held_out_b2.py` are unchanged. This file is NOT wired into
evals/run.py, so batch 3 cannot be run from here. Running it needs Paddy's go. Nothing here puts held-out text
into a prompt, retrieval, notes or training; only an item's quoted user words (and its "(context: ...)" line,
D-036) are meant to reach a model, as the turn under test.
"""
import re
from pathlib import Path

from harness import config
from evals.held_out_b2 import _prompt

HELD_OUT_B3 = Path(config.PROJECT_ROOT) / "evals" / "held-out" / "held-out-b3.md"
N_ITEMS = 18
STATUS_MARK = "APPROVED by Paddy 2026-11-01"
APPROVAL_LINE = "- **Approval (batch 3):** APPROVED by Paddy 2026-11-01"
MANIFESTS = ("v0",)
APPROVED = {f"B3-{n:02d}": f"t{1233 + n}u" for n in range(2, 19)}
APPROVED["B3-01"] = "t1233u/t1234u"
APPROVED = dict(sorted(APPROVED.items()))
CITE = re.compile(r"((?:papers|projects|imported)/[\w./-]+\.(?:md|txt)):L(\d+)(?:-L(\d+))?")


class NotApproved(Exception):
    pass


def _field(block, name):
    m = re.search(rf"^- {re.escape(name)}: (.*)$", block, re.M)
    return m.group(1).strip() if m else ""


def citations(sources):
    """[(path, start, end)] from a Sources line; 'none' gives []."""
    return [(p, int(a), int(b or a)) for p, a, b in CITE.findall(sources or "")]


def load(path=None):
    path = Path(path or HELD_OUT_B3)
    text = path.read_text(encoding="utf-8")
    if STATUS_MARK not in text or text.count(APPROVAL_LINE) != N_ITEMS:
        raise NotApproved(f"{path.name}: not the approved batch-3 copy (needs {N_ITEMS} batch-3 approval lines)")
    out = []
    for block in re.split(r"^### ", text, flags=re.M)[1:]:
        m = re.match(r"(B3-\d{2})\s+·\s+(Model)\s*$", block.splitlines()[0].strip())
        if not m:
            continue
        bid = m.group(1)
        if bid not in APPROVED:
            raise NotApproved(f"{bid}: not in the batch-3 approval record")
        appr = re.findall(rf"^{re.escape(APPROVAL_LINE)}, (\S+)$", block, re.M)
        if appr != [APPROVED[bid]]:
            raise NotApproved(f"{bid}: approval line missing or not {APPROVED[bid]}")
        manifest = _field(block, "Retrieval manifest").split()[0:1]
        if manifest != ["v0"]:
            raise ValueError(f"{bid}: retrieval manifest must be v0")
        for f in ("Pass", "Partial", "Fail", "Why", "Written by"):
            if not _field(block, f):
                raise ValueError(f"{bid}: no {f} line")
        words, note = _prompt(bid, block)
        wired = _field(block, "Sources (wired, D-052)")
        sources = wired or _field(block, "Sources")
        out.append({"id": bid, "kind": "Model", "text": words, "context_note": note, "manifest": "v0",
                    "approval": APPROVED[bid], "written_by": _field(block, "Written by"),
                    "sources": sources, "citations": citations(sources),
                    "wiring_note": _field(block, "Wiring note (D-052)")})
    if [i["id"] for i in out] != list(APPROVED):
        raise ValueError(f"expected exactly the {N_ITEMS} approved batch-3 items in order, got {len(out)}")
    return out
