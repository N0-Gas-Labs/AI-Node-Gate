# Contributing

AI-Node-Gate is built to be expanded forward, and that invitation is open to people and to AI alike. Whether you are a developer, a designer, a writer, or a model reading this repository, there is a place for you here. This document explains how to take part.

## The one rule that matters

Keep the human at the gate. Every change to this project should preserve the central property of the hub: autonomous nodes may coordinate and propose freely, but no consequential action reaches an effect without a human decision, and every decision is recorded. If a proposed change would let a node act without arbitration, or would let a decision go unrecorded, it is out of scope for this project, however clever it is.

## Ways to contribute

You do not need to write code to contribute. Clear writing about the concept, thoughtful critique of the architecture, a better diagram, or a well-argued change to the roadmap are all valuable. If you do write code, the prototype is a static site with no build step, so the barrier to entry is as low as it gets: edit a file, refresh the browser, see the result.

## Working with the repository

Clone the repository and open the prototype locally. Because the hub is a static site, you can serve it with any simple HTTP server — `python3 -m http.server 8080` from the repository root is enough — and then open the address it prints. There is nothing to install and nothing to compile. State is kept in the browser's local storage, so experiments are safe: clear your browser storage to start fresh.

## Making a change

Create a branch for your work and give it a descriptive name. Keep each change focused on one idea; a pull request that does one thing well is easier to review and easier to trust than one that does five things at once. Write a commit message that explains what changed and why, in plain language. When you open a pull request, describe the change, the reasoning behind it, and how you tested it, even if testing was as simple as opening the page and clicking through the flow.

## Style

The project favours plain language and readable code over cleverness. Documentation should be written in prose, in complete sentences, with the assumption that the reader is intelligent but not yet convinced. Code should be simple enough that a non-developer can follow the shape of it, because one of the founding goals of this project is to be legible to someone who is not a coder. When in doubt, choose the version that a newcomer could understand on first read.

## Questions and ideas

If you are unsure whether something fits, open an issue and ask. The project is at its genesis, which means the cost of a question is low and the value of a good one is high. Bring the idea, make the case, and let the hub grow.
