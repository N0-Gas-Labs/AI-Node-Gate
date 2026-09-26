"""Hub — the coordination and arbitration logic.

This module is where the sovereignty model becomes concrete:

* Nodes have real identities. Each node's proposals are signed with its key and
  verified against its public key before the hub will accept them.
* The human arbitrator has its own key. Every decision is signed, so the record
  shows not just what was decided but who decided it, provably.
* Every state change is written to the hash-chained ledger.

The hub stores public keys for verification and keeps private keys in a keyring
file the operator owns. In this single-operator build the hub signs on the
operator's behalf; the architecture keeps signing and verification separate so
that a hardened deployment can move signing to the operator's own device
without changing the record format.
"""

import json
import os
import threading
import time

from . import identity, ledger
from .store import utc_now_iso


def _new_id(prefix):
    return "%s-%s" % (prefix, os.urandom(6).hex())


class Keyring:
    """A file of private keys, owned by the operator."""

    def __init__(self, path):
        self.path = path
        self.data = {"arbitrator": None, "nodes": {}}
        if os.path.exists(path):
            with open(path, "r") as f:
                self.data = json.load(f)
        self.data.setdefault("nodes", {})

    def save(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "w") as f:
            json.dump(self.data, f, indent=2)
        os.chmod(self.path, 0o600)

    def ensure_arbitrator(self):
        if not self.data.get("arbitrator"):
            sk, pk = identity.generate_keypair()
            self.data["arbitrator"] = {"secret": sk, "public": pk}
            self.save()
        return self.data["arbitrator"]

    @property
    def arbitrator(self):
        return self.data["arbitrator"]

    def add_node(self, node_id):
        sk, pk = identity.generate_keypair()
        self.data["nodes"][node_id] = {"secret": sk, "public": pk}
        self.save()
        return self.data["nodes"][node_id]

    def node(self, node_id):
        return self.data["nodes"].get(node_id)


class Hub:
    def __init__(self, store, keyring):
        self.store = store
        self.keyring = keyring
        self._lock = threading.RLock()
        self.keyring.ensure_arbitrator()

    # --- ledger helper -----------------------------------------------------

    def _log(self, kind, payload):
        with self._lock:
            tip = self.store.ledger_tip()
            index = 0 if tip is None else tip["index"] + 1
            prev = ledger.GENESIS_PREV if tip is None else tip["hash"]
            entry = ledger.make_entry(index, prev, utc_now_iso(), kind, payload)
            self.store.append_ledger(entry)
            return entry

    # --- nodes -------------------------------------------------------------

    def register_node(self, name, role, caps):
        node_id = _new_id("node")
        keys = self.keyring.add_node(node_id)
        node = {
            "id": node_id,
            "name": name,
            "role": role or "",
            "caps": json.dumps(caps or []),
            "status": "idle",
            "pubkey": keys["public"],
            "created_at": time.time(),
        }
        self.store.add_node(node)
        self._log("node.registered", {
            "id": node_id, "name": name, "role": role or "",
            "caps": caps or [], "pubkey": keys["public"],
        })
        return self.store.get_node(node_id)

    def delete_node(self, node_id):
        node = self.store.get_node(node_id)
        if not node:
            return False
        self.store.delete_node(node_id)
        self._log("node.removed", {"id": node_id, "name": node["name"]})
        return True

    # --- proposals ---------------------------------------------------------

    def _proposal_payload(self, p):
        return {
            "id": p["id"], "title": p["title"], "description": p["description"],
            "node_id": p["node_id"], "target_id": p["target_id"],
            "priority": p["priority"], "depends_on": p["depends_on"],
            "created_at": p["created_at"],
        }

    def submit_proposal(self, node_id, title, description, target_id=None,
                        priority="med", depends_on=None):
        node = self.store.get_node(node_id)
        if not node:
            raise ValueError("unknown node")
        keys = self.keyring.node(node_id)
        if not keys:
            raise ValueError("node has no signing key")

        p = {
            "id": _new_id("prop"),
            "title": title,
            "description": description or "",
            "node_id": node_id,
            "target_id": target_id or None,
            "priority": priority,
            "depends_on": depends_on or None,
            "state": "pending",
            "signature": None,
            "created_at": time.time(),
        }
        payload = self._proposal_payload(p)
        p["signature"] = identity.sign(payload, keys["secret"])
        self.store.add_proposal(p)
        self._log("proposal.submitted", {
            "id": p["id"], "title": title, "node_id": node_id,
            "node_name": node["name"], "priority": priority,
            "target_id": target_id, "depends_on": depends_on,
            "signature": p["signature"], "pubkey": node["pubkey"],
        })
        return self.store.get_proposal(p["id"])

    def verify_proposal(self, p):
        node = self.store.get_node(p["node_id"])
        if not node:
            return False
        payload = {
            "id": p["id"], "title": p["title"], "description": p["description"],
            "node_id": p["node_id"], "target_id": p["target_id"],
            "priority": p["priority"], "depends_on": p["depends_on"],
            "created_at": p["created_at"],
        }
        return identity.verify(payload, p["signature"], node["pubkey"])

    # --- arbitration (the gate) -------------------------------------------

    def arbitrate(self, proposal_id, action, rationale=""):
        p = self.store.get_proposal(proposal_id)
        if not p:
            raise ValueError("unknown proposal")
        if action not in ("approve", "reject", "amend", "delegate", "start", "complete", "reopen"):
            raise ValueError("unknown action")

        arb = self.keyring.arbitrator
        d = {
            "id": _new_id("dec"),
            "proposal_id": proposal_id,
            "action": action,
            "rationale": rationale or "",
            "actor_pubkey": arb["public"],
            "created_at": time.time(),
        }
        signed = {k: d[k] for k in ("id", "proposal_id", "action", "rationale", "actor_pubkey", "created_at")}
        d["signature"] = identity.sign(signed, arb["secret"])
        self.store.add_decision(d)

        new_state = {
            "approve": "approved", "reject": "rejected", "amend": "pending",
            "start": "in_progress", "complete": "done", "reopen": "pending",
        }.get(action)
        if action == "delegate":
            new_state = p["state"]
        if new_state:
            self.store.update_proposal(proposal_id, state=new_state)

        self._log("gate." + action, {
            "proposal_id": proposal_id, "title": p["title"],
            "rationale": rationale or "", "actor_pubkey": arb["public"],
            "signature": d["signature"], "new_state": new_state,
        })
        return d

    def verify_decision(self, d):
        signed = {k: d[k] for k in ("id", "proposal_id", "action", "rationale", "actor_pubkey", "created_at")}
        return identity.verify(signed, d["signature"], d["actor_pubkey"])

    # --- integrity ---------------------------------------------------------

    def verify_all(self):
        """Verify the ledger chain and every signature in the hub."""
        report = {"ledger": {}, "proposals": [], "decisions": [], "ok": True}

        ok, problems = ledger.verify_chain(self.store.ledger_entries())
        report["ledger"] = {"ok": ok, "problems": problems, "entries": self.store.ledger_count()}
        if not ok:
            report["ok"] = False

        for p in self.store.list_proposals():
            good = self.verify_proposal(p)
            report["proposals"].append({"id": p["id"], "title": p["title"], "signature_ok": good})
            if not good:
                report["ok"] = False

        for d in self.store.list_decisions():
            good = self.verify_decision(d)
            report["decisions"].append({"id": d["id"], "action": d["action"], "signature_ok": good})
            if not good:
                report["ok"] = False

        return report

    # --- views -------------------------------------------------------------

    def snapshot(self):
        nodes = self.store.list_nodes()
        for n in nodes:
            try:
                n["caps"] = json.loads(n["caps"] or "[]")
            except (ValueError, TypeError):
                n["caps"] = []
            n["fingerprint"] = identity.fingerprint(n["pubkey"]) if n["pubkey"] else None
        proposals = self.store.list_proposals()
        return {
            "nodes": nodes,
            "proposals": proposals,
            "decisions": self.store.list_decisions(),
            "ledger": self.store.ledger_entries()[-60:],
            "ledger_count": self.store.ledger_count(),
            "arbitrator": {
                "public": self.keyring.arbitrator["public"],
                "fingerprint": identity.fingerprint(self.keyring.arbitrator["public"]),
            },
        }
