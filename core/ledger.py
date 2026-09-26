"""Ledger — an append-only, tamper-evident record.

Every consequential event in the hub is written here. Each entry commits to the
hash of the entry before it, forming a chain: change or remove any entry and
every hash after it no longer matches, so the forgery is detectable by anyone
who holds the chain — not just by the hub. The ledger is the hub's memory and
its proof of honesty at the same time.

Entry hash = SHA-256( index || prev_hash || timestamp || kind || payload )

The genesis entry uses a prev_hash of 64 zeroes.
"""

import hashlib
import json

GENESIS_PREV = "0" * 64


def _entry_hash(index, prev_hash, ts, kind, payload_json):
    h = hashlib.sha256()
    h.update(str(index).encode("utf-8"))
    h.update(b"\x1f")
    h.update(prev_hash.encode("utf-8"))
    h.update(b"\x1f")
    h.update(ts.encode("utf-8"))
    h.update(b"\x1f")
    h.update(kind.encode("utf-8"))
    h.update(b"\x1f")
    h.update(payload_json.encode("utf-8"))
    return h.hexdigest()


def make_entry(index, prev_hash, ts, kind, payload):
    """Build a fully-formed ledger entry (dict) with its hash."""
    payload_json = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    digest = _entry_hash(index, prev_hash, ts, kind, payload_json)
    return {
        "index": index,
        "prev_hash": prev_hash,
        "ts": ts,
        "kind": kind,
        "payload": payload,
        "payload_json": payload_json,
        "hash": digest,
    }


def verify_chain(entries):
    """Verify a full ledger.

    Returns (ok: bool, problems: list[str]). Checks that indices are
    contiguous from 0, that each prev_hash links to the previous entry's hash,
    and that each entry's own hash recomputes correctly.
    """
    problems = []
    prev = GENESIS_PREV
    for i, e in enumerate(entries):
        if e["index"] != i:
            problems.append("entry %d: index is %s, expected %d" % (i, e["index"], i))
        if e["prev_hash"] != prev:
            problems.append("entry %d: prev_hash does not link to previous entry" % i)
        recomputed = _entry_hash(
            e["index"], e["prev_hash"], e["ts"], e["kind"], e["payload_json"]
        )
        if recomputed != e["hash"]:
            problems.append("entry %d: hash mismatch (entry was modified)" % i)
        prev = e["hash"]
    return (len(problems) == 0, problems)
