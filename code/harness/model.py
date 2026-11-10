"""Model backends. The model writes text only; nothing it outputs is authorization."""
import os
import re
import time
from dataclasses import dataclass, field, asdict

from . import config

THINK_RE = re.compile(r"<\|channel\>.*?<channel\|>", re.S)   # Gemma 4 thinking channel
STRAY_RE = re.compile(r"<\|?(channel|think|turn)\|?>|<turn\|>|<channel\|>")


@dataclass
class GenResult:
    text: str
    raw_text: str = ""
    prompt_tokens: int = 0
    generation_tokens: int = 0
    prompt_tps: float = 0.0
    generation_tps: float = 0.0
    peak_memory_gb: float = 0.0
    finish_reason: str = ""
    elapsed_s: float = 0.0
    thinking: str = ""      # how thinking was handled for this call
    backend: str = ""

    def to_dict(self):
        return asdict(self)


class ModelBackend:
    name = "abstract"
    loaded = False

    def generate(self, messages, max_tokens=400) -> GenResult:  # pragma: no cover
        raise NotImplementedError

    def identity(self) -> dict:
        return {"backend": self.name}


class NullModel(ModelBackend):
    """No-model mode (REQ-038): the harness runs end to end with no model loaded."""
    name = "null"
    TEXT = "[no model loaded: the harness ran in no-model mode; nothing was generated]"

    def generate(self, messages, max_tokens=400):
        return GenResult(text=self.TEXT, raw_text=self.TEXT, finish_reason="null",
                         thinking="n/a (no model)", backend=self.name)

    def identity(self):
        return {"backend": "null", "model": None}


class MLXBackend(ModelBackend):
    """mlx-lm backend, loading the pinned snapshot from configs/models.yaml.

    Decoding is greedy (temperature 0) by default so runs are deterministic. D-027: use_sampling()
    switches to the recommended sampling in configs/models.yaml with a recorded seed; use_greedy()
    switches back. Thinking: the chat template is called
    with enable_thinking=False; the rendered prompt is checked for the <|think|>
    switch, and any <|channel>…<channel|> block in the output is stripped and logged.
    """
    name = "mlx"

    def __init__(self, model_id=None):
        from mlx_lm import load
        from mlx_lm.sample_utils import make_sampler
        self.entry = config.model_entry(model_id)
        path = self.entry["local_path"]
        if not os.path.isdir(path):
            raise FileNotFoundError(f"pinned snapshot not found: {path}")
        if os.path.basename(path.rstrip("/")) != self.entry["revision"]:
            raise ValueError("snapshot folder does not match the pinned revision")
        self.path = path
        self.model, self.tokenizer = load(path)
        self._make_sampler = make_sampler
        self.sampler = make_sampler(temp=0.0)
        self.decoding = "greedy (temp 0)"
        self.loaded = True
        self.thinking_method = self._check_template()

    def use_greedy(self):
        self.sampler = self._make_sampler(temp=0.0)
        self.decoding = "greedy (temp 0)"

    def use_sampling(self, seed, settings=None):
        """D-027: sample with the pinned recommended settings; the seed makes it repeatable."""
        import mlx.core as mx
        st = settings or self.entry["sampling"]
        mx.random.seed(int(seed))
        self.sampler = self._make_sampler(temp=float(st["temperature"]), top_p=float(st.get("top_p", 0.0)),
                                          top_k=int(st.get("top_k", 0)))
        self.decoding = f"sampled (temp {st['temperature']}, top_p {st.get('top_p')}, top_k {st.get('top_k')}, seed {seed})"

    def _check_template(self):
        probe = [{"role": "user", "content": "probe"}]
        try:
            off = self.tokenizer.apply_chat_template(probe, add_generation_prompt=True,
                                                     tokenize=False, enable_thinking=False)
            on = self.tokenizer.apply_chat_template(probe, add_generation_prompt=True,
                                                    tokenize=False, enable_thinking=True)
        except TypeError:
            return "template has no enable_thinking flag; output stripping only"
        if "<|think|>" in off:
            return "enable_thinking=False ignored by template; output stripping only"
        if "<|think|>" in on:
            return "chat template enable_thinking=False (verified: <|think|> absent); output stripping as backup"
        return "chat template enable_thinking=False (no <|think|> switch seen either way); output stripping as backup"

    def render(self, messages):
        return self.tokenizer.apply_chat_template(messages, add_generation_prompt=True,
                                                  tokenize=False, enable_thinking=False)

    def generate(self, messages, max_tokens=400):
        from mlx_lm import stream_generate
        prompt = self.render(messages)
        t0 = time.perf_counter()
        raw, last = [], None
        for r in stream_generate(self.model, self.tokenizer, prompt, max_tokens=max_tokens,
                                 sampler=self.sampler):
            raw.append(r.text)
            last = r
        elapsed = time.perf_counter() - t0
        raw_text = "".join(raw)
        text, method = raw_text, self.thinking_method
        if THINK_RE.search(text):
            text = THINK_RE.sub("", text)
            method += "; THINKING BLOCK FOUND AND STRIPPED"
        if STRAY_RE.search(text):
            text = STRAY_RE.sub("", text)
            method += "; stray control tokens stripped"
        return GenResult(
            text=text.strip(), raw_text=raw_text,
            prompt_tokens=getattr(last, "prompt_tokens", 0),
            generation_tokens=getattr(last, "generation_tokens", 0),
            prompt_tps=float(getattr(last, "prompt_tps", 0.0)),
            generation_tps=float(getattr(last, "generation_tps", 0.0)),
            peak_memory_gb=float(getattr(last, "peak_memory", 0.0)),
            finish_reason=str(getattr(last, "finish_reason", "")),
            elapsed_s=elapsed, thinking=method, backend=self.name)

    def identity(self):
        e = self.entry
        return {"backend": "mlx", "model_id": e["id"], "repo": e["repo"], "revision": e["revision"],
                "weights_sha256_pinned": e["weights"]["sha256"], "local_path": e["local_path"],
                "decoding": "greedy (temp 0) + optional seeded samples (D-027)",
                "sampling": e.get("sampling"), "thinking": self.thinking_method}
