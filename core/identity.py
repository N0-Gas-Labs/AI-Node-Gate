"""Identity — keys, canonical serialisation, and signatures.

Every actor in the hub (each node, and the human arbitrator) has an Ed25519
keypair. A node signs its proposals; the arbitrator signs its decisions. The
hub stores only public keys, so it can verify authorship without ever holding
the private key that produced it. This is what makes the record trustworthy
without trusting the hub itself.

Canonical JSON is the load-bearing detail: to sign an object we must be able to
reproduce its exact bytes later. We serialise with sorted keys, no whitespace,
and ASCII escaping so that the same logical object always hashes to the same
bytes regardless of how it was assembled.
"""

import json
import os
import base64

from . import ed25519


# --- key material ----------------------------------------------------------

def generate_keypair():
    """Return (secret_hex, public_hex)."""
    sk = os.urandom(32)
    pk = ed25519.publickey(sk)
    return sk.hex(), pk.hex()


def public_from_secret(sk_hex):
    return ed25519.publickey(bytes.fromhex(sk_hex)).hex()


# --- canonical serialisation ----------------------------------------------

def canonical(obj):
    """Deterministic bytes for any JSON-serialisable object."""
    return json.dumps(
        obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")


def fingerprint(public_hex):
    """A short, human-readable identifier derived from a public key."""
    import hashlib
    return hashlib.sha256(bytes.fromhex(public_hex)).hexdigest()[:16]


# --- signing ---------------------------------------------------------------

def sign(obj, sk_hex):
    """Sign a canonicalised object, returning a base64 signature string."""
    pk = ed25519.publickey(bytes.fromhex(sk_hex))
    sig = ed25519.signature(canonical(obj), bytes.fromhex(sk_hex), pk)
    return base64.b64encode(sig).decode("ascii")


def verify(obj, sig_b64, public_hex):
    """Verify a base64 signature over a canonicalised object."""
    if not sig_b64 or not public_hex:
        return False
    try:
        sig = base64.b64decode(sig_b64)
        pk = bytes.fromhex(public_hex)
    except (ValueError, TypeError):
        return False
    return ed25519.verify(canonical(obj), sig, pk)
