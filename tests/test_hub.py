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


def test_scouts_and_opportunities():
    print("scouts + opportunities")
    tmp = tempfile.mkdtemp()
    store = Store(os.path.join(tmp, "hub.db"))
    keyring = Keyring(os.path.join(tmp, "keyring.json"))
    hub = Hub(store, keyring)

    # ROI scoring is bounded and monotonic in value/confidence
    from core import scouts
    lo = scouts.roi_score(1000, 0.5, "med")
    hi = scouts.roi_score(100000, 0.9, "low")
    check("roi score bounded 0..100", 0 <= lo <= 100 and 0 <= hi <= 100)
    check("roi higher for bigger value", hi > lo)
    check("channels exposed", "gigs" in scouts.CHANNELS and "grants" in scouts.CHANNELS)

    scout = hub.register_node("Vega", "Scout", ["hunt", "report"])
    res = hub.deploy_scout(scout["id"], "Find paid AI automation work", channel="gigs", limit=5)
    mission = res["mission"]
    opps = res["opportunities"]
    check("mission created", mission["status"] == "returned" and mission["channel"] == "gigs")
    check("opportunities returned", len(opps) >= 1)
    check("opportunities scored + sorted",
          all(0 <= o["roi"] <= 100 for o in opps)
          and all(opps[i]["roi"] >= opps[i + 1]["roi"] for i in range(len(opps) - 1)))
    check("opportunity starts pending", opps[0]["state"] == "pending")

    # decide at the gate: signed + ledgered
    d = hub.decide_opportunity(opps[0]["id"], "approve", rationale="worth pursuing")
    check("decision signed", bool(d["signature"]))
    check("decision verifies", hub.verify_decision(d))
    check("opportunity state -> pursuing", store.get_opportunity(opps[0]["id"])["state"] == "pursuing")

    hub.decide_opportunity(opps[0]["id"], "won", rationale="closed the deal")
    check("opportunity state -> won", store.get_opportunity(opps[0]["id"])["state"] == "won")

    # capability + pocketbook derive from the signed record
    cap = hub.capability()
    check("capability has level + tier", cap["level"] >= 1 and bool(cap["tier"]))
    check("capability counts the won deal", cap["won"] >= 1 and cap["decisions"] >= 2)

    pk = hub.pocketbook()
    check("pocketbook counts won value", pk["won_count"] >= 1 and pk["won"] > 0)
    check("pocketbook win_rate in 0..1", 0.0 <= pk["win_rate"] <= 1.0)

    # integrity still holds after scout + decision activity
    report = hub.verify_all()
    check("full verification passes after scouting", report["ok"])

    snap = hub.snapshot()
    check("snapshot exposes missions/opportunities/capability/pocketbook",
          "missions" in snap and "opportunities" in snap
          and "capability" in snap and "pocketbook" in snap)

    store.close()


if __name__ == "__main__":
    test_crypto()
    test_ledger()
    test_hub_flow()
    test_scouts_and_opportunities()
    print("\n%d passed, %d failed" % (PASS, FAIL))
    sys.exit(1 if FAIL else 0)
