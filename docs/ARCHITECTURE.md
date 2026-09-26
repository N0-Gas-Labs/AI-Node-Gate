# Architecture

## Overview

AI-Node-Gate is a self-hosted coordination hub with four moving parts: nodes, proposals, the gate, and the ledger. Nodes are the participants. Proposals are the things they want to do. The gate is where a human decides. The ledger is where everything is remembered — verifiably. The hub runs as a single Python process with no external dependencies, stores everything in one SQLite file, and exposes a small JSON API to a web console.

The design goal is not scale. It is ownership: a system you can read end to end, run on your own machine, and prove honest without trusting anyone.

## The runtime

The hub is a single process, started with `python3 server.py` or `python3 manage.py serve`. It is built on `http.server` from the Python standard library and serves two things: the static web console from `web/`, and a JSON API under `/api/`. There is no framework and no build step. The operator's command line, `manage.py`, drives the same core directly for scripting and administration.

```
web/  ──HTTP──▶  server.py  ──▶  core/hub.py  ──▶  core/store.py  ──▶  .ngg/hub.db
   ▲                                  │
   └──────────── JSON ────────────────┘        core/ledger.py  (hash chain)
                                                core/identity.py (Ed25519)
                                                core/models.py   (local models)
                                                core/bundle.py   (portable proof)
```

## Nodes

A node is one autonomous participant, described by a name, a role, a set of capabilities, and a status. Crucially, it also has an **identity**: an Ed25519 keypair. The public key is stored in the database and shown as a short fingerprint; the private key is held in the keyring. A node's proposals are signed with its key, so the hub can prove authorship rather than assert it.

Nodes do not act on their own authority. They observe, form proposals, and submit them. The separation between "a node can think" and "a node can act" is enforced structurally: there is no code path by which a node's proposal reaches an effect without passing through the gate.

## Proposals

A proposal carries a title, a description, a priority, the node that raised it, an optional target node, and optional dependencies on other proposals. It is signed at submission time over a canonical serialisation of its own fields. The hub verifies that signature against the raising node's public key before accepting it, and can re-verify it at any time.

Dependencies turn a pile of proposals into a plan: a proposal that depends on another cannot be approved until its dependency is resolved. The hub computes readiness automatically and surfaces it in the console.

Every proposal has a state — pending, approved, rejected, amended, in progress, done — and the state machine is intentionally simple and visible, because a state a human cannot see is a state a human cannot govern.

## The gate

The gate is the arbitration layer and the only place a human decision changes the course of events. It offers approve, reject, amend, delegate, start, complete, and reopen. Every action produces a **signed decision**: the arbitrator's key signs the action, its rationale, and its target, and that signature is stored alongside it. The gate is deliberately a bottleneck. A bottleneck a human controls is the difference between coordination and drift.

## The ledger

The ledger is an append-only hash chain. Each entry commits to the hash of the entry before it:

```
entry_hash = SHA-256( index ‖ prev_hash ‖ timestamp ‖ kind ‖ payload )
```

Change or remove any entry and every hash after it stops matching. Verification is a pure function of the record: `core/ledger.py` recomputes the chain from the stored entries and reports the first discrepancy. The genesis entry uses a `prev_hash` of sixty-four zeroes. The ledger is the hub's memory and its proof of honesty at the same time.

## Identity and cryptography

Cryptography is provided by a self-contained Ed25519 implementation in `core/ed25519.py`, so the hub depends on no external crypto library. `core/identity.py` wraps it with two conveniences: deterministic **canonical JSON** (sorted keys, no whitespace, ASCII-escaped) so that the same logical object always hashes to the same bytes, and short **fingerprints** derived from public keys for display.

Signing and verification are kept strictly separate. The hub verifies with public keys and, in this single-operator build, signs with keys it holds in the keyring. Moving signing to the operator's own device is a deployment change, not a format change.

## Compute

`core/models.py` connects nodes to a model running on hardware you control, over the Ollama / llama.cpp-server HTTP shape. When a local runtime is reachable, a node can draft a proposal with it; when none is, the hub falls back to a deterministic drafter so the system is always demonstrable. The point is that the default is your own machine, not a rented endpoint.

## The bundle

`core/bundle.py` exports the whole hub — nodes, proposals, decisions, and the full ledger — into a single JSON file with a manifest hash over the public record. `verify_bundle` checks the file offline: it recomputes the hash chain, recomputes the manifest, and re-verifies every proposal and decision signature from the public keys in the file. Anyone can confirm a bundle is honest without the private keys and without trusting the machine that produced it.

## Data flow of one unit of work

A node observes the board and raises a proposal, signing it with its key. The hub verifies the signature and records the submission in the ledger. The proposal enters the pending queue. The human, at the gate, sees it alongside its dependencies and its originating node, and arbitrates; the decision is signed and written to the ledger. If approved, it becomes available for execution and is assigned to a node; as it progresses, each state change is recorded. At no point does a node's intent become an effect without a human decision, and at no point is a decision made without a verifiable record.
