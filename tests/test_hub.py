#!/usr/bin/env python3
"""Self-contained test suite for the sovereign hub. Standard library only.

Run:  python3 tests/test_hub.py
"""

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import bundle as bundle_mod
from core import ed25519, identity, ledger
from core.hub import Hub, Keyring
from core.store import Store

PASS = 0
FAIL = 0


def check(name, cond):
    global PASS, FAIL
    if cond:
        PASS += 1
        print("  ok   %s" % name)
    else:
        FAIL += 1
        print("  FAIL %s" % name)


def test_crypto():
    print("crypto")
    sk, pk = identity.generate_keypair()
    obj = {"b": 2, "a": 1, "nested": {"x": [1, 2, 3]}}
    sig = identity.sign(obj, sk)
    check("valid signature verifies", identity.verify(obj, sig, pk))
    check("tampered object fails", not identity.verify({"a": 1, "b": 3, "nested": {"x": [1, 2, 3]}}, sig, pk))
    sk2, pk2 = identity.generate_keypair()
    check("wrong key fails", not identity.verify(obj, sig, pk2))
    check("canonical is order-independent",
          identity.canonical({"a": 1, "b": 2}) == identity.canonical({"b": 2, "a": 1}))


def test_ledger():
    print("ledger")
    e0 = ledger.make_entry(0, ledger.GENESIS_PREV, "t0", "genesis", {"x": 1})
    e1 = ledger.make_entry(1, e0["hash"], "t1", "next", {"y": 2})
    ok, probs = ledger.verify_chain([e0, e1])
    check("valid chain verifies", ok and not probs)
    bad = [dict(e0), dict(e1)]
    bad[1]["payload_json"] = bad[1]["payload_json"] + " "
    ok2, probs2 = ledger.verify_chain(bad)
    check("modified entry detected", not ok2 and len(probs2) >= 1)
    broken = [dict(e0), dict(e1)]
    broken[1]["prev_hash"] = "0" * 64
    ok3, probs3 = ledger.verify_chain(broken)
    check("broken link detected", not ok3)


def test_hub_flow():
    print("hub flow")
    tmp = tempfile.mkdtemp()
    store = Store(os.path.join(tmp, "hub.db"))
    keyring = Keyring(os.path.join(tmp, "keyring.json"))
    hub = Hub(store, keyring)

    n = hub.register_node("Atlas", "Planner", ["plan", "route"])
    check("node registered", n["name"] == "Atlas" and n["pubkey"])

    p = hub.submit_proposal(n["id"], "Do the thing", "desc", priority="high")
    check("proposal signed on submit", bool(p["signature"]))
    check("proposal signature verifies", hub.verify_proposal(store.get_proposal(p["id"])))

    d = hub.arbitrate(p["id"], "approve", rationale="yes")
    check("decision signed", bool(d["signature"]))
    check("decision verifies", hub.verify_decision(d))
    check("proposal state updated", store.get_proposal(p["id"])["state"] == "approved")

    report = hub.verify_all()
    check("full verification passes", report["ok"])

    # bundle round-trip (exported from an untampered hub)
    b = bundle_mod.export_bundle(store, keyring.arbitrator["public"])
    check("bundle verifies", bundle_mod.verify_bundle(b)["ok"])
    b["ledger"][0]["payload_json"] = b["ledger"][0]["payload_json"] + " "
    check("tampered bundle fails", not bundle_mod.verify_bundle(b)["ok"])

    # tamper with the stored proposal and confirm verification fails
    store.conn.execute("UPDATE proposals SET title='FORGED' WHERE id=?", (p["id"],))
    store.conn.commit()
    check("forged proposal fails verification", not hub.verify_proposal(store.get_proposal(p["id"])))

    store.close()


if __name__ == "__main__":
    test_crypto()
    test_ledger()
    test_hub_flow()
    print("\n%d passed, %d failed" % (PASS, FAIL))
    sys.exit(1 if FAIL else 0)
