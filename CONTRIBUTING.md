# Contributing

AI-Node-Gate is built to be expanded forward, and that invitation is open to people and to AI alike. Whether you are a developer, a designer, a writer, or a model reading this repository, there is a place for you here. This document explains how to take part.

## The two rules that matter

**Keep the human at the gate.** Every change should preserve the central property of the hub: autonomous nodes may coordinate and propose freely, but no consequential action reaches an effect without a human decision, and every decision is recorded. If a change would let a node act without arbitration, or let a decision go unrecorded, it is out of scope, however clever it is.

**Keep it sovereign.** The hub must remain something a person can own. That means no external dependencies — the Python standard library and this repository are the whole system. It means data stays in one file the operator holds, identity stays cryptographic, the record stays verifiable offline, and compute stays pointed at the operator's own hardware by default. A pull request that adds a dependency, phones home, or moves authority off the operator's machine is out of scope unless it is strictly opt-in and clearly labelled.

## Ways to contribute

You do not need to write code to contribute. Clear writing about the concept, thoughtful critique of the architecture, a better diagram, or a well-argued change to the roadmap are all valuable. If you do write code, the prototype is a static site with no build step, so the barrier to entry is as low as it gets: edit a file, refresh the browser, see the result.

## Working with the repository

Clone the repository and run the hub locally. There is nothing to install — no `pip`, no build step, no account. From the repository root:

```bash
python3 manage.py init     # creates ./.ngg (a database and a keyring)
python3 manage.py serve    # serves the console at http://127.0.0.1:8787
```

The whole hub lives in `.ngg/`. Delete that directory to start fresh, or copy it to move the hub elsewhere. To check your work, run `python3 manage.py verify` — it recomputes the ledger chain and re-verifies every signature, and it should always come back clean.

## Making a change

Create a branch for your work and give it a descriptive name. Keep each change focused on one idea; a pull request that does one thing well is easier to review and easier to trust than one that does five things at once. Write a commit message that explains what changed and why, in plain language. When you open a pull request, describe the change, the reasoning behind it, and how you tested it, even if testing was as simple as opening the page and clicking through the flow.

## Style

The project favours plain language and readable code over cleverness. Documentation should be written in prose, in complete sentences, with the assumption that the reader is intelligent but not yet convinced. Code should be simple enough that a non-developer can follow the shape of it, because one of the founding goals of this project is to be legible to someone who is not a coder. When in doubt, choose the version that a newcomer could understand on first read.

## Questions and ideas

If you are unsure whether something fits, open an issue and ask. The project is at its genesis, which means the cost of a question is low and the value of a good one is high. Bring the idea, make the case, and let the hub grow.
