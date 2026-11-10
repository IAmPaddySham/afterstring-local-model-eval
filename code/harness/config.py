"""Paths and config loading. No secrets are read here."""
import hashlib
import os
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
AFTERSTRING_ROOT = PROJECT_ROOT.parents[4]             # ~/afterstring (read-only from here)
CONFIGS = PROJECT_ROOT / "configs"
MODELS_YAML = CONFIGS / "models.yaml"
RULES_YAML = CONFIGS / "filter" / "rules-v0.yaml"
RULES_PIN = CONFIGS / "filter" / "rules-v0.sha256"
GATE_YAML = CONFIGS / "gate-v0.yaml"               # adapter numbers (D-014)
FULL_PROMPTS = {"v0": CONFIGS / "prompts" / "full-v0.txt",   # Paddy-reviewed v0 (D-015), kept unchanged
                "v1": CONFIGS / "prompts" / "full-v1.txt",   # warmth + sources lines (D-017); selectable, not default (D-023)
                "v2": CONFIGS / "prompts" / "full-v2.txt",   # 2026-10-27 draft: v1 warmth + no-memory, refusal, plain-No rules; pending Paddy review
                "v3": CONFIGS / "prompts" / "full-v3.txt",   # D-046 draft wired opt-in (D-048); not default (D-023)
                "v4": CONFIGS / "prompts" / "full-v4.txt",   # D-053: v0 + warmth-first, validation-No, sources, fresh-yes-after-stop; opt-in, not default
                "v5": CONFIGS / "prompts" / "full-v5.txt",   # D-055: copy of notes/2026-11-03-full-v5-DRAFT.txt (5310a45d); opt-in, not default
                "v5.1": CONFIGS / "prompts" / "full-v5.1.txt",  # D-056: copy of notes/2026-11-03-full-v5.1-DRAFT.txt (0323f092); opt-in, not default
                "v5.2": CONFIGS / "prompts" / "full-v5.2.txt",   # D-059: copy of notes/2026-11-04-full-v5.2-DRAFT.txt (ab928b95); opt-in, not default
                "v5.2.1": CONFIGS / "prompts" / "full-v5.2.1.txt",  # D-061
                "v5.2.3": CONFIGS / "prompts" / "full-v5.2.3.txt",  # D-063
                "v5.2.4": CONFIGS / "prompts" / "full-v5.2.4.txt",  # D-064
                "v5.2.5": CONFIGS / "prompts" / "full-v5.2.5.txt",  # D-065
                "v5.2.6": CONFIGS / "prompts" / "full-v5.2.6.txt",  # D-067
                "v5.2.7": CONFIGS / "prompts" / "full-v5.2.7.txt",  # D-068
                "v5.2.8": CONFIGS / "prompts" / "full-v5.2.8.txt"}  # D-070: no-guilt exit, q != Release; no quote dead-end; opt-in, not default
DEFAULT_PROMPT_VERSION = "v0"   # D-023: back to v0 until v1/v2 beat it under blind grading
FULL_PROMPT = FULL_PROMPTS[DEFAULT_PROMPT_VERSION]
CRISIS_YAML = CONFIGS / "safety" / "crisis-v3.yaml"     # fixed crisis resources (D-016, D-026, D-069; v1 and v2 kept unchanged)
CRISIS_PIN = CONFIGS / "safety" / "crisis-v3.sha256"
RETRIEVAL_ALLOWLIST = CONFIGS / "retrieval" / "allowlist-v0.txt"   # D-019
RETRIEVAL_MANIFEST = CONFIGS / "retrieval" / "manifest-v0.json"
# D-043: run option `--retrieval v1` selects manifest v1 (D-041) for one run; v0 stays the default.
# D-050: `--retrieval v2` = v1's 11 paths, gate "always" (MIN_SCORE filters), top_k 5; opt-in only.
RETRIEVAL_MANIFESTS = {"v0": RETRIEVAL_MANIFEST,
                       "v1": CONFIGS / "retrieval" / "manifest-v1.json",
                       "v2": CONFIGS / "retrieval" / "manifest-v2.json"}
DEFAULT_RETRIEVAL_VERSION = "v0"
EVAL_ITEMS = PROJECT_ROOT / "evals" / "drafts" / "2026-10-25-eval-items-v0.md"
RUNS = PROJECT_ROOT / "runs"


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_models():
    with open(MODELS_YAML) as f:
        return yaml.safe_load(f)


def model_entry(model_id=None):
    cfg = load_models()
    mid = model_id or cfg["default"]
    if mid not in cfg["models"]:
        raise KeyError(f"unknown model id {mid!r}; see configs/models.yaml")
    entry = dict(cfg["models"][mid])
    entry["id"] = mid
    entry["local_path"] = os.path.expanduser(entry["local_path"])
    return entry


def load_gate_config(path=None):
    """Adapter numbers (D-014). Missing file or key raises: no silent defaults for a gate."""
    with open(path or GATE_YAML) as f:
        cfg = yaml.safe_load(f)
    for k in ("confirmation_ttl_s", "approval_ceiling_60min", "gate_timeout_s"):
        if k not in cfg:
            raise KeyError(f"{k!r} missing from {path or GATE_YAML}")
    return cfg
