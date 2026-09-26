# AI-Node-Gate — Market Research & Path to Profitability

**Prepared for:** No_Gas_Labs™ — Damien Featherstone
**Subject:** What AI-Node-Gate must expand into to become a profitable service
**Status:** Research synthesis, Q1 2026
**Method:** Primary pricing pages (vendor sites), syndicated market-research reports, and regulatory sources. Every figure is cited with a source URL. Figures are reported as published; where sources disagree, both are shown.

---

## 0. Executive summary

AI-Node-Gate is a **sovereign, human-arbitrated coordination hub**: autonomous AI nodes propose and coordinate, but a human decides at "the gate," and every proposal and decision is Ed25519-signed and written to a SHA-256 hash-chained, append-only ledger that verifies offline. It runs on the Python standard library alone, stores everything in one SQLite file, and can drive local models. It is, in one sentence, **the audit-grade decision layer for teams that run AI on infrastructure they own.**

The market research says three things clearly.

**First, the category is real and large, and it is growing faster than almost any other software category.** Agentic orchestration is a ~$6.3B market in 2025 growing at ~35% CAGR to ~$28.5B by 2030. AI governance is ~$308M (2025) growing at ~36% CAGR toward ~$3.6B by 2033. Human-in-the-loop AI is ~$2.4B (2025) growing at ~19% CAGR to ~$11.8B by 2034. Sovereign AI infrastructure is ~$15B (2025) growing at ~28% CAGR to ~$177B by 2035. These are adjacent slices of the same underlying demand: enterprises deploying AI agents need to *control, observe, and prove* what those agents do.

**Second, the "sovereign / self-hosted / on-premises" segment is not a niche — it is the majority of several of these markets, and it is the fastest-growing deployment mode in the governance and HITL categories.** On-premises held the largest deployment share of the AI-governance market in 2025 and dominated the sovereign-AI-infrastructure market; on-premises is ~38.7% of HITL revenue and growing. Government & defense is the largest vertical in both governance and sovereign AI. This is precisely where a zero-dependency, single-file, offline-verifiable system wins and where cloud-native competitors (LangSmith, CrewAI Cloud) structurally cannot follow without abandoning their own model.

**Third, the incumbents have left a specific gap that AI-Node-Gate is built to fill.** The observability leaders (LangSmith, Langfuse, Arize) sell *traces* — a record of what happened. The orchestration frameworks (LangGraph, CrewAI) sell *execution* — a way to run agents. Almost nobody sells *arbitrated, cryptographically verifiable decisions* as the unit of record, and almost nobody sells it as something you fully own and can verify offline with no vendor in the loop. AI-Node-Gate's ledger is not a log; it is a **signed, hash-chained decision record** — the artifact a regulator, an auditor, or a court actually wants. That is the wedge.

**The recommended path to profitability** is an **open-core, self-hosted-first** model: keep the runtime and record format free and open (the distribution engine), and monetize the things enterprises with compliance obligations will pay for — **non-custodial signing and hardware-backed keys, high-availability/replicated ledgers, compliance evidence packs (EU AI Act / ISO 42001 / SOC 2 mappings), SSO/RBAC/policy enforcement, and a supported "sovereign appliance" with an SLA.** Price against the enterprise tiers of the observability vendors ($2,499/mo Langfuse Enterprise; LangSmith self-hosting is Enterprise-only) and the HITL market's enterprise contract norms (frequently >$5M annually at the top end), while offering a land-and-expand entry point well below the $20k–60k SME orchestration project cost. The detailed roadmap is in Section 7.

---

## 1. What AI-Node-Gate actually is today (grounding)

Before pricing anything, the product must be stated precisely, because the whole strategy depends on what is genuinely defensible.

**What it is.** A self-hosted hub in which independent AI "nodes" (each with its own Ed25519 keypair and declared capabilities) submit **proposals** to a shared queue. A human **arbitrator** — also a keyed identity — approves, rejects, amends, or delegates each proposal at "the gate." Every proposal and every decision is signed and appended to a **SHA-256 hash-chained ledger** where each entry commits to the hash of the previous entry, so any tampering is detectable and the whole chain can be verified **offline** from an exported bundle. The system runs on the **Python standard library only** (no pip dependencies), persists to a **single SQLite file**, and can connect nodes to a **local model runtime**.

**The four sovereignties** (from the repo's `SOVEREIGNTY.md` and README):

1. **Runtime sovereignty** — standard library only; nothing to install, nothing to phone home to.
2. **Data sovereignty** — one SQLite file you own and can copy, back up, and inspect.
3. **Identity sovereignty** — keys, not accounts; no central identity provider.
4. **Compute sovereignty** — you can run your own models on your own hardware.

**The honest gap** (named in the repo's own `SOVEREIGNTY.md` and roadmap): today the hub holds the operator's signing key. The roadmap's Phase 2 is to make signing **non-custodial** — the hub only verifies, and decisions arrive pre-signed from the operator's device, ideally hardware-backed. This gap matters commercially because "the vendor (or the hub) never holds your signing key" is exactly the assurance regulated buyers want, and closing it is a monetizable milestone, not just an engineering nicety.

**Core value proposition (one sentence).** *AI-Node-Gate is the audit-grade, fully self-hosted decision layer that lets teams run autonomous AI agents while keeping a cryptographically verifiable, human-arbitrated record of every decision — on infrastructure they own, with no vendor in the loop.*

**What it is not.** It is not an agent framework (it does not compete with LangGraph/CrewAI for "how do I build an agent"), and it is not a tracing tool (it does not compete with LangSmith/Langfuse for "show me the prompt and the tokens"). It sits *above* execution and *beside* observability, owning the one thing neither owns: **the signed, arbitrated decision.**

---

## 2. Market landscape

### 2.1 The category map

AI-Node-Gate sits at the intersection of four overlapping categories. Understanding them separately matters because each has a different buyer, price point, and growth rate — and AI-Node-Gate can draw revenue from more than one.

| Category | What it sells | 2025 size | Growth | Closest to AI-Node-Gate? |
|---|---|---|---|---|
| **Agentic AI orchestration & memory** | Running and coordinating agents | ~$6.27B | 35.3% CAGR → $28.45B (2030) | Adjacent — we coordinate, they execute |
| **AI governance** | Policy, oversight, compliance for AI | ~$308.3M | 36.0% CAGR → $3.59B (2033) | **Direct** — this is our buyer's budget line |
| **Human-in-the-loop AI** | Human review/oversight of AI output | ~$2.4B | 19.3% CAGR → $11.8B (2034) | **Direct** — the "human gate" is HITL |
| **Sovereign AI infrastructure** | Owned/air-gapped AI compute + stack | ~$15.0B | 28.0% CAGR → $177.1B (2035) | Adjacent — we are the software layer of it |

Sources: Mordor Intelligence (agentic orchestration), Grand View Research (AI governance), Dataintelo (human-in-the-loop AI), Precedence Research (sovereign AI infrastructure). Full URLs in Section 9.

### 2.2 Direct competitors

There is **no single product that does exactly what AI-Node-Gate does** (arbitrated, signed, hash-chained decision record, self-hosted, zero-dependency). But buyers will compare it to these, and the sales conversation must position against each:

- **LangGraph + LangSmith (LangChain).** LangGraph is the leading agent-orchestration framework (free, MIT). LangSmith is the observability/oversight layer. This is the most likely "we already use this" objection. **Where we win:** LangSmith's self-hosted/hybrid deployment is **Enterprise-only**, and its unit of record is a *trace* (a log), not a *signed decision*. We are self-hosted by default and our unit of record is cryptographically verifiable and human-arbitrated.
- **CrewAI.** Agent framework with a free tier and an Enterprise tier that already sells **governance** (SSO, RBAC, workload identity, PII redaction, policies) and deployment on the customer's own VPC/infra. **Where we win:** CrewAI governs *how agents run*; we govern *what gets decided and prove it*. CrewAI's record is operational; ours is evidentiary.
- **AI governance platforms** (the Grand View category — IBM, Microsoft, Credo AI, Holistic AI, etc.). These sell policy management, model risk, and compliance dashboards, usually as SaaS. **Where we win:** we are the *enforcement and evidence layer* — a decision cannot be recorded without a human signature and a hash-chain link. We can be the system-of-record these platforms point to, or the sovereign alternative to them.
- **Langfuse / Arize Phoenix / Braintrust / Helicone.** Observability. **Where we win:** observability answers "what happened?"; we answer "who authorized it, and can you prove it wasn't altered?" Different question, different budget, often complementary.

### 2.3 Adjacent / indirect competitors

- **Workflow & RPA** (UiPath, ServiceNow, Zapier, n8n, Temporal). These orchestrate *tasks*; some are adding "human approval steps." **Where we win:** their approvals are workflow states in a proprietary database; ours are signed, hash-chained, and portable.
- **ITSM / change-management** (ServiceNow, Jira Service Management). They already own "human approval of a change." **Where we win:** we are the AI-native, cryptographically verifiable version — and a plausible *integration* target rather than a pure competitor.
- **Cloud AI platforms** (Azure AI, AWS Bedrock, Google Vertex). They offer "human-in-the-loop" features but only *inside their cloud*. **Where we win:** sovereignty — the entire point is that the record and the keys never leave your premises.
- **Data-annotation HITL vendors** (Scale AI, Surge, Appen). They sell *human labor* for labeling/review. **Where we win:** we sell the *mechanism and record* of human arbitration, not the labor — a different layer, and a software (not services) margin.

### 2.4 Market size and TAM/SAM/SOM

A defensible funnel for AI-Node-Gate:

- **TAM (total addressable):** the overlap of "AI governance" + "human-in-the-loop AI" + the self-hosted slice of "agentic orchestration." Conservatively, **> $8B in 2025** (governance $0.31B + HITL $2.4B + a self-hosted portion of orchestration), growing to well over $40B by the early 2030s. If you include the software layer of sovereign AI infrastructure, the ceiling is far higher.
- **SAM (serviceable addressable):** the **self-hosted / on-premises / air-gapped** slice of the above, concentrated in **government & defense, BFSI, healthcare, and IT/telecom** — the verticals that both dominate these markets and have the strongest data-sovereignty mandates. On-premises is the largest deployment mode in governance and sovereign-AI, and ~38.7% of HITL revenue.
- **SOM (serviceable obtainable, 3-year):** a realistic wedge is **dozens of enterprise/agency accounts** at $50k–$500k ACV in the compliance-driven, self-hosted segment — the same segment where HITL contracts "frequently exceed $5M annually" at the top end and where Langfuse already charges **$2,499/month** for its Enterprise tier. Even a modest share of that segment is a multi-million-dollar business.

---

## 3. Buyer & demand research

### 3.1 Who buys

Four personas, in order of likely budget authority:

1. **The compliance / risk officer (economic buyer for the governance budget).** Owns the obligation to *prove* AI was governed. Cares about: audit trails, tamper-evidence, evidence that survives an examination, mappings to EU AI Act / ISO 42001 / SOC 2. This persona has a *mandate and a deadline*, which is the strongest kind of buyer.
2. **The security / platform architect (technical gatekeeper).** Owns "does this touch our network, where do the keys live, can we run it air-gapped?" Cares about: no external dependencies, no vendor-held secrets, offline verification, single-file portability. AI-Node-Gate's four sovereignties are written for this person.
3. **The engineering leader (champion / user).** Runs the AI agents and is tired of "the model did something and we can't explain it." Cares about: an easy way to put a human in the loop, a clear record, and not having to build it themselves.
4. **The operations / delivery lead (user).** Lives at the gate — approving, amending, delegating. Cares about: the console being fast and legible, and attention being spent only where it matters.

### 3.2 What problems buyers pay to solve

- **"We can't prove what our AI decided, or who approved it."** This is the core pain. Existing logs are mutable, fragmented, and not evidentiary. AI-Node-Gate produces a signed, hash-chained record that is verifiable offline.
- **"We're not allowed to send this data to your cloud."** Government, defense, healthcare, and finance cannot use SaaS oversight tools for sensitive workloads. On-premises is the largest deployment mode in governance and sovereign AI for exactly this reason.
- **"The vendor holds our keys."** Regulated buyers increasingly refuse to let a third party hold signing authority. The non-custodial roadmap directly answers this.
- **"Human oversight is a checkbox, not a control."** Buyers want oversight that is *enforced* (a decision cannot be recorded without a human signature) and *auditable*, not a policy document.
- **"We're drowning in agent output."** As agents multiply, the scarce resource is *human attention*. A hub that surfaces only the decisions that need a human is directly valuable.

**Willingness to pay is demonstrated, not assumed.** Langfuse Enterprise is **$2,499/mo**; LangSmith self-hosting is Enterprise-only; CrewAI Enterprise is custom-priced with forward-deployed engineering; HITL enterprise contracts run into the millions. Buyers in this category already pay five- and six-figure sums for oversight and governance. The question is not *whether* they pay, but *which vendor* and *which unit of value* they pay for.

### 3.3 The regulatory tailwind

This is the single most important demand driver and it is getting stronger:

- The **EU AI Act** carries penalties of up to **EUR 30M or 6% of global turnover** for the most serious violations, and imposes record-keeping, human-oversight, and risk-management obligations on high-risk AI systems. Compliance-driven demand is projected to reach roughly **31% of HITL revenue by 2034**.
- **67% of Fortune 500 AI deployers already use human-in-the-loop** review — the practice is mainstream; the *tooling to prove it* is not.
- **Government & defense** is the largest vertical in both AI governance and sovereign AI infrastructure, and government AI-infrastructure spending is growing steeply.

The regulatory tailwind converts "nice to have" oversight into "must have" evidence. AI-Node-Gate's ledger is, functionally, a compliance-evidence engine.

### 3.4 Comparable pricing (verified from vendor pages)

| Product | Free / entry | Mid tier | Enterprise | Self-host? |
|---|---|---|---|---|
| **LangSmith** (LangChain) | Developer free (1 seat, 5k traces/mo) | Plus **$39/seat/mo** (10k traces) | Custom | **Enterprise only** |
| — LangSmith overage | — | $2.50 / 1k base traces; $5.00 / 1k extended | — | — |
| **Langfuse** | Hobby free (50k units) | Core **$29/mo**; Pro **$199/mo** | **$2,499/mo** | Yes (OSS self-host) |
| **Arize Phoenix** | OSS free | AX Pro **$50/mo** | Custom | Yes (OSS) |
| **Braintrust** | Free | Pro **$249/mo** | Custom | Limited |
| **Helicone** | Free | Pro **$79/mo** | Custom | Yes |
| **CrewAI** | Basic free (50 exec/mo) | — | Custom (governance, VPC/own infra) | Yes (Enterprise) |

Sources: truefoundry.com (LangGraph/LangSmith pricing), inference.net (LangSmith + alternatives), crewai.com/pricing. Full URLs in Section 9.

**Reading of the table:** the observability incumbents have trained the market to pay **per-seat + per-volume** for oversight, with enterprise self-hosting gated behind the top tier. AI-Node-Gate should **invert the gate**: self-hosting is free and default (our distribution), and we charge for the *enterprise assurances* (non-custodial signing, HA ledger, compliance packs, SSO/RBAC, SLA).

---

## 4. Differentiation & positioning

### 4.1 The sovereign / self-hosted / air-gapped niche is the majority, not a niche

The research repeatedly shows the "owned infrastructure" segment is large and growing:

- **AI governance:** on-premises held the **largest deployment share** in 2025; government & defense is the largest vertical.
- **Sovereign AI infrastructure:** on-premises **dominated** 2025; government & defense **dominated**; Europe is the largest region (**34.2%** share) with national data-security and data-localization mandates driving it.
- **Human-in-the-loop:** on-premises is **38.7%** of revenue and growing at **16.4% CAGR**; the market restraint on the cloud side is data-sovereignty concerns.
- **Agentic orchestration:** self-hosted/on-prem is a recognized segment; compliance mandates for LLM audit trails are a named growth driver.

**Implication:** AI-Node-Gate is not fishing in a puddle. It is built for the largest and most defensible slice of several multi-billion-dollar markets, and its zero-dependency, single-file, offline-verifiable design is *uniquely* suited to it.

### 4.2 Where AI-Node-Gate's assets win

| Asset | Why it wins | Who pays for it |
|---|---|---|
| **Signed, hash-chained ledger** | Tamper-evident, offline-verifiable evidence — the artifact auditors want | Compliance/risk, government, BFSI, healthcare |
| **Human arbitration at the gate** | Enforced oversight, not a policy checkbox; satisfies EU AI Act human-oversight duties | Compliance, ops |
| **Zero dependencies (stdlib only)** | Deploys into air-gapped, high-assurance environments; nothing to supply-chain-attack | Security/platform, defense |
| **Single SQLite file** | Data sovereignty; trivial backup, inspection, portability | Security, ops |
| **Keys, not accounts** | No central IdP to compromise; identity you own | Security |
| **Non-custodial signing (roadmap)** | "No vendor holds our keys" — the assurance regulated buyers demand | Compliance, security |

### 4.3 The wedge (beachhead)

**The beachhead is: regulated, self-hosted AI-agent deployments that must prove human oversight — starting with government/defense and BFSI.** These buyers (a) already must keep data on-premises, (b) already have a compliance mandate with a deadline, (c) already pay for oversight tooling, and (d) cannot use the cloud-native incumbents for the sensitive workloads. The initial product motion is a **"sovereign oversight appliance"**: a self-hosted AI-Node-Gate hub that gives an agency or regulated enterprise a signed, human-arbitrated, offline-verifiable record of every AI decision, with a compliance-evidence pack that maps the ledger to EU AI Act / ISO 42001 / SOC 2 controls.

**The wedge use case in one line:** *"Put a human signature on every AI decision, and keep the proof on your own hardware."*

---

## 5. Monetization models

### 5.1 The options, evaluated

- **Open-core (recommended).** Free, open, self-hostable core (the runtime, the record format, the console) as the distribution engine; paid enterprise features (non-custodial signing, HA/replication, compliance packs, SSO/RBAC/policy, support/SLA). This is the model the observability market already validates (Langfuse, Arize) and the model the Linux Foundation's *State of Commercial Open Source 2025* shows consistently outperforms closed source in valuation and liquidity — especially for infrastructure software.
- **Dual-license.** Core under a permissive license (e.g., Apache-2.0) plus a commercial license for embedding in closed products. Useful as an *additional* revenue stream (OEM), not the primary motion.
- **Hosted / managed cloud.** A managed hub for teams that want the record without operating it. **De-prioritize as the primary motion** — it contradicts the sovereignty story and competes head-on with incumbents. Offer it only as an *optional* convenience, and never for sensitive workloads.
- **Enterprise support & services.** Onboarding, air-gapped deployment, compliance mapping, and forward-deployed engineering. High-margin, and the way CrewAI already sells its enterprise tier. Essential for the government/defense wedge.
- **Certification / assurance.** A paid "verified sovereign deployment" program and a compliance-evidence pack. Recurring, defensible, and aligned with the compliance buyer.

### 5.2 Recommended pricing tiers (modeled against comparables)

| Tier | Price (indicative) | Contents | Comparable anchor |
|---|---|---|---|
| **Community** | **Free (open source)** | Full runtime, record format, console, CLI, self-host, offline verify | Langfuse Hobby / Arize OSS |
| **Team** | **$199–$499/mo** (or ~$99/seat/mo) | Managed convenience, multi-node, basic policy, email support | Langfuse Pro $199 / Braintrust $249 |
| **Business** | **$2,000–$2,999/mo** | SSO/RBAC, policy enforcement, HA/replicated ledger, audit exports, priority support | **Langfuse Enterprise $2,499/mo** |
| **Enterprise / Sovereign** | **$50k–$500k+/yr** | Non-custodial + hardware-backed signing, air-gapped deployment, compliance-evidence packs, SLA, forward-deployed engineering | CrewAI Enterprise; HITL enterprise contracts (>$5M at top end) |

**Pricing logic:** anchor the Business tier at Langfuse Enterprise ($2,499/mo) — the market has already accepted that number for self-hosted oversight. Anchor the Enterprise/Sovereign tier on the value of *provable compliance* (EU AI Act exposure up to EUR 30M/6% turnover), which dwarfs the price. Keep the Community tier genuinely free and complete so it spreads.

### 5.3 Revenue mix (target, 3-year)

- **~50% Enterprise/Sovereign subscriptions** (the wedge; high ACV, compliance-driven).
- **~25% Business-tier subscriptions** (land-and-expand from Community).
- **~15% Services** (air-gapped onboarding, compliance mapping, forward-deployed engineering).
- **~10% OEM/dual-license and certification.**

---

## 6. Risks and how the research addresses them

- **"Incumbents will add this."** LangSmith and CrewAI could add "signed approvals," but doing so credibly requires *not* holding the customer's keys and *not* requiring their cloud — which undercuts their own model. Our moat is architectural, not feature-level.
- **"Open source has no business model."** Disproven by the Linux Foundation's 2025 data (800 VC-backed COSS companies, 25 years) and by Langfuse/Arize charging enterprise prices on open cores.
- **"Sovereignty is a small niche."** Disproven: on-premises is the *largest* deployment mode in governance and sovereign AI, and a large slice of HITL.
- **"The hub holds the key today."** This is the top product risk and the top monetization opportunity — closing it (non-custodial, hardware-backed) is the flagship enterprise feature.
- **"Compliance deadlines slip."** Mitigate by selling the *engineering* value (a clean, enforced human-in-the-loop record) alongside the compliance value, so demand doesn't depend solely on regulation.

---

## 7. Prioritized feature → revenue roadmap

Ordered by *revenue impact per unit of effort*, mapped to the repo's existing phases.

**Tier 1 — Unlock the enterprise/sovereign buyer (do first).**
1. **Non-custodial signing + hardware-backed keys** (repo Phase 2). *Unlocks:* the "no vendor holds our keys" assurance → Enterprise/Sovereign tier. Highest revenue impact.
2. **Compliance-evidence packs** — map the ledger to EU AI Act / ISO 42001 / SOC 2 controls; export an auditor-ready bundle. *Unlocks:* the compliance budget line; the core of the wedge.
3. **SSO / RBAC / policy enforcement.** *Unlocks:* the Business tier ($2,000–$2,999/mo); table-stakes for enterprise procurement.

**Tier 2 — Make it durable and sellable at scale.**
4. **Replicated / HA ledger + signed checkpoints** (repo Phase 3). *Unlocks:* production deployment in regulated environments; removes the "single point of failure" objection.
5. **Air-gapped deployment kit + supported appliance** (installer, hardening guide, offline upgrade path). *Unlocks:* government/defense and high-assurance accounts.
6. **Compliance mapping service / forward-deployed onboarding.** *Unlocks:* services revenue and faster enterprise sales cycles.

**Tier 3 — Deepen the moat and the value.**
7. **Coordination intelligence** — capability/load-based routing, dependency graphs, confidence scoring to focus human attention (repo Phase 4). *Unlocks:* differentiation vs. plain "approval workflow"; higher-tier pricing.
8. **Federation** — cross-hub proposals with verifiable history (repo Phase 5). *Unlocks:* network effects; multi-agency / multi-org deployments.
9. **Managed convenience tier** (optional hosted hub). *Unlocks:* a lower-friction entry point for non-sensitive teams; do not lead with it.

**Tier 4 — Ecosystem and distribution.**
10. **Integrations** (LangGraph/CrewAI adapters, ServiceNow/Jira approval bridges, SIEM export). *Unlocks:* meeting buyers where they are; reduces "rip and replace" friction.
11. **Certification / partner program.** *Unlocks:* recurring assurance revenue and channel distribution.

---

## 8. Recommendations (what the repo should expand into)

1. **Position as the audit-grade, sovereign decision layer — not another agent framework or tracer.** Own the *signed, arbitrated decision* as the unit of record.
2. **Adopt open-core, self-hosted-first.** Keep the core free and complete; monetize enterprise assurances. This matches both the market's proven models and the project's sovereignty ethos.
3. **Lead with the government/defense and BFSI beachhead**, where self-hosting is mandatory and compliance is urgent.
4. **Ship non-custodial, hardware-backed signing next** — it is both the biggest product risk and the flagship enterprise feature.
5. **Build compliance-evidence packs** (EU AI Act / ISO 42001 / SOC 2) — this converts the ledger from a technical feature into a budget-line purchase.
6. **Price the Business tier at ~$2,499/mo (Langfuse anchor) and the Sovereign tier at $50k–$500k+/yr**, justified by compliance exposure.
7. **Keep the Community edition genuinely free and complete** so it remains the distribution engine.

---

## 9. Sources

- Mordor Intelligence — *Agentic AI Orchestration & Memory Systems Market* (size, CAGR, deployment segments, drivers/restraints, regional shares).
- Grand View Research — *AI Governance Market* (size, CAGR, on-premises largest deployment share, government & defense largest vertical, solution/large-enterprise shares).
- Dataintelo — *Human-in-the-Loop AI Market* (size, CAGR, component/deployment/end-user/regional shares, enterprise contract norms, EU AI Act penalty context).
- Precedence Research — *Sovereign AI Infrastructure Market* (size, CAGR, on-premises and government dominance, Europe share, drivers).
- TrueFoundry — *LangGraph Pricing* (LangGraph free/MIT; LangSmith tiers, overage, LCU/LSU, deployment-run pricing, Enterprise-only self-hosting).
- Inference.net — *LangSmith Pricing* (LangSmith confirmation + Langfuse/Arize/Braintrust/Helicone comparison tiers).
- CrewAI — *Pricing* (free tier; Enterprise governance, VPC/own-infra deployment, onboarding).
- Linux Foundation / Serena — *State of Commercial Open Source 2025* (25 years of VC data across 800 companies; commercial open source outperformance).
- DreamFactory — on-premises LLM adoption statistics (on-prem share, cost/latency advantages, government AI infra spending).
- European Commission — *EU AI Act* (penalties up to EUR 30M or 6% of global turnover; human-oversight and record-keeping obligations).

*Figures are reported as published by the cited sources; market-research estimates vary by methodology and are used here for direction and order-of-magnitude, not precision.*
