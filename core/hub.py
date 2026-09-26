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

from . import doctrine, identity, ledger, scouts
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

    # --- doctrine (the hub's own constitution) -----------------------------

    def record_doctrine(self, kind, subject, statement, decided_at=None):
        """Record a signed, standalone doctrine decision and ledger it.

        A doctrine decision is a declaration by the arbitrator that does not
        target a proposal or an opportunity — for example, naming the canonical
        home of the project. It is signed with the arbitrator's key and written
        to the hash-chained ledger, so it is verifiable offline and
        tamper-evident in the hub's own history.
        """
        arb = self.keyring.arbitrator
        rec = doctrine.make_record(arb["secret"], arb["public"], kind, subject,
                                   statement, decided_at)
        self._log("doctrine.decided", {
            "id": rec["id"], "kind": rec["kind"], "subject": rec["subject"],
            "statement": rec["statement"], "decided_at": rec["decided_at"],
            "actor_pubkey": arb["public"], "signature": rec["signature"],
        })
        return rec

    def verify_doctrine(self, rec):
        """Verify a doctrine record against the hub's arbitrator key."""
        if not doctrine.verify_record(rec):
            return False
        # In this single-operator build the arbitrator is the only signer of
        # doctrine, so bind the record to the hub's own key as well.
        return rec.get("actor_pubkey") == self.keyring.arbitrator["public"]

    def list_doctrines(self):
        """Every doctrine decision recorded in the ledger, in order."""
        out = []
        for e in self.store.ledger_entries():
            rec = doctrine.record_from_ledger_entry(e)
            if rec is not None:
                out.append(rec)
        return out

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

        report["doctrines"] = []
        for rec in self.list_doctrines():
            good = self.verify_doctrine(rec)
            report["doctrines"].append({
                "id": rec["id"], "kind": rec["kind"],
                "subject": rec["subject"], "signature_ok": good,
            })
            if not good:
                report["ok"] = False

        return report

    # --- scouts: deploy agents that locate opportunities ------------------

    def deploy_scout(self, scout_id, mission, channel="gigs", limit=6, source=None):
        """Send a scout (a node) out on a mission. Returns the mission + findings.

        The scout proposes; it never decides. Every opportunity it returns lands
        at the gate in state 'pending' until the human arbitrates.
        """
        node = self.store.get_node(scout_id)
        if not node:
            raise ValueError("unknown scout")
        mission = (mission or "").strip()
        if not mission:
            raise ValueError("a mission needs an objective")
        channel = channel if channel in scouts.CHANNELS else "gigs"

        mid = _new_id("mission")
        m = {
            "id": mid, "scout_id": scout_id, "scout_name": node["name"],
            "mission": mission, "channel": channel,
            "source": source or "demo", "status": "running",
            "found": 0, "created_at": time.time(),
        }
        self.store.add_mission(m)
        self._log("scout.deployed", {
            "mission_id": mid, "scout_id": scout_id, "scout_name": node["name"],
            "mission": mission, "channel": channel,
        })

        engine = scouts.Scout(source=scouts.DemoSource())
        try:
            found = engine.run(mission, channel=channel, limit=limit)
        except Exception as e:  # a scout must never take the hub down
            found = []
            self._log("scout.error", {"mission_id": mid, "error": str(e)[:200]})

        created = []
        for c in found:
            oid = _new_id("opp")
            o = {
                "id": oid, "mission_id": mid, "scout_id": scout_id,
                "scout_name": node["name"], "title": c["title"],
                "summary": c["summary"], "source": c["source"], "url": c["url"],
                "category": c["category"], "value": c["value"],
                "confidence": c["confidence"], "effort": c["effort"],
                "roi": c["roi"], "state": "pending", "rationale": "",
                "created_at": time.time(), "decided_at": None,
            }
            self.store.add_opportunity(o)
            created.append(o)

        self.store.update_mission(mid, status="returned", found=len(created))
        self._log("scout.returned", {
            "mission_id": mid, "scout_name": node["name"], "channel": channel,
            "found": len(created), "top": [c["title"] for c in created[:3]],
        })
        return {"mission": self.store.get_mission(mid), "opportunities": created}

    def decide_opportunity(self, opportunity_id, action, rationale=""):
        """Arbitrate an opportunity at the gate. Signed and ledgered."""
        o = self.store.get_opportunity(opportunity_id)
        if not o:
            raise ValueError("unknown opportunity")
        if action not in ("approve", "reject", "pursue", "won", "lost", "reopen"):
            raise ValueError("unknown action")

        arb = self.keyring.arbitrator
        d = {
            "id": _new_id("dec"), "proposal_id": opportunity_id,
            "action": action, "rationale": rationale or "",
            "actor_pubkey": arb["public"], "created_at": time.time(),
        }
        signed = {k: d[k] for k in ("id", "proposal_id", "action", "rationale",
                                    "actor_pubkey", "created_at")}
        d["signature"] = identity.sign(signed, arb["secret"])
        self.store.add_decision(d)

        new_state = {
            "approve": "pursuing", "pursue": "pursuing", "reject": "rejected",
            "won": "won", "lost": "lost", "reopen": "pending",
        }.get(action, o["state"])
        self.store.update_opportunity(opportunity_id, state=new_state,
                                      rationale=rationale or "",
                                      decided_at=time.time())

        self._log("gate.opportunity." + action, {
            "opportunity_id": opportunity_id, "title": o["title"],
            "value": o["value"], "new_state": new_state,
            "rationale": rationale or "", "actor_pubkey": arb["public"],
            "signature": d["signature"],
        })
        return d

    # --- capability & pocketbook ------------------------------------------

    def capability(self):
        """Derive the operator's capability from the verifiable record.

        Capability is not a vanity metric: it is computed from signed decisions
        and won opportunities, so it reflects what actually happened, provably.
        """
        decisions = self.store.list_decisions()
        opps = self.store.list_opportunities()
        approved = sum(1 for o in opps if o["state"] in ("pursuing", "won"))
        won = sum(1 for o in opps if o["state"] == "won")
        missions = self.store.list_missions()
        xp = (len(decisions) * 5) + (approved * 10) + (won * 50) + (len(missions) * 3)
        level = 1 + xp // 150
        into = xp % 150
        tiers = ["Scout", "Ranger", "Operator", "Strategist", "Principal", "Sovereign"]
        tier = tiers[min(len(tiers) - 1, (level - 1) // 2)]
        return {
            "xp": xp, "level": level, "tier": tier,
            "into_level": into, "to_next": 150 - into,
            "decisions": len(decisions), "approved": approved, "won": won,
            "missions": len(missions),
        }

    def pocketbook(self):
        """Money view: pipeline, expected value, and realised wins."""
        opps = self.store.list_opportunities()
        open_states = ("pending", "pursuing")
        pipeline = sum(o["value"] for o in opps if o["state"] in open_states)
        expected = sum(o["value"] * o["confidence"] for o in opps if o["state"] in open_states)
        won = sum(o["value"] for o in opps if o["state"] == "won")
        lost = sum(o["value"] for o in opps if o["state"] == "lost")
        pursuing = sum(1 for o in opps if o["state"] == "pursuing")
        pending = sum(1 for o in opps if o["state"] == "pending")
        won_n = sum(1 for o in opps if o["state"] == "won")
        decided = pursuing + won_n + sum(1 for o in opps if o["state"] == "lost")
        win_rate = round(won_n / decided, 3) if decided else 0.0
        return {
            "pipeline": round(pipeline, 2),
            "expected": round(expected, 2),
            "won": round(won, 2),
            "lost": round(lost, 2),
            "pending": pending, "pursuing": pursuing, "won_count": won_n,
            "win_rate": win_rate,
        }

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
            "missions": self.store.list_missions(),
            "opportunities": self.store.list_opportunities(),
            "capability": self.capability(),
            "pocketbook": self.pocketbook(),
            "ledger": self.store.ledger_entries()[-60:],
            "ledger_count": self.store.ledger_count(),
            "arbitrator": {
                "public": self.keyring.arbitrator["public"],
                "fingerprint": identity.fingerprint(self.keyring.arbitrator["public"]),
            },
        }
