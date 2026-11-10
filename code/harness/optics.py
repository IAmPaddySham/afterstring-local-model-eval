"""Input guard (4.2-inspired), v0 — rules OR-01…OR-15 as approved (pt705u).

Deterministic: keyword lists (configs/filter/rules-v0.yaml), the clock and counters.
No model, no score. Three outputs only: PASS, ANNOTATE, HOLD. It has no way to
PERMIT and never touches 1/0. Most restrictive wins (HOLD > ANNOTATE > PASS).
D-021: OR-07 (release words) may only annotate; it never weakens a HOLD. Real stops are
handled before this guard by the release hard path (harness/release.py). Any error, a run over 50 ms, or a
rules file whose sha256 differs from the pin gives HOLD (OR-15).
"""
import re
import time
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import yaml

from . import config
from .actions import Action

PASS, ANNOTATE, HOLD = "PASS", "ANNOTATE", "HOLD"
VERDICTS = (PASS, ANNOTATE, HOLD)
_RANK = {PASS: 0, ANNOTATE: 1, HOLD: 2}

# id -> (plain tag, lineage tag)
RULE_META = {
    "OR-01": ("small_hours_consequential", "4.2-inspired"),
    "OR-02": ("urgency_or_threat", "4.2-inspired"),
    "OR-03": ("injected_authority_quarantined", "4.2-inspired"),
    "OR-04": ("earlier_yes_not_reusable", "4.2-inspired"),
    "OR-05": ("insight_is_not_authorization", "4.2-inspired"),
    "OR-06": ("unverified_success_requested", "4.1-reality"),
    "OR-07": ("release_requested", "4.2-inspired"),
    "OR-08": ("approval_fatigue", "4.2-inspired"),
    "OR-09": ("sycophancy_pressure", "4.2-inspired"),
    "OR-10": ("hostile_tone", "4.2-inspired"),
    "OR-11": ("pressure_or_deceive_other", "4.2-inspired"),
    "OR-12": ("drift", "4.1-reality"),
    "OR-13": ("certainty_requested", "4.1-reality"),
    "OR-14": ("past_wrong_referenced", "4.2-inspired"),
    "OR-15": ("filter_failed_closed", "4.2-inspired"),
}


@dataclass
class FilterInput:
    text: str
    passages: List[Tuple[str, str]] = field(default_factory=list)  # (source, text)
    action: Optional[Action] = None
    local_hour: Optional[float] = None
    session_minutes: float = 0.0
    approvals_last_60min: int = 0
    prev_verdict: Optional[str] = None
    tool_status: Optional[str] = None    # "ok" | "fail" | None


@dataclass
class Fired:
    rule: str
    action: str
    tag: str
    lineage: str
    detail: str = ""


@dataclass
class Verdict:
    verdict: str
    fired: List[Fired]
    quarantined: List[int]
    elapsed_ms: float
    rules_sha256: str
    release_requested: bool = False
    suppressed_by_release: List[str] = field(default_factory=list)
    error: str = ""

    @property
    def tags(self):
        return [f.tag for f in self.fired]

    def by_lineage(self, lineage):
        return [f.rule for f in self.fired if f.lineage == lineage]


class InputGuard:
    def __init__(self, rules_path=None, pin_path=None, max_elapsed_ms=None):
        self.rules_path = rules_path or config.RULES_YAML
        self.pin_path = pin_path or config.RULES_PIN
        self._load_error = ""
        self.rules_sha256 = ""
        self.pinned = ""
        self.lists = {}
        self.th = {}
        try:
            self.rules_sha256 = config.sha256_file(self.rules_path)
            with open(self.pin_path) as f:
                self.pinned = f.read().strip()
            with open(self.rules_path) as f:
                doc = yaml.safe_load(f)
            self.th = doc["thresholds"]
            self.lists = {k: [re.compile(p, re.I) for p in v] for k, v in doc["lists"].items()}
        except Exception as e:  # fail closed at evaluate()
            self._load_error = f"{type(e).__name__}: {e}"
        self.max_elapsed_ms = max_elapsed_ms if max_elapsed_ms is not None else \
            float(self.th.get("max_elapsed_ms", 50))

    def _m(self, name, text):
        for p in self.lists[name]:
            m = p.search(text or "")
            if m:
                return m.group(0)
        return None

    def _hold15(self, t0, why):
        return Verdict(HOLD, [Fired("OR-15", HOLD, *RULE_META["OR-15"], detail=why)], [],
                       (time.perf_counter() - t0) * 1000, self.rules_sha256, error=why)

    def evaluate(self, inp: FilterInput) -> Verdict:
        t0 = time.perf_counter()
        if self._load_error:
            return self._hold15(t0, "rules failed to load: " + self._load_error)
        if self.rules_sha256 != self.pinned:
            return self._hold15(t0, "rules_hash != pinned_hash")
        try:
            v = self._rules(inp, t0)
        except Exception as e:
            return self._hold15(t0, f"exception: {type(e).__name__}: {e}")
        if v.elapsed_ms > self.max_elapsed_ms:
            return self._hold15(t0, f"elapsed {v.elapsed_ms:.2f} ms > {self.max_elapsed_ms} ms")
        return v

    # The rules, in table order. Conditions are written as in optics-rules-v0.md.
    def _rules(self, inp: FilterInput, t0) -> Verdict:
        th = self.th
        text = inp.text or ""
        a = inp.action
        tier = a.tier if a is not None else 0
        cons = tier >= int(th["consequential_tier"])
        h = inp.local_hour
        fired, quarantined = [], []

        def fire(rule, action, detail=""):
            fired.append(Fired(rule, action, *RULE_META[rule], detail=detail))

        sh0, sh1 = th["small_hours"]
        if h is not None and sh0 <= h < sh1 and cons:
            fire("OR-01", HOLD, f"local_hour={h} tier={tier}")
        m = self._m("URGENCY_THREAT", text)
        if m:
            fire("OR-02", HOLD if cons else ANNOTATE, repr(m))
        for i, (src, ptxt) in enumerate(inp.passages):
            if src in ("retrieval", "tool"):
                m = self._m("INJECTED_AUTHORITY", ptxt)
                if m:
                    quarantined.append(i)
                    fire("OR-03", HOLD, f"passage {i} ({src}): {m!r}")
        m = self._m("PRIOR_OR_BLANKET_PERMISSION", text)
        if m:
            fire("OR-04", ANNOTATE, repr(m))
        m = self._m("INSIGHT_AS_AUTH", text)
        if m:
            fire("OR-05", ANNOTATE, repr(m))
        m = self._m("SAY_IT_WORKED", text)
        m2 = self._m("REASSURE_REQ", text) if inp.tool_status == "fail" else None
        if m or m2:
            fire("OR-06", ANNOTATE, repr(m or m2))
        m = self._m("RELEASE_WORDS", text)
        release = bool(m)
        if m:
            fire("OR-07", ANNOTATE, repr(m))
        if inp.approvals_last_60min >= int(th["n_fatigue"]) and cons:
            fire("OR-08", HOLD, f"approvals_last_60min={inp.approvals_last_60min}")
        if inp.prev_verdict == HOLD:
            m = self._m("FLATTERY_OR_EXCEPTION", text)
            if m:
                fire("OR-09", ANNOTATE, repr(m))
        m = self._m("HOSTILE", text)
        if m:
            fire("OR-10", ANNOTATE, repr(m))
        m = self._m("MANIPULATE_OTHER", text)
        if m:
            fire("OR-11", HOLD if (a is not None and a.verb in ("send", "post")) else ANNOTATE, repr(m))
        m = self._m("ONLY_YOU_UNDERSTAND", text)
        d0, d1 = th["drift_hours"]
        late_long = h is not None and d0 <= h < d1 and inp.session_minutes > th["drift_session_minutes"]
        if m or late_long:
            fire("OR-12", ANNOTATE, repr(m) if m else f"session={inp.session_minutes}min hour={h}")
        m = self._m("CERTIFY_REQ", text)
        if m:
            fire("OR-13", ANNOTATE, repr(m))
        m = self._m("PAST_WRONG", text)
        if m:
            fire("OR-14", ANNOTATE, repr(m))

        verdict = PASS
        for f in fired:
            if _RANK[f.action] > _RANK[verdict]:
                verdict = f.action
        # OR-07 only annotates (D-021). It never weakens a HOLD: a real stop is handled
        # earlier by the release hard path (release.py), which never calls the model or
        # the gate. A message that merely contains a release word ("..., and stop asking
        # me") is not a stop and must not unlock a held action.
        suppressed = []
        assert verdict in VERDICTS
        return Verdict(verdict, fired, quarantined, (time.perf_counter() - t0) * 1000,
                       self.rules_sha256, release_requested=release,
                       suppressed_by_release=suppressed)
