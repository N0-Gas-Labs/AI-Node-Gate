# Portfolio — lanes, decisions, and the mapping into this hub (legacy)

> **Status: historical memory.** This records the prior portfolio's lanes, the decisions
> taken on each, and how that prior capability maps into AI-Node-Gate. It is *not* a
> claim of live systems, and it contains no credentials or private keys. Financial and
> blockchain material is recorded under **security hold**.

## The portfolio, as it stood

| Portfolio lane | Prior canonical home | Supporting repos | Status | Next action (prior) |
|---|---|---|---|---|
| Public front door | `no-gas-labs` | Publibuildsec, sovereign-forge, oracle-mvp | Production candidate / prototype | Choose one public user journey |
| Portfolio intelligence | `evidenceos` | EvidenceOS-Inference-Engine, audit-vault, audit-monorepo | Foundation candidate | Reconcile public spec with implementation |
| Governance & ops | `no-gas-labs-governance` | command-center, execution, system-integration, AI-orchestrator-test, ai-guild | Foundation candidate | Keep decisions and release rules here |
| Podcast Operations Suite | `MaestroNGL` | BroadcastNGL, BuzzWireNGL, EthosGuardNGL, MoodSync, PulseMonitor, SonicForge, VoxScript, VeritasShield | First flagship / prototype suite | One end-to-end workflow before splitting |
| Games & social | decision required | TownSquare, no-gas-slaps, Mythos, dia-p2e, etc. | Experimental | Select one demonstrator |
| Finance / blockchain | `flashware-monorepo` | flash-loan-dapp, sui-flash-loan-*, multi-chain, Omnichain_Bridge_wallet, etc. | **Security hold** | No real-value use; consolidate docs; independent review |
| Historical copies | — | all `featherstone-*` (35) | **Archived** | Read-only; history preserved |

## The decision queue that was open

1. Confirm the public front door.
2. Build the Podcast Ops demonstrator around `MaestroNGL`.
3. Keep Featherstone archived.
4. Decide Games/Social: product lane or creative archive.
5. Keep finance under security hold.
6. Do not delete repositories; archival is the preservation strategy.

## Mapping the prior world into AI-Node-Gate

The recreation package's central instruction was to **absorb capability and memory, not
recreate ninety repositories**. The new hub already embodies the core doctrine — human at
the gate, signed decisions, verifiable ledger, sovereignty — so the prior world maps onto
it as follows:

| Prior capability | Absorbed into AI-Node-Gate as… | Notes |
|---|---|---|
| Node-Gate / epistemic gate | The core of AI-Node-Gate (already) | Taxonomy, personas, orchestration, arbitration |
| Command Center | The console and the mobile Command Center | Human control surface |
| EvidenceOS | An evidence / provenance module or sibling service | Verifiable analysis; the claim/source graph remains the next hard problem |
| Governance doctrines | `docs/` plus ledgered decisions | Charter, status vocabulary, roadmap, and this portfolio map live as docs and signed decisions |
| Podcast Ops suite | Optional node roles / scout channels later | Do not rebuild eight repos first; one workflow if ever |
| Games / social | Optional later, or archive conceptually | Decision still open |
| Finance / flash-loan family | **Do not recreate as product** | Security hold; research notes only if needed |
| Featherstone copies | Historical memory only | 35 archived; see [`REPO_INVENTORY.md`](REPO_INVENTORY.md); never treated as active code |
| Recursive Artifact Engine | A future verification boundary before publication | Still missing; design before implement |
| AI Guild | Agent-runtime patterns | Permissions and least privilege |

## Sovereignty properties already started here — keep them

The prior world's most valuable transferable asset was not a repository; it was a set of
properties this hub already carries. They should be defended:

- Standard-library-only / zero external dependencies where possible.
- One data file the operator owns.
- Ed25519 identity — keys, not accounts.
- A SHA-256 hash-chained ledger, verifiable offline.
- A local model adapter (Ollama / llama.cpp shape).
- Portable, verifiable bundle export.
- Honest limits, documented — for example, the operator key still lives in the hub
  keyring, which the current [`ROADMAP.md`](../ROADMAP.md) names as the next phase to
  close.

## The decision this memory produced

The prior organization's own doctrine — *one official home per product* — pointed at the
conclusion this hub now records: **`N0-Gas-Labs/AI-Node-Gate` is the canonical home**, and
the prior organization is historical reference only. That decision is recorded, signed,
and verifiable — see [`CANONICAL_HOME.md`](CANONICAL_HOME.md).
