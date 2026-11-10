# configs/

Planned layout (nothing here yet):
- `model/<name>.yaml`: model id, revision or Ollama digest, quantization, chat template, sampling, context length, weight sha256 (ADR-0004)
- `lora/recipe.yaml`: one LoRA recipe with values looked up by model size
- `data/<name>.manifest.json`: per-file path, sha256, bytes, licence, include reason
- `optics/rules.yaml`: T0 filter rules (ADR-0005)
Pin every version. Never put secrets here.

In use now (harness v0): `models.yaml` (pinned builds), `filter/rules-v0.yaml` + `filter/rules-v0.sha256` (input guard, OR-01…OR-15), `prompts/full-v0.txt` (full-mode instructions, Paddy-reviewed v0, D-015; the file is sent to the model verbatim, so its status is recorded here and in DECISIONS, not inside it), `gate-v0.yaml` (adapter numbers: 120 s confirmation window, 10 approvals/hour ceiling — Paddy-approved v0, D-014; may increase later as the project scales and passes validation).

Added 2026-10-26 late: `prompts/full-v1.txt` (default full prompt, warmth + Sources lines, D-017; select v0 with `--prompt v0`), `safety/crisis-v1.yaml` + `safety/crisis-v1.sha256` (fixed crisis resources, D-016), `retrieval/allowlist-v0.txt` + `retrieval/manifest-v0.json` (retrieval v0 sources pinned by sha256, D-019; rebuild with `.venv/bin/python -m harness.retrieval --build`).
