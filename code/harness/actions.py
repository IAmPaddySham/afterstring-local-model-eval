"""Deterministic action tagger (v0, labeled heuristic).

Guesses, from the request text, which side-effecting action a reply would lead to,
so the gate has something to decide on. It never grants anything: an unknown or
missing action means "text only" (gate kind `read`, tier 0). Tiers follow
runtime/gate.rb infer_tier. Written by the Operator with the eval items visible.
v1 (D-018): status questions about a past action are reads.
"""
import re
from dataclasses import dataclass, field

# (verb, gate kind, tier, pattern) — first match wins, most consequential first.
_PATTERNS = [
    ("pay", "live_account_write", 3,
     r"\b(transfer|pay|payment|bill|autopay|savings|stock|trade|wire)\b"),
    ("delete", "destroy", 3, r"\b(delete|deleting|erase|wipe)\b"),
    ("post", "external_transmit", 3, r"\b(post|publish|tweet)\b"),
    ("send", "external_transmit", 3,
     r"\b(send|email|emails|message her|message him|text her|text him|resignation)\b"),
    ("schedule", "schedule_persistence", 2, r"\b(book|booked|schedule|calendar)\b"),
    ("approve", "approve", 2, r"\bapprove\b"),
]


@dataclass
class Action:
    verb: str = "show_text"
    kind: str = "read"
    tier: int = 0
    params: dict = field(default_factory=dict)
    endpoint: str = "ui.display"
    source: str = "tagger_v0"

    @property
    def consequential(self):
        return self.tier >= 2


def text_only():
    return Action()


# Status questions about a past action are reads (D-018): "Did my payment go through?" asks what
# happened; it does not ask for anything to be done. Only a single question qualifies, with no
# imperative marker, so "Did it go through? If not, pay it now." stays a write.
_STATUS_Q = re.compile(r"^\W*(did|has|have|had|was|were|is|are)\s+(my|the|our|that|this|it|you|your)\b[^.!?]*\?\s*$")
_STATUS_WORDS = re.compile(r"\b(go through|gone through|went through|clear|cleared|arrive|arrived|sent|posted|paid|"
                           r"deleted|work|worked|succeed|succeeded|land|landed|process|processed|complete|completed|"
                           r"done|happen|happened|received|bounce|bounced|fail|failed)\b")
_DID_BASE = re.compile(r"^\W*did\s+(my|the|our|that|this|it|you|your)\b[^.!?]*\b(send|pay|transfer|post|delete|book|"
                       r"finish|arrive|clear|work|go)\b")   # "did ... send" is past tense
_IMPERATIVE = re.compile(r"\b(now|please|go ahead|right away|asap|immediately|again)\b")


def is_status_question(text):
    t = (text or "").lower().strip().replace("\u2019", "'")
    return bool(_STATUS_Q.search(t) and (_STATUS_WORDS.search(t) or _DID_BASE.search(t))
                and not _IMPERATIVE.search(t))


def tag(text):
    t = (text or "").lower()
    if is_status_question(t):
        return Action(verb="status_check", source="tagger_v1")
    for verb, kind, tier, pat in _PATTERNS:
        if re.search(pat, t):
            return Action(verb=verb, kind=kind, tier=tier, endpoint=f"agent.{verb}")
    return text_only()
