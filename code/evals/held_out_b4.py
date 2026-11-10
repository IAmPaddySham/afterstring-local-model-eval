"""Loader for held-out batch 4 (D-057 sealed; D-058 wiring. 18 items B4-01..B4-18, Google AI Mode r2,
approved by Paddy 2026-11-04; wiring named at t1625u).

Kept separate from batches 1–3: `held_out.py`, `held_out_b2.py` and `held_out_b3.py` are unchanged. Wired into
evals/run.py as opt-in `--held-out-b4` (D-058). Nothing here puts held-out text into a prompt, retrieval, notes
or training; only an item's quoted user words (and its "(context: ...)" line, D-036) are meant to reach a model,
as the turn under test.

Retrieval (D-057 / D-058): B4-03 and B4-07 are filed with manifest "none" (no retrieval; t1617u, t1618u). Every
other item is filed with manifest "v0" (621be560…). A batch-4 sealed run uses one pass with the default v0
retriever and a per-item skip for the two "none" ids.
"""
import hashlib
import re
from pathlib import Path

from harness import config
from evals.held_out_b2 import _prompt

HELD_OUT_B4 = Path(config.PROJECT_ROOT) / "evals" / "held-out" / "held-out-b4.md"
SEALED_SHA = Path(config.PROJECT_ROOT) / "evals" / "held-out" / "held-out-b4-SEALED.sha256"
N_ITEMS = 18
STATUS_MARK = "APPROVED by Paddy 2026-11-04"
APPROVAL_LINE = "- **Approval (batch 4):** APPROVED by Paddy 2026-11-04"
MANIFESTS = ("v0", "none")
NO_RETRIEVAL = {"B4-03", "B4-07"}
# Pin from held-out-b4-SEALED.sha256 (D-057); loader refuses a different copy.
ITEMS_SHA256 = "d6da34d5a01494a4c6ed5da8e4c578ff8e334a8a024a2f7026ea2c28aaf01a3c"

# Approval record (D-057): exactly these 18 items with the turn(s) on each Approval line.
APPROVED = {
    "B4-01": "t1543u",
    "B4-02": "t1544u",
    "B4-03": "t1547u/t1617u",
    "B4-04": "t1603s13450",
    "B4-05": "t1603s13456/t1617u/t1618u",
    "B4-06": "t1603s13462/t1604s13471/t1621u",
    "B4-07": "t1604s13471/t1618u",
    "B4-08": "t1604s13477/t1604s13483",
    "B4-09": "t1604s13483/t1619s13598",
    "B4-10": "t1604s13489",
    "B4-11": "t1604s13495",
    "B4-12": "t1604s13501",
    "B4-13": "t1604s13507",
    "B4-14": "t1604s13513",
    "B4-15": "t1614s13557/t1614s13563",
    "B4-16": "t1614s13563",
    "B4-17": "t1614s13569",
    "B4-18": "t1614s13575",
}


class NotApproved(Exception):
    pass


def _field(block, name):
    m = re.search(rf"^- {re.escape(name)}: (.*)$", block, re.M)
    return m.group(1).strip() if m else ""


def load(path=None):
    path = Path(path or HELD_OUT_B4)
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if path.resolve() == HELD_OUT_B4.resolve() and digest != ITEMS_SHA256:
        raise NotApproved(f"{path.name}: sha256 {digest} != sealed pin {ITEMS_SHA256}")
    text = raw.decode("utf-8")
    if STATUS_MARK not in text or text.count(APPROVAL_LINE) != N_ITEMS:
        raise NotApproved(f"{path.name}: not the approved batch-4 copy (needs {N_ITEMS} batch-4 approval lines)")
    out = []
    for block in re.split(r"^### ", text, flags=re.M)[1:]:
        m = re.match(r"(B4-\d{2})\s+·\s+(Model)\s*$", block.splitlines()[0].strip())
        if not m:
            continue
        bid = m.group(1)
        if bid not in APPROVED:
            raise NotApproved(f"{bid}: not in the batch-4 approval record")
        appr = re.findall(rf"^{re.escape(APPROVAL_LINE)}, (\S+)$", block, re.M)
        if appr != [APPROVED[bid]]:
            raise NotApproved(f"{bid}: approval line missing or not {APPROVED[bid]}")
        man_raw = _field(block, "Retrieval manifest")
        if bid in NO_RETRIEVAL:
            if "none" not in man_raw.lower() or "no retrieval" not in man_raw.lower():
                raise ValueError(f"{bid}: retrieval manifest must be none (no retrieval)")
            manifest = "none"
        else:
            if "per run go" not in man_raw.lower() and man_raw.split()[0:1] != ["v0"]:
                raise ValueError(f"{bid}: retrieval manifest must be per run go (v0 at run time)")
            manifest = "v0"
        for f in ("Pass", "Partial", "Fail", "Why", "Written by"):
            if not _field(block, f):
                raise ValueError(f"{bid}: no {f} line")
        words, note = _prompt(bid, block)
        sources = _field(block, "Sources")
        out.append({"id": bid, "kind": "Model", "text": words, "context_note": note, "manifest": manifest,
                    "approval": APPROVED[bid], "written_by": _field(block, "Written by"),
                    "sources": sources, "area": _field(block, "Area")})
    if [i["id"] for i in out] != list(APPROVED):
        raise ValueError(f"expected exactly the {N_ITEMS} approved batch-4 items in order, got {len(out)}")
    return out
