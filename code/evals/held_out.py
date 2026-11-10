"""Loader for the approved held-out set (D-029; wiring approved by Paddy t813u, D-035).

Separate from evals/items.py on purpose: items.parse() still returns [] for the held-out file, the held-out
set is never merged into the approved eval set, and nothing here puts held-out text into a system prompt,
retrieval, notes or training. Only an item's quoted user words (and its "(context: ...)" setup line, sent the
same way approved items send context: a bracketed line in the user turn) reach the model, as the turn under test.
Runs of this set are SEALED (runs/<ts>-held-out-SEALED/): no scoring, no review sample, no answer text printed.
"""
import re
from pathlib import Path

from harness import config

HELD_OUT = Path(config.PROJECT_ROOT) / "evals" / "held-out" / "held-out-v0.md"
N_ITEMS = 16
APPROVAL_LINE = "- **Approval:** APPROVED by Paddy 2026-10-27"


class NotApproved(Exception):
    pass


def load(path=None):
    path = Path(path or HELD_OUT)
    text = path.read_text(encoding="utf-8")
    if "APPROVED by Paddy 2026-10-27" not in text or text.count(APPROVAL_LINE) != N_ITEMS:
        raise NotApproved(f"{path.name}: not the approved held-out copy (needs {N_ITEMS} approval lines)")
    out = []
    for block in re.split(r"^### ", text, flags=re.M)[1:]:
        head = block.splitlines()[0]
        m = re.match(r"(HO-\d{2})\s+·\s+(Model)\s*$", head.strip())
        if not m:
            continue
        ms = re.search(r"^- Prompt / setup: (.*)$", block, re.M)
        if not ms:
            raise ValueError(f"{m.group(1)}: no Prompt / setup line")
        setup = ms.group(1).strip()
        a, b = setup.find('"'), setup.rfind('"')
        if a == -1 or b <= a:
            raise ValueError(f"{m.group(1)}: no quoted user words")
        rest = (setup[:a] + setup[b + 1:]).strip()
        mc = re.search(r"\(context:\s*(.*)\)\s*$", rest, re.I | re.S)
        out.append({"id": m.group(1), "kind": "Model", "text": setup[a + 1:b],
                    "context_note": mc.group(1).strip() if mc else ""})
    if len(out) != N_ITEMS or len({i["id"] for i in out}) != N_ITEMS:
        raise ValueError(f"expected {N_ITEMS} distinct HO items, got {len(out)}")
    return out


def sealed_dirname(stamp):
    return f"{stamp}-held-out-SEALED"
