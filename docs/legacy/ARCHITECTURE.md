# Intended System Architecture — the "Recursive OS" (legacy)

> **Status: historical memory / specification.** This is the architecture the prior
> organization *intended*, reconstructed from its governance repository and the
> 2026-09-05 audit. Much of it was documentation-only or incomplete. It is preserved
> as design memory, not as a description of running software.

The prior portfolio aspired to a single recursive loop in which a human objective
travels through classification, deliberation, evidence, arbitration, artifact
generation, and independent verification — and then re-enters the system as fresh
evidence. The name given to it was the **Recursive OS**.

## The loop

```
Human objective
  -> Command Center
  -> Node-Gate taxonomy and complexity analysis
  -> Meta-Guild council formation
  -> Persona deliberation and challenge
  -> EvidenceOS retrieval and provenance
  -> Arbitration / preserved uncertainty
  -> Recursive Artifact Engine
  -> independent verification and governance checks
  -> GitHub branch, tests, PR, deployment observation
  -> EvidenceOS re-ingestion
```

The important property is that the loop closes: the output of one pass becomes the
evidence of the next. Nothing is trusted merely because a model produced it; every
artifact is meant to be independently verified before it is published, and the result
of that verification is fed back into the evidence substrate.

## Canonical components (status as of 2026-09-05)

| Component | Prior repo | Role | Status at the time |
|---|---|---|---|
| Human control surface | `no-gas-labs-command-center` | React/Vite + Express; proxies Node-Gate & EvidenceOS | Implemented, incomplete (E2E smoke 12/12; auth and persistence open) |
| Epistemic gate | `AI-BI-Intelligence-node-gate` | V/P/S/M/A taxonomy, 25-persona registry, provider-backed orchestration | Implemented, incomplete (POST /v2/orchestrate real; simulation labeled) |
| Agent runtime | `ai-guild-hardened-v0.2` | API, auth, agents, repos | Implemented, incomplete (no test suite) |
| Evidence substrate | `evidenceos` | Two-pass analysis CLI + HTTP service, `evidenceos/v1` provenance envelope | Implemented, incomplete (syntactic signals; no claim/source graph) |
| Governance control plane | `no-gas-labs-governance` | Portfolio, policy, architecture registry | Documentation-only |
| Execution lane | `no-gas-labs-execution` | Templates, checklists, reports | Documentation-only |
| Artifact boundary | `recursive-artifact-engine` | Intended verification boundary before publication | Documentation-only (README intent) |

## Trust boundaries (must be preserved)

The architecture named five boundaries where trust changes hands. Each is a place
where a failure can silently become a false success, so each must be watched:

1. **Browser → Command Center.** Untrusted input; validate and trace it.
2. **Command Center → Node-Gate.** A network boundary; errors must never be converted
   into simulated success.
3. **Node-Gate → model providers.** A provider-neutral adapter; credentials live in the
   environment only, never in code.
4. **Runtime → GitHub / DB / Redis.** Least privilege — at the time, not yet proven.
5. **Artifact generation → publication.** Independent verification and provenance are
   required before anything is published.

## Implementation order that was next

When the audit closed, the intended order of work was:

1. Executable API and failure-path tests for the Command Center and Node-Gate.
2. Connect the deployed EvidenceOS and return repo/file/commit provenance.
3. Expand provider adapters and add structured-output tests.
4. Persist orchestration sessions beyond process memory.
5. Make agent permissions explicit in the AI Guild.
6. Validate artifacts in the Artifact Engine before publication.
7. Turn governance metadata into tested GitHub checks.

## What this hub kept

AI-Node-Gate already embodies the spine of this architecture: a human objective enters
a control surface, passes through a gate where a human arbitrates, and every decision is
signed and written to a verifiable record. The parts that were *missing* in the prior
world — a durable claim→source→artifact→commit→test→deployment evidence graph, and
independent artifact verification before publication — remain the honest next hard
problems. See [`STATUS.md`](STATUS.md) for the full snapshot.
