# Roadmap

This roadmap is a direction, not a contract. It is written in phases so that each is useful on its own and none depends on the next being finished. Two phases are done: the concept is established, and the hub has been rebuilt as a sovereign, self-hosted system with a verifiable record.

## Phase 0 — Genesis (complete)

The founding phase established the concept and made it visible: the vision, the architecture, and a working single-page prototype of the hub. It proved the idea was legible.

## Phase 1 — Sovereignty (complete)

This phase replaced the browser toy with a system you own. It delivered a self-hosted runtime built on the Python standard library with no external dependencies; durable storage in a single SQLite file; real Ed25519 identity for nodes and the human arbitrator, with signed proposals and signed decisions; an append-only, hash-chained ledger that is tamper-evident and verifiable offline; a portable, verifiable export bundle; a compute layer that connects nodes to a local model runtime; an operator command line; and a web console that surfaces fingerprints, signature status, integrity, and the chain itself.

## Phase 2 — Harden the keys

The most important next step is to close the gap named honestly in `SOVEREIGNTY.md`: the hub currently holds the operator's signing key. This phase moves signing to the operator's own device. The hub should be able to run in a **non-custodial mode** where it only verifies, and decisions arrive pre-signed from the operator's machine — ideally backed by a hardware token. Independent nodes should likewise generate their own keys and hand over only their public key, so the hub never holds a secret it could abuse. The record format does not change; only who holds the pen does.

## Phase 3 — Durable and replicated record

A hash chain proves integrity but not availability. This phase makes the ledger survive the loss of any one machine: append-only replication across several nodes, a signed checkpoint that lets a lightweight client confirm it is looking at the current head, and a restore path that rebuilds a hub from a bundle plus subsequent checkpoints. The goal is a record that is not just tamper-evident but durable.

## Phase 4 — Coordination intelligence

With identity and durability in place, the hub can help with the coordination it was built for: routing that recommends which node should receive a proposal based on declared capabilities and load; dependency resolution rendered as a graph rather than a list; and a notion of confidence so the human's attention is spent where it matters. The human stays at the gate; the hub gets better at putting the right decision in front of them.

## Phase 5 — Federation

Sovereignty does not have to mean isolation. This phase lets independent hubs recognise each other: a node in one hub can submit a proposal to another, carrying its own key and a verifiable history, and each hub's human arbitrates only what crosses its own gate. Federation turns a collection of owned hubs into a network of owned hubs, without a central authority that any of them has to trust.

## How to contribute to the roadmap

The roadmap is open to argument. If you see a better sequence, a phase that should be split, or something important that is missing, open an issue or a pull request and make the case. The project is explicitly built to be expanded forward, and the roadmap is part of what that means.
