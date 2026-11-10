"""Approvals ledger (REQ-042, D-033): a real count of human approvals, kept on disk for one run.

- One JSON object per line, append-only. Each line carries `h`, the sha256 of the previous line's `h`
  plus this record (a hash chain), so an edited, dropped or reordered line is detected.
- Record types: `header` (first line), `approval` (a human ConfirmationEvent was received) and
  `revoke` (a human withdrew a confirmation).
- `count(now)` = approvals with now - window_s < t <= now. The window and the ceiling come from
  configs/gate-v0.yaml (D-014: 10 per 60 min, Paddy-approved v0; `approval_window_s` = 3600).
- Fail closed: a missing, unreadable or corrupt ledger, a broken chain, an unknown record type,
  timestamps going backwards or a record from the future raise ApprovalsUnavailable. Callers turn
  that into HOLD for any consequential action. Nothing here ever grants anything.
- Every read re-reads the file from disk, so the effect-time executor (REQ-041) sees revocations
  written after the gate decided.
"""
import hashlib
import json
import os
import time
from pathlib import Path

from . import config

TYPES = ("header", "approval", "revoke")
_FUTURE_SKEW_S = 5.0   # a record more than this far in the future means the clock or file is wrong


class ApprovalsUnavailable(Exception):
    """The approvals count can't be trusted. Callers must HOLD, never PERMIT."""


def window_from_config(cfg=None):
    cfg = cfg or config.load_gate_config()
    if "approval_window_s" not in cfg:
        raise KeyError("'approval_window_s' missing from configs/gate-v0.yaml")
    return float(cfg["approval_window_s"])


def _canon(rec):
    return json.dumps({k: v for k, v in rec.items() if k != "h"}, sort_keys=True, separators=(",", ":"))


def _link(prev_h, rec):
    return hashlib.sha256((prev_h + "\n" + _canon(rec)).encode()).hexdigest()


class ApprovalsLedger:
    def __init__(self, path, window_s=None, clock=time.time, create=True):
        self.path = Path(path)
        self.window_s = float(window_s) if window_s is not None else window_from_config()
        self.clock = clock
        if create and not self.path.exists():
            self._append({"type": "header", "version": 1, "t": float(self.clock()),
                          "window_s": self.window_s}, prev_h="")

    # ---- reading (always from disk) ----
    def records(self):
        try:
            with open(self.path, encoding="utf-8") as f:
                lines = f.read().splitlines()
        except Exception as e:
            raise ApprovalsUnavailable(f"ledger unreadable: {type(e).__name__}")
        if not lines:
            raise ApprovalsUnavailable("ledger empty (no header)")
        out, prev_h, last_t = [], "", None
        for i, ln in enumerate(lines, 1):
            try:
                rec = json.loads(ln)
            except Exception:
                raise ApprovalsUnavailable(f"ledger line {i} is not JSON")
            if not isinstance(rec, dict) or rec.get("type") not in TYPES:
                raise ApprovalsUnavailable(f"ledger line {i} has an unknown record type")
            if (i == 1) != (rec["type"] == "header"):
                raise ApprovalsUnavailable(f"ledger line {i}: header must be first and only first")
            t = rec.get("t")
            if isinstance(t, bool) or not isinstance(t, (int, float)):
                raise ApprovalsUnavailable(f"ledger line {i} has no valid time")
            if last_t is not None and t < last_t:
                raise ApprovalsUnavailable(f"ledger line {i}: time goes backwards")
            if rec.get("h") != _link(prev_h, rec):
                raise ApprovalsUnavailable(f"ledger line {i}: hash chain broken")
            if rec["type"] != "header" and not rec.get("id"):
                raise ApprovalsUnavailable(f"ledger line {i} has no confirmation id")
            prev_h, last_t = rec["h"], t
            out.append(rec)
        return out

    def count(self, now=None, exclude_id=None):
        """Human approvals in the window ending at `now` (REQ-042)."""
        now = float(self.clock() if now is None else now)
        n = 0
        for r in self.records():
            if r["t"] > now + _FUTURE_SKEW_S:
                raise ApprovalsUnavailable("ledger has a record from the future")
            if r["type"] == "approval" and r["id"] != exclude_id and now - self.window_s < r["t"] <= now:
                n += 1
        return n

    def approval(self, conf_id):
        hits = [r for r in self.records() if r["type"] == "approval" and r["id"] == conf_id]
        if len(hits) > 1:
            raise ApprovalsUnavailable(f"confirmation {conf_id!r} recorded more than once")
        return hits[0] if hits else None

    def is_revoked(self, conf_id):
        return any(r["type"] == "revoke" and r["id"] == conf_id for r in self.records())

    # ---- writing (append only) ----
    def _append(self, rec, prev_h=None):
        if prev_h is None:
            prev_h = self.records()[-1]["h"]   # also verifies the whole chain first
        rec = dict(rec)
        rec["h"] = _link(prev_h, rec)
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, sort_keys=True, separators=(",", ":")) + "\n")
            f.flush()
            os.fsync(f.fileno())
        return rec

    def record_approval(self, conf_id, action_hash, confirmed_at=None, t=None):
        """t = when the harness received the yes (ledger order); confirmed_at = when the human said it."""
        if self.approval(conf_id) is not None:
            raise ApprovalsUnavailable(f"confirmation {conf_id!r} already recorded (a yes is single-use)")
        t = float(self.clock() if t is None else t)
        return self._append({"type": "approval", "id": str(conf_id), "action_hash": action_hash, "t": t,
                             "confirmed_at": float(t if confirmed_at is None else confirmed_at)})

    def revoke(self, conf_id, t=None):
        return self._append({"type": "revoke", "id": str(conf_id),
                             "t": float(self.clock() if t is None else t)})

    def sha256(self):
        return config.sha256_file(self.path) if self.path.exists() else None
