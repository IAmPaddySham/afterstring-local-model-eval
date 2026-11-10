"""Loader for held-out batch 2 (D-043; 18 items approved by Paddy 2026-10-28: t832u, t844u, t846u-t863u).

Kept separate from batch 1 on purpose. `evals/held_out.py` (batch 1, HO-01..HO-16, D-029/D-035) is not changed
and refuses this file; this loader refuses batch 1. `evals/items.py` does not parse either file. Nothing here
puts held-out text into a system prompt, retrieval, notes or training: only an item's quoted user words (and
its "(context: ...)" line, D-036) are meant to reach a model, as the turn under test.

Wired into evals/run.py as `--held-out-b2` (D-044, Paddy t874u), but not run: running batch 2 needs Paddy's go.
Each item records the retrieval manifest it needs ("v0" default; "v1" for HO2-18 / OP-02, D-041). A batch-2 run
uses one manifest and runs only the items filed with it (select()); its folder is named by sealed_dirname().
"""
import re
from pathlib import Path

from harness import config

HELD_OUT_B2 = Path(config.PROJECT_ROOT) / "evals" / "held-out" / "held-out-b2.md"
N_ITEMS = 18
STATUS_MARK = "APPROVED by Paddy 2026-10-28"
APPROVAL_LINE = "- **Approval (batch 2):** APPROVED by Paddy 2026-10-28"
MANIFESTS = ("v0", "v1")

# The approval record (D-043): exactly these 18 items, each with the turn in which Paddy approved it.
APPROVED = {
    "HO2-01": ("MISTRAL-01", "t846u"), "HO2-02": ("CHATGPT-01", "t847u"), "HO2-03": ("GEMINI-02", "t848u"),
    "HO2-04": ("CHATGPT-02", "t849u"), "HO2-05": ("CHATGPT-03", "t850u"), "HO2-06": ("META-03", "t851u"),
    "HO2-07": ("META-04", "t852u"), "HO2-08": ("DEEPSEEK-04", "t853u"), "HO2-09": ("CHATGPT-05", "t854u"),
    "HO2-10": ("MISTRAL-05", "t856u"), "HO2-11": ("MISTRAL-06", "t857u"), "HO2-12": ("GEMINI-06", "t858u"),
    "HO2-13": ("MISTRAL-07", "t860u"), "HO2-14": ("CHATGPT-07", "t861u"), "HO2-15": ("CHATGPT-08", "t862u"),
    "HO2-16": ("DEEPSEEK-08", "t863u"), "HO2-17": ("OP-01", "t832u"), "HO2-18": ("OP-02", "t844u"),
}


class NotApproved(Exception):
    pass


def _field(block, name):
    m = re.search(rf"^- {re.escape(name)}: (.*)$", block, re.M)
    return m.group(1).strip() if m else ""


def _prompt(hid, block):
    ms = re.search(r"^- Prompt / setup(?: \*\*\[[^\]\n]*\]\*\*)?: (.*)$", block, re.M)
    if not ms:
        raise ValueError(f"{hid}: no Prompt / setup line")
    setup = ms.group(1).strip()
    note = ""
    mc = re.search(r"\s*\(context:\s*(.*)\)\s*$", setup, re.I | re.S)
    if mc:                       # split the context line off first: it may hold its own quotes
        note, setup = mc.group(1).strip(), setup[:mc.start()].strip()
    a, b = setup.find('"'), setup.rfind('"')
    if a == -1 or b <= a:
        raise ValueError(f"{hid}: no quoted user words")
    if setup[b + 1:].strip():
        raise ValueError(f"{hid}: text after the quoted user words")
    return setup[a + 1:b], note


def load(path=None):
    path = Path(path or HELD_OUT_B2)
    text = path.read_text(encoding="utf-8")
    if STATUS_MARK not in text or text.count(APPROVAL_LINE) != N_ITEMS:
        raise NotApproved(f"{path.name}: not the approved batch-2 copy (needs {N_ITEMS} batch-2 approval lines)")
    out = []
    for block in re.split(r"^### ", text, flags=re.M)[1:]:
        head = block.splitlines()[0]
        m = re.match(r"(HO2-\d{2})\s+·\s+(Model)\s*$", head.strip())
        if not m:
            continue
        hid = m.group(1)
        if hid not in APPROVED:
            raise NotApproved(f"{hid}: not in the batch-2 approval record")
        orig, turn = APPROVED[hid]
        appr = re.findall(rf"^{re.escape(APPROVAL_LINE)}, (t\d+u)\b", block, re.M)
        if appr != [turn]:
            raise NotApproved(f"{hid}: approval line missing or not {turn}")
        if not re.search(rf"^- \*\*APPROVED by Paddy {turn} 2026-10-28 ", block, re.M):
            raise NotApproved(f"{hid}: verbatim approval line for {turn} missing")
        if _field(block, "Original ID").split()[0:1] != [orig]:
            raise ValueError(f"{hid}: original id is not {orig}")
        manifest = _field(block, "Retrieval manifest").split()[0:1]
        if not manifest or manifest[0] not in MANIFESTS:
            raise ValueError(f"{hid}: retrieval manifest must be one of {MANIFESTS}")
        words, note = _prompt(hid, block)
        out.append({"id": hid, "kind": "Model", "text": words, "context_note": note,
                    "original_id": orig, "aliases": _field(block, "Aliases"),
                    "written_by": _field(block, "Written by"), "manifest": manifest[0], "approval": turn})
    if [i["id"] for i in out] != list(APPROVED):
        raise ValueError(f"expected exactly the {N_ITEMS} approved batch-2 items in order, got {len(out)}")
    return out


def select(items, manifest):
    """D-044: the items a batch-2 run on `manifest` runs (those filed with it) and the ids it leaves out."""
    if manifest not in MANIFESTS:
        raise ValueError(f"retrieval manifest must be one of {MANIFESTS}")
    chosen = [i for i in items if i["manifest"] == manifest]
    if not chosen:
        raise ValueError(f"no batch-2 item is filed with retrieval {manifest}")
    return chosen, [i["id"] for i in items if i["manifest"] != manifest]


def sealed_dirname(stamp, manifest="v0"):
    """D-044: v0 part -> <ts>-held-out-b2-SEALED; v1 part (HO2-18 only) -> <ts>-held-out-b2-v1-SEALED."""
    if manifest not in MANIFESTS:
        raise ValueError(f"retrieval manifest must be one of {MANIFESTS}")
    return f"{stamp}-held-out-b2-SEALED" if manifest == "v0" else f"{stamp}-held-out-b2-{manifest}-SEALED"
