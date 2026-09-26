# Roadmap

This roadmap is a direction, not a contract. It is written in phases so that each phase is useful on its own and none depends on the next being finished. The first phase is done: the vision, the architecture, and a working prototype of the hub exist in this repository.

## Phase 0 — Genesis (complete)

The founding phase establishes the concept and makes it visible. It delivers the vision document, the architecture document, a working single-page prototype of the hub with node registration, proposal submission, human arbitration, and a ledger, and the contribution guidelines that let others extend the work. The prototype runs with no build step and persists its state locally.

## Phase 1 — Make the hub real

The next phase turns the prototype from a demonstration into something a person would actually use day to day. The most valuable addition is persistence that survives more than a browser: an export and import of hub state as a portable JSON file, so a plan can be saved, shared, and versioned alongside the repository. Alongside that, the arbitration flow should grow richer — the ability to leave a written rationale on each decision, to set deadlines on proposals, and to filter the board by node, state, and priority so that a human can find the decision that needs them. This phase is about making the gate pleasant to sit at.

## Phase 2 — Connect real nodes

With the hub usable, the next step is to connect it to actual models. A node in the prototype is currently a description; in this phase it becomes a live participant with an endpoint. The hub gains a thin adapter layer that can send a proposal's context to a model and receive a response, so that proposals can be drafted by the nodes themselves rather than typed by hand. The adapter should be transport-agnostic — a local process, an HTTP endpoint, or a hosted API — so that the hub is not tied to any one provider. The human arbitration layer does not change in this phase; that is the point. Nodes get smarter, the gate stays the gate.

## Phase 3 — Coordination intelligence

Once real nodes are connected, the hub can begin to help with the coordination it was built for. This phase adds routing: the hub recommends which node should receive a proposal based on declared capabilities and current load, and the human can accept or override the recommendation. It adds dependency resolution that is visible as a graph rather than a list, so a human can see the shape of a plan at a glance. And it adds a notion of confidence, so that proposals can be triaged and the human's attention spent where it matters most.

## Phase 4 — Scale and governance

The final phase in view is about operating the hub at the scale of many nodes and many humans. This includes role-based arbitration, so that different decisions can be routed to different human authorities; a durable, append-only ledger that can be reviewed and audited over long periods; and the tooling to run the hub as a shared service rather than a personal one. The governing principle throughout is the one the project started with: autonomy for the nodes, authority for the human, and a record of both.

## How to contribute to the roadmap

The roadmap is open to argument. If you are working on the hub and see a better sequence, or a phase that should be split, or something important that is missing, open an issue or a pull request and make the case. The project is explicitly built to be expanded forward, and the roadmap is part of what that means.
