# Canonical Home — the signed decision

> **Status: recorded, signed, and verifiable.** This is the hub's own decision that
> `N0-Gas-Labs/AI-Node-Gate` is the canonical home of the project, and that the prior
> organization is historical reference only. It was recorded as a **doctrine decision**
> — a signed, standalone statement written to the hash-chained ledger — and the
> evidence is committed alongside this file so anyone can verify it offline.

## The decision

| Field | Value |
|---|---|
| Kind | `canonical-home` |
| Subject | `N0-Gas-Labs/AI-Node-Gate` |
| Record id | `doc-7a756893ecb3` |
| Decided at | 2026-09-26T19:03:04Z (epoch `1790449384.158539`) |
| Signed by (arbitrator fingerprint) | `997438a68a4818cb` |
| Arbitrator public key | `5013387d1465d06e4bb44a980504b28e0ce5fa8463d79d12a97360af2d5313fd` |

The signed statement, verbatim:

> The canonical home of this project is the repository **N0-Gas-Labs/AI-Node-Gate**. The
> prior organization **No-Gas-Labs-Official** (94 repositories) is historical reference
> only: its doctrine and capability are absorbed here as memory, its finance and
> blockchain material remains under **security hold**, and its Featherstone repositories
> remain **archived**. Nothing is bulk-recreated. The founding rule carries forward
> unchanged: **autonomous nodes propose; a human decides at the gate; every decision is
> signed and recorded.**

## The evidence

Two files sit beside this document. Together they make the decision checkable without
trusting this repository's authors, and without any private key:

- [`canonical-home.decision.json`](canonical-home.decision.json) — the signed doctrine
  record itself: the statement, the signer's public key, and the Ed25519 signature over
  the canonical bytes of the record. It is self-verifying.
- [`canonical-home.evidence.json`](canonical-home.evidence.json) — a portable **bundle**
  of the hub that recorded the decision: the full ledger (the genesis entry and the
  `doctrine.decided` entry), the public keys, and a manifest hash over the public record.
  Bundle public hash: `046b8588aaa2499097ef52ef2117e37b0d0fd4c241e0153471922c86f14a535e`.

## How to verify it offline

Verification needs nothing but this repository and the Python standard library — no
network, no `pip install`, no private key. From the repository root:

```bash
# 1. verify the standalone signed record
python3 manage.py verify-doctrine docs/legacy/canonical-home.decision.json

# 2. verify the portable bundle: hash chain, manifest, and every signature
python3 manage.py verify-bundle docs/legacy/canonical-home.evidence.json
```

Both commands print `OK` and exit `0` when the evidence is intact. If any byte of the
statement, the signature, or the ledger is altered, they print `FAILED` and exit `2`. To
see the same check inside a running hub, `python3 manage.py verify` reports doctrine
decisions alongside proposals and decisions.

## How this decision was made

The decision was recorded with the hub's own mechanism, not asserted in prose:

```bash
python3 manage.py doctrine canonical-home "N0-Gas-Labs/AI-Node-Gate" \
    --statement-file statement.txt \
    --export docs/legacy/canonical-home.decision.json
python3 manage.py export docs/legacy/canonical-home.evidence.json
```

The signing key is a dedicated **evidence key** generated for this record, so the
fingerprint above is the identity that signed *this* decision. An operator running their
own hub can re-record the same decision with their own key — the record format, the
signature scheme, and the verification commands are identical. That is the point: the
decision is portable, and the proof travels with it.

## Why a doctrine decision

The prior organization's first working principle was *one official home per product*. A
principle is only a principle once it is recorded. This hub's whole reason to exist is
that **decisions are signed and recorded** — so the decision that names the hub's own
home is recorded the same way as any other: signed by the arbitrator, written to the
append-only ledger, and verifiable by anyone. The memory of the prior world lives in
[`../LEGACY_PORTFOLIO.md`](../LEGACY_PORTFOLIO.md) and the documents in this directory;
the decision that this is where it now lives is here, and it is signed.
