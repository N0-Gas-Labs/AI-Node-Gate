#!/usr/bin/env python3
"""server.py — the hub's self-hosted runtime.

A single-process HTTP server built on the Python standard library. It serves the
web interface from ./web and exposes a small JSON API over the hub. There is no
framework to install and no service to rent: run it on any machine you own.

Endpoints:
    GET    /api/state              full snapshot of the hub
    GET    /api/verify             verify ledger + signatures
    GET    /api/models             local model runtime status
    GET    /api/export             download a portable bundle
    POST   /api/nodes              register a node
    DELETE /api/nodes/<id>         remove a node
    POST   /api/proposals          submit a signed proposal
    POST   /api/arbitrate          arbitrate at the gate
    POST   /api/draft              draft a proposal with a local model
"""

import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from core import bundle as bundle_mod
from core import models
from core.hub import Hub, Keyring
from core.store import Store

HERE = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.join(HERE, "web")
HUB_DIR = os.path.join(HERE, ".ngg")
DB_PATH = os.path.join(HUB_DIR, "hub.db")
KEY_PATH = os.path.join(HUB_DIR, "keyring.json")

MIME = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".svg": "image/svg+xml",
    ".ico": "image/x-icon",
}

# Module-level hub handle (single-operator build).
_store = None
_hub = None
_model = models.LocalModel()


def get_hub():
    global _store, _hub
    if _hub is None:
        os.makedirs(HUB_DIR, exist_ok=True)
        _store = Store(DB_PATH)
        _hub = Hub(_store, Keyring(KEY_PATH))
        if _store.ledger_count() == 0:
            _hub._log("hub.initialised", {"version": "0.2.0", "mode": "sovereign"})
    return _hub


class Handler(BaseHTTPRequestHandler):
    server_version = "AINodeGate/0.2"

    # --- helpers -----------------------------------------------------------

    def _json(self, obj, status=200):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self):
        length = int(self.headers.get("Content-Length", 0) or 0)
        if not length:
            return {}
        try:
            return json.loads(self.rfile.read(length).decode("utf-8"))
        except ValueError:
            return {}

    def _serve_static(self, path):
        if path == "/" or path == "":
            path = "/index.html"
        # Redirect the app root to its trailing-slash form so relative asset
        # paths (css/, js/, icons/, sw.js) resolve inside /command/.
        if path == "/command":
            self.send_response(301)
            self.send_header("Location", "/command/")
            self.end_headers()
            return
        if path == "/command/":
            path = "/command/index.html"
        rel = path.lstrip("/")
        full = os.path.normpath(os.path.join(WEB_DIR, rel))
        if not full.startswith(WEB_DIR) or not os.path.isfile(full):
            self.send_error(404, "Not found")
            return
        ext = os.path.splitext(full)[1].lower()
        with open(full, "rb") as f:
            body = f.read()
        self.send_response(200)
        self.send_header("Content-Type", MIME.get(ext, "application/octet-stream"))
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        sys.stderr.write("[hub] " + (fmt % args) + "\n")

    # --- routing -----------------------------------------------------------

    def do_GET(self):
        path = urlparse(self.path).path
        hub = get_hub()
        if path == "/api/state":
            return self._json(hub.snapshot())
        if path == "/api/verify":
            return self._json(hub.verify_all())
        if path == "/api/models":
            return self._json({
                "endpoint": _model.endpoint,
                "model": _model.model,
                "available": _model.available(),
                "note": "Point the hub at your own runtime (Ollama / llama.cpp / LM Studio).",
            })
        if path == "/api/channels":
            from core import scouts as _scouts
            return self._json({
                "channels": [
                    {"id": k, "label": v["label"], "blurb": v["blurb"]}
                    for k, v in _scouts.CHANNELS.items()
                ]
            })
        if path == "/api/export":
            b = bundle_mod.export_bundle(hub.store, hub.keyring.arbitrator["public"])
            body = json.dumps(b, indent=2, sort_keys=True).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Disposition", "attachment; filename=ai-node-gate.bundle.json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        return self._serve_static(path)

    def do_POST(self):
        path = urlparse(self.path).path
        hub = get_hub()
        data = self._read_json()
        try:
            if path == "/api/nodes":
                node = hub.register_node(
                    data.get("name", "").strip() or "Unnamed",
                    data.get("role", "").strip(),
                    data.get("caps", []),
                )
                return self._json({"ok": True, "node": node})
            if path == "/api/proposals":
                p = hub.submit_proposal(
                    data.get("node_id"), data.get("title", "").strip(),
                    data.get("description", ""), data.get("target_id"),
                    data.get("priority", "med"), data.get("depends_on"),
                )
                return self._json({"ok": True, "proposal": p})
            if path == "/api/arbitrate":
                d = hub.arbitrate(data.get("proposal_id"), data.get("action"),
                                  data.get("rationale", ""))
                return self._json({"ok": True, "decision": d})
            if path == "/api/draft":
                node = hub.store.get_node(data.get("node_id"))
                if not node:
                    return self._json({"ok": False, "error": "unknown node"}, 400)
                text, source = models.draft_proposal(
                    _model, node["name"], node["role"], data.get("intent", "")
                )
                return self._json({"ok": True, "draft": text, "source": source})
            if path == "/api/scout/deploy":
                result = hub.deploy_scout(
                    data.get("scout_id"), data.get("mission", ""),
                    channel=data.get("channel", "gigs"),
                    limit=int(data.get("limit", 6) or 6),
                )
                return self._json({"ok": True, **result})
            if path == "/api/opportunity/decide":
                d = hub.decide_opportunity(
                    data.get("opportunity_id"), data.get("action"),
                    data.get("rationale", ""),
                )
                return self._json({"ok": True, "decision": d})
        except ValueError as e:
            return self._json({"ok": False, "error": str(e)}, 400)
        return self._json({"ok": False, "error": "not found"}, 404)

    def do_DELETE(self):
        path = urlparse(self.path).path
        hub = get_hub()
        if path.startswith("/api/nodes/"):
            node_id = path.rsplit("/", 1)[-1]
            ok = hub.delete_node(node_id)
            return self._json({"ok": ok})
        return self._json({"ok": False, "error": "not found"}, 404)


def run(host="127.0.0.1", port=8787):
    get_hub()
    httpd = ThreadingHTTPServer((host, port), Handler)
    print("AI-Node-Gate serving on http://%s:%d" % (host, port))
    print("Data: %s" % DB_PATH)
    print("Arbitrator key held in %s" % KEY_PATH)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        httpd.server_close()


if __name__ == "__main__":
    run(port=int(sys.argv[1]) if len(sys.argv) > 1 else 8787)
