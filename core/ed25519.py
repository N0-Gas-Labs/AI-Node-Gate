"""Pure-Python Ed25519 — public-key signatures with zero external dependencies.

Sovereignty means not renting your trust from a package registry. This is a
compact, self-contained implementation of the Ed25519 signature scheme
(Edwards-curve Digital Signature Algorithm over Curve25519), adapted from the
well-known public-domain reference implementation by Daniel J. Bernstein and
others. It is slow compared to a native library but correct, auditable, and
dependency-free — which is exactly the trade this project is willing to make.

Keys:
    secret key  = 32 random bytes
    public key  = 32 bytes, derived from the secret key

Signatures are 64 bytes. Verification needs only the public key.
"""

import hashlib

# Curve constants -----------------------------------------------------------
p = 2 ** 255 - 19
q = 2 ** 252 + 27742317777372353535851937790883648493


def _H(m):
    return hashlib.sha512(m).digest()


def _expmod(b, e, m):
    if e == 0:
        return 1
    t = _expmod(b, e // 2, m) ** 2 % m
    if e & 1:
        t = (t * b) % m
    return t


def _inv(x):
    return _expmod(x, p - 2, p)


_d = -121665 * _inv(121666) % p
_I = _expmod(2, (p - 1) // 4, p)


def _xrecover(y):
    xx = (y * y - 1) * _inv(_d * y * y + 1)
    x = _expmod(xx, (p + 3) // 8, p)
    if (x * x - xx) % p != 0:
        x = (x * _I) % p
    if x % 2 != 0:
        x = p - x
    return x


_By = 4 * _inv(5) % p
_Bx = _xrecover(_By)
_B = [_Bx % p, _By % p]


def _edwards(P, Q):
    x1, y1 = P
    x2, y2 = Q
    x3 = (x1 * y2 + x2 * y1) * _inv(1 + _d * x1 * x2 * y1 * y2)
    y3 = (y1 * y2 + x1 * x2) * _inv(1 - _d * x1 * x2 * y1 * y2)
    return [x3 % p, y3 % p]


def _scalarmult(P, e):
    # iterative to avoid deep recursion on 254-bit scalars
    Q = [0, 1]
    while e > 0:
        if e & 1:
            Q = _edwards(Q, P)
        P = _edwards(P, P)
        e >>= 1
    return Q


def _encodepoint(P):
    x, y = P
    bits = [(y >> i) & 1 for i in range(255)] + [x & 1]
    return bytes(sum(bits[i * 8 + j] << j for j in range(8)) for i in range(32))


def _bit(h, i):
    return (h[i // 8] >> (i % 8)) & 1


def _Hint(m):
    return int(_H(m).hex(), 16)


def _encodeint(y):
    return y.to_bytes(32, "little")


def _decodeint(s):
    return int.from_bytes(s, "little")


def _decodepoint(s):
    y = _decodeint(s) & ((1 << 255) - 1)
    x = _xrecover(y)
    if (x & 1) != (_decodeint(s) >> 255) & 1:
        x = p - x
    P = [x, y]
    if not _isedwards(P):
        raise ValueError("point is not on the curve")
    return P


def _isedwards(P):
    x, y = P
    return (-x * x + y * y - 1 - _d * x * x * y * y) % p == 0


# Public API ----------------------------------------------------------------

def publickey(sk: bytes) -> bytes:
    """Derive the 32-byte public key from a 32-byte secret key."""
    h = _H(sk)
    a = 2 ** 254 + sum(2 ** i * _bit(h, i) for i in range(3, 254))
    return _encodepoint(_scalarmult(_B, a))


def signature(m: bytes, sk: bytes, pk: bytes) -> bytes:
    """Produce a 64-byte signature of message m under secret key sk."""
    h = _H(sk)
    a = 2 ** 254 + sum(2 ** i * _bit(h, i) for i in range(3, 254))
    r = _Hint(h[32:64] + m) % q
    R = _scalarmult(_B, r)
    S = (r + _Hint(_encodepoint(R) + pk + m) * a) % q
    return _encodepoint(R) + _encodeint(S)


def verify(m: bytes, sig: bytes, pk: bytes) -> bool:
    """Return True iff sig is a valid signature of m under public key pk."""
    if len(sig) != 64 or len(pk) != 32:
        return False
    try:
        R = _decodepoint(sig[:32])
        S = _decodeint(sig[32:])
        h = _Hint(_encodepoint(R) + pk + m)
        A = _decodepoint(pk)
    except (ValueError, IndexError):
        return False
    if S >= q:
        return False
    return _scalarmult(_B, S) == _edwards(R, _scalarmult(A, h))
