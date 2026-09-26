"""Doctrine — signed, standalone statements of record.

Most decisions in the hub target something concrete: a proposal, or an
opportunity a scout brought back. A *doctrine* decision is different. It is a
signed declaration by the arbitrator that does not point at a proposal at all.
It is how the hub records its own constitution — which repository is the
canonical home, which rules carry forward, what is under security hold.

A doctrine record is deliberately self-contained and self-verifying: it carries
the statement, the signer's public key, and the signature over the canonical
bytes of the statement. Anyone can check it offline, with nothing but this
repository and the Python standard library, without holding any private key and
without trusting the machine that produced it. The same record is also written
to the hash-chained ledger, so it is tamper-evident in the hub's own history.
"""

import json
import os
import time

from . import identity

DOCTRINE_FORMAT = "ai-node-gate/doctrine@1"

# The fields that are covered by the signature, in canonical order. Keeping this
# list explicit means the signed surface is obvious and stable.
_SIGNED_FIELDS = (
    "format", "id", "kind", "subject", "statement", "decided_at", "actor_pubkey",
)


def _signed_view(record):
    return {k: record[k] for k in _SIGNED_FIELDS}


def make_record(secret_hex, public_hex, kind, subject, statement, decided_at=None):
    """Build and sign a doctrine record. Returns the record dict."""
    record = {
        "format": DOCTRINE_FORMAT,
        "id": "doc-" + os.urandom(6).hex(),
        "kind": kind,
        "subject": subject,
        "statement": statement,
        "decided_at": decided_at if decided_at is not None else time.time(),
        "actor_pubkey": public_hex,
    }
    record["signature"] = identity.sign(_signed_view(record), secret_hex)
    return record


def verify_record(record):
    """Verify a doctrine record offline. Returns True/False."""
    if not isinstance(record, dict) or record.get("format") != DOCTRINE_FORMAT:
        return False
    try:
        signed = _signed_view(record)
        return identity.verify(signed, record["signature"], record["actor_pubkey"])
    except (KeyError, TypeError, ValueError):
        return False


def record_from_ledger_entry(entry):
    """Reconstruct a doctrine record from a `doctrine.decided` ledger entry.

    This lets a bundle's doctrine decisions be re-verified from the ledger alone.
    """
    if entry.get("kind") != "doctrine.decided":
        return None
    raw = entry.get("payload")
    if raw is None:
        try:
            raw = json.loads(entry.get("payload_json") or "{}")
        except (ValueError, TypeError):
            return None
    p = raw or {}
    return {
        "format": DOCTRINE_FORMAT,
        "id": p.get("id"),
        "kind": p.get("kind"),
        "subject": p.get("subject"),
        "statement": p.get("statement"),
        "decided_at": p.get("decided_at"),
        "actor_pubkey": p.get("actor_pubkey"),
        "signature": p.get("signature"),
    }
