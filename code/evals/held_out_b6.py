"""B6-only sealed loader; no model imports, grading, key generation or output writes.

The immutable packet's historical PENDING lines are superseded solely by the
exact externally approved seal and adopted freeze below. Never print its body.
Runtime inputs are verified before model construction; old B1-B5 loaders are untouched.
"""
import hashlib
import re
from pathlib import Path

from harness import config
from evals.held_out_b2 import _prompt

ROOT = Path(config.PROJECT_ROOT)
WRAPPER = ROOT.parent
PACKET = WRAPPER / "B6_SEALED_ITEMS_2026-11-07"
HELD_OUT_B6 = PACKET / "B6_ITEMS_DRAFT.md"
APPROVAL = PACKET / "APPROVAL_AND_SEAL_2026-11-07.md"
MANIFEST = PACKET / "SHA256SUMS"
FREEZE = WRAPPER / "B6_FREEZE_ADOPTED_2026-11-07.md"
ITEMS_SHA256 = "06ba30dc27843ed0dd1195976eae55fcf452bd0b4395158f8f9d62abd0c6fbe1"
ITEMS_BYTES = 21970
APPROVAL_SHA256 = "c6ded7468a446c368d3cccde8453bd1325c5ba4fac1d565790b5a45e78e6f30a"
MANIFEST_SHA256 = "3bf1a639291f86b3361e11181e1618c408624cfc6741a28e95282e1f549d00fa"
FREEZE_SHA256 = "ef0cb9376567fd40d859a16ef792aaf3ccdbfbb702f2cff2f27b4807c3797e2b"
IDS = tuple(f"B6-{i:02d}" for i in range(1, 19))
MODEL_ID = "gemma4-e4b-it-4bit-mlx"
MODEL_REPO = "mlx-community/gemma-4-e4b-it-4bit"
MODEL_REVISION = "475b9088d29754a3379866cf5aeb6b41acd313c2"
WEIGHTS_SHA256 = "932b8271fc3fe65adcc78b96c10c6268bbfb13e8f67d1358727c0d6ee97e1eff"
SAMPLING = {"temperature": 1.0, "top_p": 0.95, "top_k": 64}
# The adopted document remains unchanged. This named slice authorizes only the
# runner old->new delta, explicitly recorded in B6_LOADER_IMPLEMENTATION receipt.
FROZEN_FILES = {
    "configs/prompts/full-v0.txt": "a4de3c9fd69098802a84247892150df57dc3e631e92392c76d6b0ff1185adc69",
    "configs/prompts/full-v5.2.8.txt": "62962ab3fed18dd305bccf2d274f5f8335cc3b13f6236511d302baf721e8fa62",
    "configs/safety/crisis-v3.yaml": "890878f167fb6e1dec2425bca48a39361e1b7fb81ae04813e01f85a4a562f6e7",
    "configs/retrieval/manifest-v0.json": "621be560f4acb068e77bd654853bc858bc9ac7121f5bbe011dade8db73ead1fa",
    "configs/retrieval/allowlist-v0.txt": "c68f2093ebdf88a81b316faf1b32fb01e523942e854d7a867e750f8ed6e531ea",
    "configs/models.yaml": "ec751e5b15e5c28539fcb1031dc65a471b8282979a6817eecccb9577ad489184",
    "harness/config.py": "1c6a84d30a04e625f52753343d3e5af19996c5dc78ec4beec365aa7a5b1ec1af",
    "evals/run.py": "5cc1fa2961d3da566d5502d1c2883f08d626388cc36bf8d254c8f0edc4e59b1b",
    "evals/preflight_b6.py": "f2d35de6f7c8c77c983485f1b71b338eab92aba1bd3b903a3291c269d00051c5",
    "harness/release.py": "f3617de225b7d4e5e90442b07e38d751ab54a34053d1233809780e2ab7050396",
    "harness/pipeline.py": "73187c159e30d7ea280a6c15ed7cc351bc327fa27d8453f33845f224f48f1835",
    "requirements.lock": "beb8a07421fc3adbc745d3495b6b8827b1fa863a8a3aa5d0e5bf522bc4ef11f6",
    "docs/DECISIONS.md": "aa226cfb6e2c28516e3fb477c5bee60d3e27aa754b9552707b47662ab4dc3493",
    "evals/grading/README.md": "db54f8d6aac2a9184ce06bb278c56ff6fdb2779a3ebc924040bc4e18229eed6c",
    "../PROSPECTIVE_FREEZE_v0_2026-11-06.md": "ae39957881ccb32161bf789a707bcffb78e3692d254dd1eef0ea1d0a35972895",
    "../B6_FREEZE_ADOPTED_2026-11-07.md": FREEZE_SHA256,
}


class NotApproved(ValueError):
    """A seal/format mismatch: messages deliberately contain no packet content."""


def _read_pinned(path, expected):
    try:
        data = path.read_bytes()
    except OSError:
        raise NotApproved("B6 required sealed file unavailable") from None
    if hashlib.sha256(data).hexdigest() != expected:
        raise NotApproved("B6 sealed hash mismatch")
    return data


def load():
    """Read only the exact externally approved packet; never accept another path."""
    _read_pinned(FREEZE, FREEZE_SHA256)
    _read_pinned(APPROVAL, APPROVAL_SHA256)
    manifest = _read_pinned(MANIFEST, MANIFEST_SHA256).decode("utf-8")
    expected = {f"{PACKET.name}/{HELD_OUT_B6.name}": ITEMS_SHA256,
                f"{PACKET.name}/{APPROVAL.name}": APPROVAL_SHA256}
    entries = []
    for line in manifest.splitlines():
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) != 2 or expected.get(parts[1]) != parts[0]:
            raise NotApproved("B6 invalid seal manifest")
        entries.append(parts[1])
    if len(entries) != 2 or set(entries) != set(expected):
        raise NotApproved("B6 incomplete or duplicate seal manifest")
    data = _read_pinned(HELD_OUT_B6, ITEMS_SHA256)
    if len(data) != ITEMS_BYTES:
        raise NotApproved("B6 sealed size mismatch")
    blocks = re.split(r"^### ", data.decode("utf-8"), flags=re.M)[1:]
    ids = []
    for block in blocks:
        m = re.fullmatch(r"(B6-\d{2})\s+·\s+Model", block.splitlines()[0].strip())
        if not m:
            raise NotApproved("B6 invalid item header")
        ids.append(m.group(1))
    if tuple(ids) != IDS:
        raise NotApproved("B6 missing, duplicate, unexpected or unordered IDs")
    out = []
    for hid, block in zip(ids, blocks):
        for name in ("Prompt / setup", "Retrieval manifest"):
            if len(re.findall(rf"^- {re.escape(name)}: ", block, re.M)) != 1:
                raise NotApproved("B6 missing or duplicate required field")
        manifest = re.search(r"^- Retrieval manifest: (.*)$", block, re.M).group(1).strip()
        if manifest not in ("v0", "none"):
            raise NotApproved("B6 incompatible retrieval manifest")
        try:
            words, note = _prompt(hid, block)
        except ValueError:
            raise NotApproved("B6 invalid quoted user/setup format") from None
        if not words.strip():
            raise NotApproved("B6 empty user words")
        out.append({"id": hid, "kind": "Model", "text": words,
                    "context_note": note, "manifest": manifest})
    return out


def validate_frozen_inputs(model_id=None):
    """Future run preflight: hash adopted inputs and local weights, never load MLX.

    Stub tests replace every path and model entry with fictional temp fixtures.
    This does not grant run authority and does not implement any grading rule.
    """
    for name, pin in FROZEN_FILES.items():
        try:
            actual = config.sha256_file(ROOT / name)
        except OSError:
            raise NotApproved("B6 frozen input unavailable") from None
        if actual != pin:
            raise NotApproved("B6 frozen input hash mismatch")
    entry = config.model_entry(model_id)
    weights = entry.get("weights", {})
    if (entry.get("id") != MODEL_ID or entry.get("repo") != MODEL_REPO
            or entry.get("revision") != MODEL_REVISION or entry.get("sampling") != SAMPLING
            or weights.get("file") != "model.safetensors" or weights.get("sha256") != WEIGHTS_SHA256
            or Path(entry.get("local_path", "")).name != MODEL_REVISION):
        raise NotApproved("B6 incompatible model/decoding pins")
    path = Path(entry["local_path"]) / weights["file"]
    try:
        valid = path.stat().st_size == weights.get("bytes") and config.sha256_file(path) == WEIGHTS_SHA256
    except OSError:
        valid = False
    if not valid:
        raise NotApproved("B6 local weight hash/size mismatch")
    return {"files": dict(FROZEN_FILES), "model_repo": MODEL_REPO,
            "model_revision": MODEL_REVISION, "weights_sha256_verified": WEIGHTS_SHA256,
            "sampling": dict(SAMPLING)}
