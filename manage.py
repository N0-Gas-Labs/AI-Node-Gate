#!/usr/bin/env python3
"""manage.py — the operator's command line for the sovereign hub.

Everything an owner needs to run their hub without a single external service:

    python3 manage.py init                 create a fresh hub (db + keys)
    python3 manage.py serve                run the hub on your machine
    python3 manage.py verify               verify the ledger and all signatures
    python3 manage.py export out.json      export a portable, verifiable bundle
    python3 manage.py import out.json      import and verify a bundle
    python3 manage.py node add NAME ROLE   register a node
    python3 manage.py node list            list nodes and their fingerprints
    python3 manage.py propose ...          submit a signed proposal
    python3 manage.py gate ID approve      arbitrate a proposal
"""

import argparse
import json
import os
import sys

from core import bundle as bundle_mod
from core import identity
from core.hub import Hub, Keyring
from core.store import Store


HUB_DIR = ".ngg"
DB_PATH = os.path.join(HUB_DIR, "hub.db")
KEY_PATH = os.path.join(HUB_DIR, "keyring.json")


def open_hub():
    if not os.path.exists(DB_PATH):
        print("No hub found here. Run: python3 manage.py init", file=sys.stderr)
        sys.exit(1)
    store = Store(DB_PATH)
    keyring = Keyring(KEY_PATH)
    return store, Hub(store, keyring)


# --- commands --------------------------------------------------------------

def cmd_init(args):
    os.makedirs(HUB_DIR, exist_ok=True)
    store = Store(DB_PATH)
    keyring = Keyring(KEY_PATH)
    hub = Hub(store, keyring)
    if store.is_new or store.ledger_count() == 0:
        hub._log("hub.initialised", {"version": "0.2.0", "mode": "sovereign"})
    print("Hub ready at %s" % DB_PATH)
    print("Arbitrator key: %s" % identity.fingerprint(hub.keyring.arbitrator["public"]))
    print("Keys held in %s (chmod 600). Keep it safe; it is your authority." % KEY_PATH)
    store.close()


def cmd_serve(args):
    from server import run
    run(host=args.host, port=args.port)


def cmd_verify(args):
    store, hub = open_hub()
    report = hub.verify_all()
    print(json.dumps(report, indent=2))
    store.close()
    sys.exit(0 if report["ok"] else 2)


def cmd_export(args):
    store, hub = open_hub()
    b = bundle_mod.export_bundle(store, hub.keyring.arbitrator["public"])
    bundle_mod.write_bundle(args.path, b)
    print("Exported %d ledger entries to %s" % (b["manifest"]["ledger_count"], args.path))
    print("Public hash: %s" % b["manifest"]["public_hash"])
    store.close()


def cmd_import(args):
    b = bundle_mod.read_bundle(args.path)
    report = bundle_mod.verify_bundle(b)
    print("Bundle verification: %s" % ("OK" if report["ok"] else "FAILED"))
    print(json.dumps(report, indent=2))
    if not report["ok"] and not args.force:
        print("Refusing to import an unverified bundle (use --force to override).", file=sys.stderr)
        sys.exit(2)
    store = Store(DB_PATH)
    bundle_mod.import_into_store(store, b)
    print("Imported into %s" % DB_PATH)
    store.close()


def cmd_node(args):
    store, hub = open_hub()
    if args.node_action == "add":
        caps = [c.strip() for c in (args.caps or "").split(",") if c.strip()]
        node = hub.register_node(args.name, args.role, caps)
        print("Registered %s (%s) fp=%s" % (node["name"], node["id"], identity.fingerprint(node["pubkey"])))
    elif args.node_action == "list":
        for n in store.list_nodes():
            print("%-10s %-12s %-10s %s" % (n["name"], n["id"], n["status"], identity.fingerprint(n["pubkey"])))
    store.close()


def cmd_propose(args):
    store, hub = open_hub()
    p = hub.submit_proposal(args.node_id, args.title, args.description or "",
                            target_id=args.target, priority=args.priority,
                            depends_on=args.depends_on)
    print("Proposal %s submitted and signed by node %s" % (p["id"], p["node_id"]))
    store.close()


def cmd_gate(args):
    store, hub = open_hub()
    d = hub.arbitrate(args.proposal_id, args.action, rationale=args.rationale or "")
    print("Decision %s: %s on %s" % (d["id"], args.action, args.proposal_id))
    store.close()


# --- parser ----------------------------------------------------------------

def build_parser():
    p = argparse.ArgumentParser(description="AI-Node-Gate operator CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("init", help="create a fresh hub").set_defaults(func=cmd_init)

    s = sub.add_parser("serve", help="run the hub")
    s.add_argument("--host", default="127.0.0.1")
    s.add_argument("--port", type=int, default=8787)
    s.set_defaults(func=cmd_serve)

    sub.add_parser("verify", help="verify ledger and signatures").set_defaults(func=cmd_verify)

    s = sub.add_parser("export", help="export a portable bundle")
    s.add_argument("path")
    s.set_defaults(func=cmd_export)

    s = sub.add_parser("import", help="import a bundle")
    s.add_argument("path")
    s.add_argument("--force", action="store_true")
    s.set_defaults(func=cmd_import)

    s = sub.add_parser("node", help="manage nodes")
    s.add_argument("node_action", choices=["add", "list"])
    s.add_argument("name", nargs="?")
    s.add_argument("role", nargs="?")
    s.add_argument("--caps", default="")
    s.set_defaults(func=cmd_node)

    s = sub.add_parser("propose", help="submit a signed proposal")
    s.add_argument("node_id")
    s.add_argument("title")
    s.add_argument("--description", default="")
    s.add_argument("--target", default=None)
    s.add_argument("--priority", default="med", choices=["high", "med", "low"])
    s.add_argument("--depends-on", dest="depends_on", default=None)
    s.set_defaults(func=cmd_propose)

    s = sub.add_parser("gate", help="arbitrate a proposal")
    s.add_argument("proposal_id")
    s.add_argument("action", choices=["approve", "reject", "amend", "delegate", "start", "complete", "reopen"])
    s.add_argument("--rationale", default="")
    s.set_defaults(func=cmd_gate)

    return p


def main():
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
