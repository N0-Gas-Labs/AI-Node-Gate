# AI-Node-Gate

**A sovereign, human-arbitrated coordination and planning hub.**

AI-Node-Gate is a single, human-supervised gateway through which multiple autonomous AI nodes connect, coordinate, plan, and act. The nodes negotiate work among themselves and propose plans, but nothing crosses the gate into the real world until a human arbitrates the decision. Every proposal and every decision is signed, and every event is written to an append-only, tamper-evident ledger that anyone can verify offline.

It runs on your machine, stores everything in one file you own, depends on nothing but the Python standard library, and can point its nodes at a model running on your own hardware. Nothing is rented and nothing is hidden.

> Founded by **Damien Featherstone** — The Neophyte Founder of **No_Gas_Labs™**. "I am not a coder or developer. I'm just good at talking to AI and being creative. I intend to demonstrably increase ability by augmenting my mental bandwidth with multiple LLMs. My AI is invited to expand this repository forward."

---

## Why this exists

A single LLM has a single point of view. Several of them, each with different strengths and roles, behave more like a team than a tool — but a team without a decision-maker drifts. AI-Node-Gate is the missing decision-maker made explicit, and made *provable*: an arbitration layer where autonomous nodes propose and a human decides, with a cryptographic record of both. It augments mental bandwidth without removing the human from the loop.

## Quickstart

Requires Python 3.9 or newer. Nothing else — no `pip install`, no build step, no account.

```bash
# 1. create a hub (a database and a keyring, in ./.ngg)
python3 manage.py init

# 2. run it
python3 manage.py serve
# open http://127.0.0.1:8787
```

Register a node, submit a proposal, arbitrate it at the gate, then click **verify now** to watch the ledger chain and every signature check out.

### Command line

Everything the console does, the operator CLI does too:

```bash
python3 manage.py node add Atlas Planner --caps "plan,route"
python3 manage.py node list
python3 manage.py propose <node-id> "Draft the doctrine" --priority high
python3 manage.py gate <proposal-id> approve --rationale "On mission."
python3 manage.py verify                 # verify the chain and all signatures
python3 manage.py export hub.bundle.json # a portable, verifiable bundle
python3 manage.py import hub.bundle.json # verify, then load
```

## What makes it sovereign

- **No dependencies.** The whole hub is the Python standard library plus this repository. Nothing to install, nothing to trust, nothing that can be deprecated out from under you.
- **Your data.** Everything lives in one SQLite file. Copy it and you have copied the hub.
- **Real identity.** Every node and the human arbitrator have Ed25519 keys. Proposals and decisions are signed and verifiable against public keys.
- **A verifiable record.** The ledger is a SHA-256 hash chain; altering any entry breaks every hash after it. Verification needs no network and no trust.
- **Your compute.** Nodes can draft with a model on your own hardware (Ollama / llama.cpp / LM Studio), not a rented API.
- **Portable proof.** Export the whole hub as one JSON bundle that anyone can verify offline, without the private keys.

Read the full account, including its honest limits, in [`docs/SOVEREIGNTY.md`](docs/SOVEREIGNTY.md).

## Repository layout

```
AI-Node-Gate/
├── README.md
├── server.py            ← the self-hosted runtime (stdlib only)
├── manage.py            ← the operator command line
├── core/
│   ├── ed25519.py       ← pure-Python signatures, zero dependencies
│   ├── identity.py      ← keypairs, canonical JSON, signing
│   ├── ledger.py        ← the hash-chained append-only record
│   ├── store.py         ← SQLite persistence
│   ├── hub.py           ← nodes, proposals, the gate, the ledger
│   ├── scouts.py        ← scout engine: channels, scoring, demo + feed sources
│   ├── models.py        ← local model runtime adapter
│   └── bundle.py        ← portable, verifiable export
├── web/                 ← the console (index.html, css, js)
│   └── command/         ← the mobile Command Center (PWA)
└── docs/
    ├── VISION.md        ← what we are building and why
    ├── ARCHITECTURE.md  ← how the hub is structured
    ├── SOVEREIGNTY.md   ← what sovereignty means here, and its limits
    └── ROADMAP.md       ← where it goes next
```

## Core vocabulary

**Node** — one autonomous participant: an LLM instance, an agent, or a tool-wrapper, with a role, capabilities, and an Ed25519 identity.

**Proposal** — a signed plan or action a node wants to execute. Inert until arbitrated.

**The gate** — the human decision that moves a proposal forward: approve, reject, amend, delegate, start, complete, or reopen. Each decision is signed.

**Ledger** — the append-only, hash-chained record of every node, proposal, decision, and state change. Verifiable by anyone.

**Bundle** — a single JSON file containing the whole hub plus a manifest hash, verifiable offline.

**Scout** — a node deployed on a mission to hunt for opportunities in a channel. It proposes; it never acts.

**Mission** — a scout's assignment: what to find, and where to look.

**Opportunity** — a scored finding a scout brings back (value, confidence, effort → ROI). It waits at the gate for your decision.

**Pocketbook** — pipeline, expected, and realised value, plus win rate — derived from the signed record.

**Capability** — your tier, level, and XP, earned from decisions, approvals, wins, and missions — also derived from the signed record.

## Status

The hub is a working sovereign system: self-hosted, dependency-free, with real identity and a verifiable record. It is honest about where it stops short — most importantly, the operator's signing key is currently held by the hub, and moving it onto the operator's own device is the next phase. See the [roadmap](docs/ROADMAP.md).

---

*No_Gas_Labs™ — autonomy for the nodes, authority for the human, and a verifiable record of both.*
