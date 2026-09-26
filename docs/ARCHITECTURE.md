# Architecture

## Overview

AI-Node-Gate is organised around four moving parts: nodes, proposals, the gate, and the ledger. Nodes are the participants. Proposals are the things they want to do. The gate is where a human decides. The ledger is where everything is remembered. The prototype in this repository implements all four as a single-page web application, but the model is deliberately small enough to re-implement on top of any transport — a local script, an HTTP API, or a message bus — without changing the concepts.

## Nodes

A node is one autonomous participant. In the prototype it is described by a name, a role, a set of capabilities, and a status. The role is the node's point of view: a planner sees the whole board, a researcher gathers, a builder executes, a critic looks for what is wrong. Capabilities are the verbs a node claims it can perform, and they are what the hub uses to decide which node a piece of work should be offered to. A node's status — idle, active, or blocked — is how the hub knows whether it is available.

Nodes do not act on their own authority. They observe the board, form proposals, and submit them. The separation between "a node can think" and "a node can act" is the whole point of the design, and it is enforced structurally: there is no code path by which a node's proposal reaches an effect without passing through arbitration.

## Proposals

A proposal is a unit of intent. It carries a title, a description, a priority, the node that raised it, an optional target node to carry it out, and a set of dependencies on other proposals. Dependencies are what turn a pile of proposals into a plan: a proposal that depends on another cannot be considered ready until its dependency is resolved. The hub computes this readiness automatically and surfaces it, so that the human sees not just what is proposed but what is actually unblocked.

Every proposal has a state. It begins as *pending*, awaiting arbitration. From there it can become *approved*, *rejected*, or *amended*. Approved proposals can be marked *in progress* and then *done*. The state machine is intentionally simple and intentionally explicit, because a state that is not visible is a state a human cannot govern.

## The gate

The gate is the arbitration layer, and it is the only place in the system where a human decision changes the course of events. It presents pending proposals and offers four actions. Approve lets the proposal proceed. Reject ends it. Amend reopens it for editing so the human can reshape the intent before it moves. Delegate reassigns it to a different node, which is how the human routes work to the participant best suited to it. The gate is deliberately a bottleneck. A bottleneck that a human controls is a feature; it is the difference between coordination and drift.

## The ledger

The ledger is an append-only list of events. Every time a node is registered, a proposal is submitted, a decision is made, or a state changes, an entry is written with a timestamp and a description. The ledger is the system's memory and its audit trail. It is what allows a human to reconstruct, after the fact, not only what was decided but why — which node proposed it, what it depended on, and who arbitrated it. Nothing in the hub is more important to trust than the ledger, and nothing is simpler: it is a list that only grows.

## Data flow

The flow of a single unit of work runs in one direction, with the human in the middle. A node observes the board and raises a proposal. The proposal enters the pending queue. The human, at the gate, sees it alongside its dependencies and its originating node, and arbitrates. If approved, it becomes available for execution and is assigned to a node. As it progresses, its state advances and each change is written to the ledger. At no point does a node's intent become an effect without a human decision in between, and at no point is a decision made without a record of it.

## The prototype

The prototype is a static site: `index.html` for structure, `css/styles.css` for presentation, and `js/app.js` for behaviour. State lives in the browser's local storage under a single key, and is serialised as JSON. There is no backend, no build step, and no dependency beyond the browser. This is a deliberate choice for a first version: it means the concept can be opened, understood, and modified by anyone, including someone who is not a developer, by editing a single HTML file and refreshing. The prototype is a reference implementation of the model, not the model itself. When a real transport is added, the four concepts — nodes, proposals, the gate, the ledger — carry over unchanged.
