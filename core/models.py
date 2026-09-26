"""Models — compute sovereignty.

A node is only as sovereign as the model behind it. This adapter lets a node be
backed by a model running on hardware you control, reached over a plain local
HTTP endpoint. It speaks the widely-supported Ollama / llama.cpp-server style
API (POST /api/generate), so it works with any runtime that exposes that shape:
Ollama, llama.cpp's server, LocalAI, LM Studio, and others.

If no local runtime is reachable, the hub falls back to a built-in deterministic
drafter so the system is always demonstrable and never depends on a network. The
point is not the fallback — it is that the *default* is your own machine.
"""

import json
import urllib.request
import urllib.error


DEFAULT_ENDPOINT = "http://127.0.0.1:11434"  # Ollama's default


class LocalModel:
    """A handle to a model running on infrastructure you own."""

    def __init__(self, endpoint=DEFAULT_ENDPOINT, model="llama3", timeout=30):
        self.endpoint = endpoint.rstrip("/")
        self.model = model
        self.timeout = timeout

    def available(self):
        """Return True if the runtime answers a lightweight request."""
        try:
            req = urllib.request.Request(
                self.endpoint + "/api/tags", method="GET"
            )
            with urllib.request.urlopen(req, timeout=3) as r:
                return r.status == 200
        except (urllib.error.URLError, OSError, ValueError):
            return False

    def generate(self, prompt, system=None):
        """Ask the local model to complete a prompt. Returns (text, source)."""
        body = {"model": self.model, "prompt": prompt, "stream": False}
        if system:
            body["system"] = system
        data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(
            self.endpoint + "/api/generate",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                payload = json.loads(r.read().decode("utf-8"))
            text = payload.get("response", "").strip()
            if text:
                return text, "local:" + self.model
        except (urllib.error.URLError, OSError, ValueError, KeyError):
            pass
        return self._fallback(prompt), "fallback:deterministic"

    def _fallback(self, prompt):
        """A dependency-free drafter so the hub never hard-fails."""
        topic = prompt.strip().splitlines()[0][:120] if prompt.strip() else "the task"
        return (
            "DRAFT (offline)\n"
            "Objective: %s\n"
            "Steps: 1) clarify scope  2) gather inputs  3) produce a first pass  "
            "4) submit to the gate for arbitration.\n"
            "Note: no local model runtime was reachable; this is a deterministic "
            "placeholder. Point the hub at your own runtime to draft with a real "
            "model." % topic
        )


def draft_proposal(model, node_name, node_role, intent):
    """Compose a proposal draft from a node's perspective."""
    system = (
        "You are %s, a %s node inside a human-arbitrated coordination hub. "
        "Propose a concrete, well-scoped plan. Be brief and specific."
        % (node_name, node_role or "general")
    )
    prompt = "Intent: %s\n\nWrite a short proposal (a title line, then 2-4 sentences)." % intent
    return model.generate(prompt, system=system)
