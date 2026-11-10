"""Parse evals/drafts/2026-10-25-eval-items-v0.md (61 items).

This file is a harness answer key: only an item's prompt text may reach a model,
and only as the prompt under test.
"""
import re
from harness import config

FIELDS = {"REQ": "req", "Source": "source", "Prompt / setup": "setup", "Pass": "pass_",
          "Fail examples": "fail", "Status": "status",
          # optional, used by practice files (evals/practice/); absent from the approved v0 file
          "Local hour": "local_hour", "Context note": "context_note", "Then": "then",
          "Expected path": "expected_path"}


def parse(path=None):
    with open(path or config.EVAL_ITEMS, encoding="utf-8") as f:
        text = f.read()
    items = []
    for block in re.split(r"^### ", text, flags=re.M)[1:]:
        head, *lines = block.splitlines()
        m = re.match(r"((?:EV|PRACTICE|B3|B4|B5)-[A-Za-z0-9-]+)\s+·\s+(Harness|Model)", head.strip())  # D-055: B3 ids for evals/diagnostic/; D-060: B4
        if not m:
            continue
        it = {"id": m.group(1), "kind": m.group(2)}
        for ln in lines:
            mm = re.match(r"- ([^:]+): (.*)$", ln)
            if mm and mm.group(1) in FIELDS:
                it[FIELDS[mm.group(1)]] = mm.group(2).strip()
        if it["id"].startswith(("B3-", "B4-", "B5-")) and "context_note" not in it:   # D-055 diagnostic: same split as held_out_b2._prompt
            mc = re.search(r"\s*\(context:\s*(.*)\)\s*$", it.get("setup", ""), re.I | re.S)
            if mc:
                it["context_note"], it["setup"] = mc.group(1).strip(), it["setup"][:mc.start()].strip()
        items.append(it)
    return items


def quoted_prompt(setup):
    """The user's words: text between the first and last straight double quote."""
    a, b = setup.find('"'), setup.rfind('"')
    if a == -1 or b <= a:
        return None
    return setup[a + 1:b]


def expected_words(pass_text):
    """For governor-pack items: (main word, accepted set, needs_bypass_event)."""
    m = re.search(r"\*\*([A-Z_]+)( \+ bypass event)?\*\*", pass_text or "")
    if not m:
        return None, set(), False
    acc = {m.group(1)}
    ma = re.search(r"\(accept ([A-Z_/ ]+)\)", pass_text)
    if ma:
        acc |= {w.strip() for w in ma.group(1).split("/") if w.strip()}
    return m.group(1), acc, bool(m.group(2))
