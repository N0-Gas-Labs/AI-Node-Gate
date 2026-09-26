"""Bundle — portable, verifiable export of the entire hub.

Sovereignty means the hub is not trapped in one place. A bundle is a single
JSON file containing every node, proposal, decision, and ledger entry, plus a
manifest hash over the whole thing. Anyone can take the bundle to a machine
with nothing but Python installed, import it, and verify that the ledger chain
and every signature still hold — without needing the private keys, and without
trusting the machine that produced it.

The manifest hash covers the public record (ledger + public keys), so tampering
with the exported history is detectable offline.
"""

import hashlib
import json

from . import ledger


BUNDLE_FORMAT = "ai-node-gate/bundle@1"


def _hash_public(store):
    """Hash the public record: the ledger chain and public keys."""
    h = hashlib.sha256()
    for e in store.ledger_entries():
        h.update(e["hash"].encode("utf-8"))
    for n in store.list_nodes():
        h.update((n["id"] + ":" + (n["pubkey"] or "")).encode("utf-8"))
    for d in store.list_decisions():
        h.update((d["id"] + ":" + (d["signature"] or "")).encode("utf-8"))
    return h.hexdigest()


def export_bundle(store, arbitrator_public):
    """Build a portable bundle dict from a store."""
    bundle = {
        "format": BUNDLE_FORMAT,
        "manifest": {
            "public_hash": _hash_public(store),
            "ledger_count": store.ledger_count(),
        },
        "arbitrator_public": arbitrator_public,
        "nodes": store.list_nodes(),
        "proposals": store.list_proposals(),
        "decisions": store.list_decisions(),
        "ledger": store.ledger_entries(),
    }
    return bundle


def write_bundle(path, bundle):
    with open(path, "w") as f:
        json.dump(bundle, f, indent=2, sort_keys=True)
    return path


def read_bundle(path):
    with open(path, "r") as f:
        return json.load(f)


def verify_bundle(bundle):
    """Verify a bundle offline: chain integrity, manifest, and signatures.

    Returns a report dict. Signature checks re-derive the canonical payloads
    from the bundle itself, so no external state is needed.
    """
    report = {"ok": True, "ledger": {}, "manifest": {}, "proposals": [], "decisions": []}

    ok, problems = ledger.verify_chain(bundle.get("ledger", []))
    report["ledger"] = {"ok": ok, "problems": problems, "entries": len(bundle.get("ledger", []))}
    if not ok:
        report["ok"] = False

    # manifest recomputation
    h = hashlib.sha256()
    for e in bundle.get("ledger", []):
        h.update(e["hash"].encode("utf-8"))
    for n in bundle.get("nodes", []):
        h.update((n["id"] + ":" + (n.get("pubkey") or "")).encode("utf-8"))
    for d in bundle.get("decisions", []):
        h.update((d["id"] + ":" + (d.get("signature") or "")).encode("utf-8"))
    recomputed = h.hexdigest()
    expected = bundle.get("manifest", {}).get("public_hash")
    report["manifest"] = {"ok": recomputed == expected, "recomputed": recomputed, "expected": expected}
    if recomputed != expected:
        report["ok"] = False

    # signatures
    from . import identity
    nodes_by_id = {n["id"]: n for n in bundle.get("nodes", [])}
    for p in bundle.get("proposals", []):
        node = nodes_by_id.get(p["node_id"])
        payload = {
            "id": p["id"], "title": p["title"], "description": p["description"],
            "node_id": p["node_id"], "target_id": p["target_id"],
            "priority": p["priority"], "depends_on": p["depends_on"],
            "created_at": p["created_at"],
        }
        good = bool(node) and identity.verify(payload, p["signature"], node["pubkey"])
        report["proposals"].append({"id": p["id"], "signature_ok": good})
        if not good:
            report["ok"] = False

    for d in bundle.get("decisions", []):
        signed = {k: d[k] for k in ("id", "proposal_id", "action", "rationale", "actor_pubkey", "created_at")}
        good = identity.verify(signed, d["signature"], d["actor_pubkey"])
        report["decisions"].append({"id": d["id"], "signature_ok": good})
        if not good:
            report["ok"] = False

    return report


def import_into_store(store, bundle):
    """Load a verified bundle into an (ideally empty) store."""
    for n in bundle.get("nodes", []):
        store.conn.execute(
            "INSERT OR REPLACE INTO nodes(id,name,role,caps,status,pubkey,created_at) "
            "VALUES(:id,:name,:role,:caps,:status,:pubkey,:created_at)",
            {**n, "caps": n.get("caps") if isinstance(n.get("caps"), str) else json.dumps(n.get("caps") or [])},
        )
    for p in bundle.get("proposals", []):
        store.conn.execute(
            "INSERT OR REPLACE INTO proposals(id,title,description,node_id,target_id,"
            "priority,depends_on,state,signature,created_at) VALUES(:id,:title,:description,"
            ":node_id,:target_id,:priority,:depends_on,:state,:signature,:created_at)", p,
        )
    for d in bundle.get("decisions", []):
        store.conn.execute(
            "INSERT OR REPLACE INTO decisions(id,proposal_id,action,rationale,"
            "actor_pubkey,signature,created_at) VALUES(:id,:proposal_id,:action,"
            ":rationale,:actor_pubkey,:signature,:created_at)", d,
        )
    for e in bundle.get("ledger", []):
        store.conn.execute(
            "INSERT OR REPLACE INTO ledger(idx,prev_hash,ts,kind,payload_json,hash) "
            "VALUES(:index,:prev_hash,:ts,:kind,:payload_json,:hash)", e,
        )
    store.conn.commit()
