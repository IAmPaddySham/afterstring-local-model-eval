"""Release hard path (REQ-037, REQ-007, OR-07).

Checked before anything else. When it fires, it returns at once: no model call,
no filter, no gate. It only ever stops things; it can never start or authorize one.
"""
import re
import time
from dataclasses import dataclass, field

# D-025: a message releases only when EVERY sentence in it is a stand-alone stop/leave
# command. "Stop, I need help", "Stop being so negative and help me plan" and
# "I'm done with my homework, can you check it?" carry a request, so they go to the model.
# Text *about* stopping ("even if I say stop") never releases. OR-07 only annotates.
_SENTENCE = re.compile(
    r"(?:(?:please|ok(?:ay)?|enough|just)[\s,]+)*"
    r"(?:(?:stop|halt|cancel|quit)(?:[\s,]+(?:it|now|please|that|this|everything|all|right now))*"
    r"|cancel (?:everything|it all|all of it)"
    r"|i'?m done(?:\s+with\s+(?:it|this|that|everything|all of (?:this|it)"
    r"|(?:this|the)\s+(?:project|conversation|chat|session)))?)",
    re.I)


def _sentences(text):
    t = (text or "").replace("\u2019", "'")
    return [s.strip(" \t\n,") for s in re.split(r"[.!?;\n]+", t) if s.strip(" \t\n,")]


@dataclass
class ReleaseResult:
    released: bool
    text: str = ""
    cancelled: list = field(default_factory=list)
    still_pending: list = field(default_factory=list)
    elapsed_ms: float = 0.0
    path: str = "release.hard_path"


def is_release(text):
    parts = _sentences(text)
    return bool(parts) and all(_SENTENCE.fullmatch(p) for p in parts)


def handle(text, pending=None):
    """Return ReleaseResult. `pending` = list of (label, cancellable: bool)."""
    t0 = time.perf_counter()
    if not is_release(text):
        return ReleaseResult(released=False, elapsed_ms=(time.perf_counter() - t0) * 1000)
    pending = list(pending or [])
    cancelled = [label for label, ok in pending if ok]
    residual = [label for label, ok in pending if not ok]
    lines = ["Stopped. Nothing further will run from this session."]
    lines.append("Cancelled: " + (", ".join(cancelled) if cancelled else "nothing was running."))
    if residual:
        lines.append("Still pending outside my control: " + ", ".join(residual) + ".")
    else:
        lines.append("Nothing is still pending.")
    lines.append("You can come back any time; nothing is needed from you now.")
    r = ReleaseResult(released=True, text="\n".join(lines), cancelled=cancelled,
                      still_pending=residual)
    r.elapsed_ms = (time.perf_counter() - t0) * 1000
    return r
