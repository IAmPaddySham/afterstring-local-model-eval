"""Loader for held-out batch 5 (D-066; Paddy t1737u). 18 items B5-01..B5-18, fresh scenarios,
blind-authored. Mirrors held_out_b4.py.

Retrieval: B5-03 and B5-07 are filed with manifest "none" (no retrieval). Every other item is "v0"
(per run go). A batch-5 sealed run uses one pass with the default v0 retriever and a per-item skip
for the two "none" ids.

NOTE: the loader enforces the sealed pin only after the items are SEALED. Until Paddy's real approval
refs replace the "t-pending" placeholders and the SEALED.sha256 is written, run_held_out_b5 must not be
invoked. Item content is never altered after sealing.
"""
import hashlib
import re
from pathlib import Path

from harness import config
from evals.held_out_b2 import _prompt

HELD_OUT_B5 = Path(config.PROJECT_ROOT) / "evals" / "held-out" / "held-out-b5.md"
SEALED_SHA = Path(config.PROJECT_ROOT) / "evals" / "held-out" / "held-out-b5-SEALED.sha256"
N_ITEMS = 18
STATUS_MARK = "APPROVED by Paddy 2026-11-05"
APPROVAL_LINE = "- **Approval (batch 5):** APPROVED by Paddy 2026-11-05"
MANIFESTS = ("v0", "none")
NO_RETRIEVAL = {"B5-03", "B5-07"}


class NotApproved(Exception):
    pass


def _items_sha256():
    """Read the sealed pin; raise if not yet sealed."""
    if not SEALED_SHA.exists():
        raise NotApproved("batch 5 is not sealed yet: held-out-b5-SEALED.sha256 missing (awaiting Paddy's approval refs)")
    for line in SEALED_SHA.read_text().splitlines():
        if "held-out-b5.md" in line:
            return line.split()[0].strip()
    raise NotApproved("held-out-b5-SEALED.sha256 has no held-out-b5.md line")


def _field(block, name):
    m = re.search(rf"^- {re.escape(name)}: (.*)$", block, re.M)
    return m.group(1).strip() if m else ""


def load(path=None):
    path = Path(path or HELD_OUT_B5)
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if path.resolve() == HELD_OUT_B5.resolve() and digest != _items_sha256():
        raise NotApproved(f"{path.name}: sha256 {digest} != sealed pin")
    text = raw.decode("utf-8")
    if STATUS_MARK not in text or text.count(APPROVAL_LINE) != N_ITEMS:
        raise NotApproved(f"{path.name}: not the approved batch-5 copy (needs {N_ITEMS} approval lines)")
    if "t-pending" in text:
        raise NotApproved(f"{path.name}: approval refs still placeholder (t-pending); awaiting Paddy's real refs")
    out = []
    for block in re.split(r"^### ", text, flags=re.M)[1:]:
        m = re.match(r"(B5-\d{2})\s+·\s+(Model)\s*$", block.splitlines()[0].strip())
        if not m:
            continue
        bid = m.group(1)
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
                    "approval": "", "written_by": _field(block, "Written by"),
                    "sources": sources, "area": _field(block, "Area")})
    if len(out) != N_ITEMS:
        raise ValueError(f"expected exactly {N_ITEMS} batch-5 items, got {len(out)}")
    return out
