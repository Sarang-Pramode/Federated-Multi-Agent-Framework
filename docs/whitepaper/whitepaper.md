---
title: The Federated Enterprise Agent Platform
subtitle: Architecture, adversarial design rationale, runtime guardrails and capacity engineering
kicker: White Paper v1.0
lead: This document argues for a specific shape of enterprise agent platform, one where independently owned domain agents are composed by a deliberately thin central runtime, where authority is deterministic rather than inferred, and where the fast path runs on quantized models inside the estate while frontier reasoning is reserved for the small fraction of turns that genuinely need it.
lead2: It is written adversarially. Each competing design is given its strongest form before it is criticised, every claim is paired with the observation that would falsify it, and one chapter is spent entirely on where this architecture is worse than the alternatives.
author: Sarang Pramode
version: Version 1.0
date: August 2026
status: Technical design document, for review
running_title: Federated Enterprise Agent Platform | v1.0
footer_left: Federated Enterprise Agent Platform, v1.0
scope: All hardware, latency and throughput figures in this document are third-party published values or explicitly modelled estimates. They are starting points for capacity planning, not guarantees. Chapter 23 gives the exact commands to re-measure every one of them on your own workload.
---

# Position {#part-position}

Part I states the claim, defines the problem precisely enough to be argued with, and grounds the rest of the document in a working prototype whose artefacts are named throughout.

## Executive Summary {#ch-exec}

An enterprise that wants conversational and agentic access to its own capabilities faces a structural problem long before it faces a modelling problem. The capabilities live in different systems, are owned by different teams, change on different release cadences, carry different regulatory obligations, and are correct according to rules that only their owning team can state authoritatively. Any architecture that requires those teams to converge on a single prompt, a single deployable, or a single release train is not solving the enterprise's problem; it is asking the enterprise to reorganise itself around a model.

This document argues for federation with a thin centre. Each business domain publishes a versioned agent that owns its own prompts, skills, tools, evaluation rubrics and deployment lifecycle. A central runtime, owned by a platform team, does five things and refuses to do more: it classifies the request, discovers which declared capabilities are eligible, plans the smallest sufficient sequence of calls, enforces authority deterministically, and composes a response that has passed output validation. Everything else, including the semantics of any business rule, belongs to a domain.

Three design commitments distinguish this from the general idea of "multi-agent".

The first is that **discovery is closed-world and independently audited**. A capability is reachable if and only if it appears in a published, hash-identified bundle, and an auditor that is not the changing team recomputes that property on every change. In the reference implementation this is the `reachability-closed` check, a set comparison whose failure detail reads "Central can reach a surface that is not identical to the published bundle." This is what makes targeted evaluation sound rather than merely cheap: the blast radius of a change is a computable set, not an act of judgement by the person who made the change.

The second is that **the model never holds authority**. Entitlement, limits, idempotency and write permission are decided by deterministic code reading structured state. A model proposes; a policy engine disposes. This is not a stylistic preference. It is the only way to answer a regulator's question about why a specific customer was allowed to perform a specific action with a reproducible artefact rather than a probability distribution.

The third is that **model capability is tiered, and the fast path is local**. Roughly two thirds of production turns should be resolvable with no model at all. Most of the remainder need a small quantized model, served inside the estate, answering in tens of milliseconds. Frontier reasoning is reserved for cross-domain decomposition, contested policy interpretation and plan repair, which together should account for a few percent of turns. Chapter 15 works the counterfactual in detail: routing the same journey's control path through a frontier API instead costs roughly 458 ms versus 2,115 ms end to end on identical domain work, a factor of about 4.6, and buys a set of second-order liabilities that latency alone does not reveal, including shared provider quota coupling user traffic to evaluation traffic, and raw utterances leaving the estate on exactly the hop where capability was gained least.

The document then does the work that architecture papers usually skip. Part II gives each rejected alternative its strongest form and states the specific mechanism by which it fails at scale, along with the observation that would prove the criticism wrong. Chapter 11 is an honest accounting of what this design costs: additional network hops on every journey, a genuinely harder debugging story, a platform team headcount floor that does not amortise below a certain scale, and a new control-plane dependency that becomes a correlated failure mode. Part IV converts a business number into a GPU count through an explicit chain of assumptions, sizes three deployment tiers, and states the accuracy price of each quantization format rather than hiding it. Part V covers assurance, and Part VI is the practical residue: anti-patterns, a phased roadmap, and a question bank for design review.

The intended outcome is not agreement. It is that a technical audience can locate precisely where they disagree, and know what measurement would settle it.

> **Design rule.** Prefer the fewest reasoning hops that still preserve domain autonomy, enforceable authority and independent deployability. Every additional hop must be justified by a capability that cannot be obtained more cheaply, and every model call must be justified by a decision that deterministic code cannot make.

::: figure src=reference-architecture.svg id=fig-arch width=full
The reference architecture. The synchronous request path is deliberately short and owned end to end by the platform team. Control planes on the left are what make federation governable rather than merely distributed. The model plane on the right is tiered, with the fast path resident in the estate and frontier capacity reserved for escalation. Note what is absent: no path by which one domain calls another, and no point at which a model grants itself authority.
:::

## The Problem, Stated Precisely Enough to Argue With {#ch-problem}

### What the enterprise actually has {#sec-what-exists}

Before discussing agents it is worth being concrete about the substrate. A large financial services, telecommunications or retail organisation typically has between thirty and several hundred business capabilities that a customer might reasonably ask about. Each is implemented across systems of record of varying age, wrapped in services of varying quality, and governed by rules that are partly in code, partly in policy documents, and partly in the heads of the four people who have owned the domain for a decade.

Three properties of this substrate drive the architecture, and all three are usually understated in agent design discussions.

**Ownership is real and it is not going away.** The team that owns rewards accrual is accountable for whether a customer is told the correct multiplier. That accountability is contractual, sometimes regulatory, and it does not transfer to a platform team merely because the platform team now operates the interface through which the customer asks. Any design that separates the accountability for an answer from the ability to change how that answer is produced will fail, not technically but organisationally, and the failure will present as a queue of unresolved tickets rather than as an outage.

**Cadence is heterogeneous by necessity.** A payments domain under a scheme mandate may ship weekly with heavy change control. A marketing offers domain may want to ship several times a day. A core banking integration may ship quarterly because its downstream dependency does. Forcing these onto a common release train does not make the slow ones faster; it makes the fast ones slow and creates an incentive to bypass the platform entirely.

**Correctness is domain-local and often surprising.** The reference implementation encodes a deliberately small example of this: restaurant purchases earn a 3x multiplier and grocery purchases earn 2x, so a $100 restaurant transaction earns 300 points. That rule is trivially simple and yet an incorrect prompt reduced it to the grocery multiplier and produced a confidently worded answer of 200 points. Nothing about that answer was malformed, unsafe, off-topic or ungrounded in the retrieved transaction. It was simply wrong in a way that only the rewards domain could adjudicate. Multiply that by a hundred domains, each with rules an order of magnitude more intricate, and the futility of centralising semantic correctness becomes clear.

### What the enterprise wants {#sec-what-wanted}

Stated as jobs to be done rather than as features, the platform must let a customer or employee express an intent in natural language and receive an answer that is correct according to the owning domain, permitted according to policy, attributable to a specific chain of decisions, and delivered inside a latency budget that keeps the interaction conversational. It must let a domain team add or correct capability without coordinating with any other team. It must let a governance function answer, after the fact and without the implementation team's cooperation, what the system was permitted to do at a given moment and why a specific decision was taken. And it must let a finance function attribute cost to journeys rather than to an undifferentiated model bill.

These are ordinary distributed-systems requirements. That observation is the point of this document. The novelty of language models has encouraged a great deal of architecture that would be rejected immediately in any other domain, and the discipline this design applies is mostly the recovery of ordinary practice: explicit contracts, bounded blast radius, deterministic authority, independent verification, per-dependency timeouts, and capacity planning from measured load.

### The three forces that decide the architecture {#sec-forces}

Every design decision in this document can be traced to a tension between three forces, and most disagreements about agent architecture are really disagreements about their relative weight.

**Latency is a product constraint, not an engineering preference.** Conversational interaction degrades sharply once the first token is delayed beyond roughly a second, and abandonment rises steeply after that. This is a hard budget that must be divided among identity, guardrails, routing, domain work, validation and composition. Chapter 13 divides it explicitly. The consequence that most architectures resist is that model calls on the critical path are expensive in the currency that matters most, so the number of them must be minimised rather than merely optimised.

**Change safety is the dominant long-run cost.** A platform that cannot absorb a domain change without a full-system regression will either accumulate an unaffordable evaluation bill or stop evaluating properly. Chapter 26 develops this, but the structural conclusion appears early: the architecture must make the blast radius of a change computable, because only then can evaluation be targeted without being negligent.

**Autonomy is what makes the platform adoptable.** If joining the platform costs a domain team its release independence, the platform's growth is capped by the platform team's capacity, which is precisely the bottleneck federation exists to remove.

::: figure src=pattern-comparison.svg id=fig-patterns width=full
The three candidate shapes, with the mechanism of failure named in each panel rather than left implicit. Panel C is a superset of the others: a bounded domain may legitimately be implemented as panel A behind its agent card, and two consenting peers may exchange messages directly if their contract says so. What panel C adds is an owner of the end-to-end deadline, a single trace root, and an artefact stating what the system is permitted to do.
:::

## Scope, Audience and How to Read This {#ch-scope}

### Audience {#sec-audience}

This document is written for the people who will be asked to sign off on the design or operate it: enterprise and solution architects, platform and ML infrastructure engineers, heads of engineering deciding whether to fund a platform team, and risk, security and governance functions who need to know where their controls attach. It assumes familiarity with distributed systems and with the practical behaviour of language models, and it does not explain what a transformer is.

### What is in scope {#sec-in-scope}

The architecture of the request path and the control planes around it; the division of responsibility between the centre and the domains; the placement, layering and evaluation of input and output guardrails; the model tiering strategy and the escalation policy that governs it; hardware sizing from a business load figure through to a GPU count; the engineering capabilities required to build and keep the thing running; and the assurance apparatus that makes any of it defensible.

### What is deliberately out of scope {#sec-out-scope}

Vendor selection, procurement and commercial terms. Specific framework choices, which change faster than this document could track and which the architecture is designed to survive. Model pre-training and the construction of foundation models. Data platform architecture beyond the points where the agent platform touches it. And organisation design, except where an architectural choice has an unavoidable organisational consequence, in which case the consequence is stated.

### A note on the word "customer" {#sec-customer-word}

The sizing chapters use three load tiers described informally as fewer than ten customers, one thousand to five thousand, and more than fifty thousand. Because the word "customer" is ambiguous in exactly the way that ruins capacity planning, it is pinned down here and used consistently thereafter.

Table. How the informal tier labels map onto the quantity that actually determines hardware. Registered user counts are useful for a business case and useless for sizing; the chain in Chapter 18 converts between them explicitly. {#tbl-customer-word}

| Tier label | Informal reading | The quantity that sizes hardware | Approximate registered base implied |
|---|---|---|---|
| Tier S | Fewer than 10 customers | Fewer than about 40 peak concurrent assisted sessions | A few thousand highly engaged pilot users, or about 130,000 at the engagement rates assumed in Chapter 18 |
| Tier M | 1,000 to 5,000 concurrent | 1,000 to 5,000 peak concurrent assisted sessions | Roughly 3 to 17 million registered users at those same rates |
| Tier L | More than 50,000 customers | More than 50,000 peak concurrent assisted sessions | Above 160 million at those rates, or tens of millions where engagement is far higher |

The tier that matters is the middle column. Two organisations with identical registered user counts can differ by an order of magnitude in concurrent sessions, and the ratio between them is the single assumption most worth measuring early. The right-hand column is therefore the least reliable in the table, and it is included only to show how wide the range is: it is computed from one specific chain of engagement assumptions, stated and worked in Chapter 18, and an organisation whose users engage twice as often needs half the registered base for the same hardware.

### How to read this document {#sec-how-to-read}

Part I establishes the position. Part II is the argument, and is the part to read first if you are inclined to disagree, particularly Chapter 11, which lists the costs of this design without mitigation. Part III is the runtime design and is the most directly implementable material. Part IV is the sizing work and is written to be used as a worksheet rather than read once; Chapter 23 in particular exists so that its own numbers can be replaced with measured ones. Parts V and VI cover assurance and practice.

Every quantitative claim in this document falls into one of three categories, and each is labelled where it appears: **measured** in the reference implementation, **third-party published** with a citation, or **modelled** from stated assumptions. There are no unlabelled numbers, and no figure in this document should be used to buy hardware before Chapter 23 has been executed against the actual workload.

## The Reference Implementation {#ch-reference-impl}

### What exists and what it is for {#sec-what-prototype-is}

The architecture in this document is accompanied by a working prototype: a Next.js console that walks an audience through twelve steps, each of which exercises one control surface of the platform and produces a named artefact. It is explicitly a visual-first prototype. Guided Demo Mode replays a deterministic event stream through the same reducer and the same components that a live backend would drive, with a mock transport that emits most events 220 ms apart and evaluation or auditor check events 70 ms apart so that a room can follow them. Live Mode is reserved for the phase-two services, which the prototype's configuration anticipates as a central runtime and two domain services alongside the interface.

Being precise about what a prototype proves is a matter of professional hygiene, so it is stated plainly. The prototype demonstrates that the control surfaces exist, that the seams fall in defensible places, and that the platform's claims are expressible as artefacts a reviewer can inspect. It demonstrates nothing whatsoever about throughput, tail latency or cost, because it performs no inference. Every performance number in Part IV is third-party or modelled, and is labelled as such.

### The twelve steps and the claims they make falsifiable {#sec-twelve-steps}

The value of the demonstration is not that it works. It is that each step converts an architectural assertion into something an observer could catch being false.

::: figure src=demo-steps.svg id=fig-demo width=full
The twelve steps, the concrete artefact each one produces, and the claim it makes testable. The most important row is step 7: a semantic regression that is caught not by a general-purpose safety filter but by a domain evaluation case selected automatically from the shape of the change.
:::

**Steps 1 to 4 establish that capability is discovered rather than shipped.** In step 1 the central runtime is running with no domain connected. A customer asks how many points they have, the planner runs, and the trace completes in 48 ms with a degraded status and the answer "No available domain capability can answer this request." This is the single most useful frame in the demonstration, because it shows the centre with its domain knowledge removed and therefore shows exactly how much domain knowledge the centre holds, which is none.

In step 2 the Rewards domain publishes a bundle. The centre discovers an agent card declaring version 1.0, prompt version 1.0 with fingerprint `8ab1`, a protocol interface of `A2A v1.0 / JSON-RPC`, a bundle hash of `m-rew-10`, three skills, and two tools with schema hashes `t4c1` and `t8d2`. Discovery does not confer trust. The platform selects an onboarding suite of intent and rewards smoke tests, runs five cases, and only then hands the result to a rule-based auditor which runs four checks and returns a verdict of `ATTESTED`. Step 3 replays the identical customer sentence from step 1 and it now routes through the planner to the Rewards agent to `get_points_balance`, returning "You have 12,500 points." No central code changed between steps 1 and 3. Step 4 repeats the whole gate for the Transactions domain and bundle `m-txn-10`, which matters because it shows the gate is a rule applied uniformly rather than a courtesy extended to the first domain.

**Step 5 establishes that composition is a central responsibility.** The cross-domain question about a Demo Bistro transaction produces a trace in which the planner fans out to Transactions, which returns transaction `T1001` for $100 in the restaurant category, and then to Rewards, which applies the 3x multiplier, yielding 300 points. The structural point is visible in the trace shape rather than in the answer: there is no span in which Transactions calls Rewards. The two domains remain unaware of each other, which is what allows either to be replaced without renegotiating with the other.

**Steps 6 to 8 are the heart of the argument.** In step 6 the Rewards team independently swaps its prompt. The platform does not receive a declaration of what changed; it compares runtime snapshots and observes the fingerprint move from `8ab1` to `91fd`, prompt version 1.0 to 1.1. From the change type alone it selects four suites: `intent`, `rewards_regression`, `cross_domain` and `response_judge`.

In step 7 those suites run. Seventeen of eighteen cases pass. Case `c13`, "Cross-domain Rewards Calculation", expected `300 points` and observed `200 points`, with the recorded reason "Bad prompt applied grocery 2x instead of restaurant 3x." The release status becomes `REGRESSION_DETECTED`, and the auditor withholds attestation because its `eval-executed` check requires an evaluation verdict of `PASS`.

It is worth dwelling on what kind of defect this is, because it is the defect class that general guardrails cannot see. The answer "Your Demo Bistro purchase earns 200 points" is well formed, on topic, non-toxic, free of injected instructions, grounded in a real transaction that was really retrieved, and confidently phrased. Every input rail and every generic output rail passes it. It is caught only because a domain-owned expectation about a domain-owned rule was selected for execution by a platform-owned policy triggered by a change the platform detected itself. Remove any one of those four properties and the wrong answer reaches the customer.

Step 8 closes the loop. The Rewards team ships a corrected prompt, the fingerprint moves `91fd` to `c3e4` and version 1.1 to 1.2, the same four suites re-run, all eighteen cases pass, and attestation is granted. No central change was involved in either the failure or the repair, which is the autonomy claim demonstrated rather than asserted.

**Steps 9 and 10 establish that capability grows from the edge.** Rewards registers a new tool, `get_expiring_points` with schema hash `t2e9`, and the platform selects tool-selection and rewards regression suites. Then Rewards adds an `expiring_points` skill. Step 10 shows the before and after explicitly: the question "When do my points expire?" is unsupported, then the skill lands, then the identical question routes through Rewards to `expiring_points` to `get_expiring_points` and returns a grounded answer. Both changes are confined to one domain's bundle, moving it to `m-rew-12`.

**Step 11 establishes fault containment.** Rewards is taken offline. A Transactions-only question succeeds normally, completing in 130 ms. The cross-domain question then produces a trace in which the Transactions work succeeds and the Rewards delegation span fails after 12 ms with an error status, and the trace as a whole is marked degraded rather than failed. The customer receives a named partial: the transaction was found, and Rewards is unavailable so points cannot be calculated right now. Two properties are on display. The failure is fast, because a per-dependency budget bounded it rather than a global timeout absorbing it. And the failure is legible, because the response says which capability is missing instead of silently omitting it, which is the difference between a degraded answer and a misleading one.

**Step 12 states the attested end state.** Rewards at version 1.2, prompt `c3e4`, bundle `m-rew-12`, with the reachable surface confirmed identical to the published bundle.

### The auditor, and why it is not a model {#sec-auditor}

The auditor runs four checks on every change, and their construction is deliberate.

Table. The four auditor checks in the reference implementation, with the comparison method each uses. Every one is a hash comparison, a set comparison, or a rule, and none involves a model. {#tbl-auditor}

| Check id | What it establishes | Method | Failure meaning |
|---|---|---|---|
| `manifest-published` | A bundle with this hash was actually published and is the subject under audit | hash comparison | The artefact under review is not the artefact that was published |
| `reachability-closed` | The skills and tools central can reach are exactly the published set, with nothing missing and nothing extra | set comparison | Central can reach a surface that is not identical to the published bundle |
| `eval-coverage` | Every suite required for this change type was selected | rule | The evidence gathered does not cover the change that was made |
| `eval-executed` | The selected suites ran against this manifest and returned a passing verdict | rule | Evidence exists but does not support release |

The verdict is `ATTESTED` only if all four pass, and `WITHHELD` otherwise.

Two aspects of this deserve emphasis because they are the parts most often argued with. First, the auditor is rule-based rather than model-based, which is a constraint accepted on purpose. A model-based auditor would be more flexible and would be able to comment on things a rule cannot, and it would also be non-deterministic, expensive to run on every change, and impossible to defend in a post-incident review, because the answer to "why did it pass" would itself be a generation. A rule-based verdict is reproducible, cheap enough to run on every change without negotiation, and settles arguments rather than starting them.

Second, `reachability-closed` is the check that makes the rest of the architecture load-bearing. It is a closed-world assertion: not merely that everything published is reachable, but that nothing else is. Without it, "we only evaluated the affected surface" is an assumption. With it, that sentence is a computed property, and targeted evaluation becomes a sound practice rather than an economising one.

### What the prototype does not yet do {#sec-prototype-gaps}

Stated plainly, so that no reader has to discover it themselves. There is no inference: the events are replayed, so no latency figure in the prototype reflects model behaviour. There are only two domains, so the coordination costs that appear at twenty are not exercised. There is no durable execution engine, so long-running and human-in-the-loop journeys are described in this document but not demonstrated. The guardrail cascade of Chapters 16 and 17 is designed here and not implemented there. And the prototype runs one model family throughout, `gpt-4.1-mini` in the recorded configuration, so the tiering strategy of Chapter 14 is likewise architecture rather than demonstration. Chapter 31 sequences the work to close these gaps in the order that retires the most risk first.

# Why This Design, Adversarially {#part-adversarial}

Part II is the argument. Each competing design is stated in its strongest form, credited with the cases where it genuinely wins, and then criticised by naming the specific mechanism through which it fails. Every criticism is paired with the observation that would refute it. Chapter 11 turns the same treatment on the design this document advocates.

## How to Argue About Architecture {#ch-how-to-argue}

Architecture debates go badly for a predictable reason: the participants compare a well-understood incumbent against an idealised alternative, or an idealised incumbent against a caricatured alternative, and no observation is nominated in advance that could settle the disagreement. The chapters that follow adopt three rules to avoid that.

**Steelman first.** Each alternative is described as its best advocates would describe it, including the cases where it is simply the correct choice. An argument that only defeats the weak version of a position has established nothing.

**Name the mechanism.** "It does not scale" is not a criticism. A criticism identifies the specific quantity that grows, what it grows with, and what breaks when it does. Change surface growing linearly with capability count is a mechanism. Trust edges growing quadratically with peer count is a mechanism. Prefill tokens growing with catalogue size is a mechanism.

**State the falsification.** Each chapter ends by naming what would have to be true for the criticism to be wrong. This is the discipline that separates an architectural position from a preference, and it also makes the document useful in review: a reader who believes an alternative is being treated unfairly has a concrete experiment to propose.

### The criteria {#sec-criteria}

Six criteria are used consistently, chosen because each one is observable rather than aesthetic.

Table. The evaluation criteria used throughout Part II, and how each is observed rather than asserted. {#tbl-criteria}

| Criterion | Question it answers | How it is observed |
|---|---|---|
| Change surface | When one team changes one thing, how many components must be re-verified? | Count the components a change-impact analysis returns, and check whether that count is computed or estimated |
| Blast radius | When one component fails or misbehaves, how many journeys degrade? | Fail one component in a controlled test and count affected journeys |
| Authority integrity | Can a model cause an action it was not entitled to cause? | Attempt it; if the answer depends on prompt wording, authority is not enforced |
| Attribution | For a given production request, can you reconstruct every decision and its cost? | Pick a request id at random and try |
| Deployability | Can one team ship without coordinating with another? | Measure elapsed time from merge to production for a single-domain change |
| Deadline ownership | Who is accountable for the end-to-end latency the user experiences? | Ask for a name; if there is not one, there is no budget |

### On premature decomposition {#sec-premature}

One concession belongs at the front, because it is the most common and most expensive way to misapply this document. Decomposing a system before its boundaries are understood is worse than not decomposing it. The boundaries in a federated agent platform are the domain agent cards, and a card drawn around the wrong capability set is expensive to move: it has consumers, versions, evaluation suites and an audit history. A team that does not yet know which capabilities belong together should build a single agent, keep it clean, and split it when the seams become obvious from the change log rather than from a diagram. Chapter 31 sequences the roadmap accordingly, starting with in-process modularity and moving to service federation only when a named pressure demands it.

> **Decision.** Federation is not a starting position. It is a response to specific, observable pressures: more than three teams needing independent cadence, a regulatory requirement for reproducible authority decisions, a change surface that has already made full regression unaffordable, or a fault-containment requirement that shared-process modularity cannot meet. Adopt it when at least one of those is true and you can name which.

## Alternative A: The Single Agent With Skills {#ch-single-agent}

### The design in its strongest form {#sec-single-agent-what}

One agent process holds one system prompt. Every capability the organisation exposes appears in that prompt as a skill: a name, a description of when to use it, a parameter schema, and often a few examples. The agent receives the user's message, selects a skill, calls the corresponding tool, and answers. Modern frameworks make this genuinely elegant, and the operational story is the simplest of any option in this document: one deployable, one prompt file, one place to look when something is wrong, one trace, no network hops between reasoning and capability selection.

It also has a real latency advantage that is often overlooked in these comparisons. Skill selection happens inside the same model call that produces the plan, so there is no separate routing round trip, and there is no service boundary between the centre and the capability. On a request that a federated design would resolve in 460 ms, a well-tuned single agent with a small catalogue can plausibly reach 380 ms, because it has removed two network hops and one model call.

**Where it is simply the right answer.** A product owned by one team. A capability catalogue in the low single digits that is not expected to grow quickly. A prototype whose purpose is to discover what the boundaries are. An internal tool where attribution requirements are informal. In these cases federation adds control planes that solve problems the system does not have, and this document's design would be the wrong recommendation.

### Mechanism one: change surface grows with the catalogue, and it grows in a shared mutable global {#sec-single-agent-change}

The system prompt is a shared mutable global variable. That framing is not rhetorical; it has the same consequences that shared mutable state has anywhere else, and they are worth spelling out.

When the rewards team needs to correct its multiplier language, it edits a region of a file that also governs how transactions are looked up, how out-of-scope requests are refused, and how the agent decides between two similar capabilities. There is no mechanism that confines the effect of the edit to rewards, because the model attends over the whole prompt. The rewards team therefore cannot know, from the diff alone, what else it might have changed. Neither can anyone else. The only sound response is to re-verify everything, which is exactly what the reference implementation's federated design avoids: in the federated case a prompt change inside Rewards moved one bundle hash from `m-rew-11` to `m-rew-12` and triggered four named suites, and the auditor independently confirmed that nothing outside that bundle became reachable.

::: figure src=change-surface.svg id=fig-change width=full
The same change under three architectures. The difference is not that federated teams are more careful; it is that a manifest plus an independent reachability check turns "what changed" into a computable set. Without that artefact, the honest engineering answer to "what must we re-test" is "everything", and the practical answer becomes "whatever we have time for", which is not the same thing.
:::

The second-order consequence is worse than the first. Because full regression is expensive, teams reduce it. Because reductions are chosen by the person who made the change, they are chosen by the person least able to see the change's non-local effects, and with the strongest incentive to conclude the change is safe. The failure mode is not that a team is dishonest. It is that a reasonable engineer, asked to select the evidence that their own change is harmless, will select evidence consistent with that belief, and there is no artefact contradicting them.

### Mechanism two: prefill cost grows with capability count, on every turn, whether or not the capabilities are relevant {#sec-single-agent-prefill}

Every capability description occupies context on every request. A moderately documented capability, with a description, a parameter schema and one example, occupies on the order of 150 to 250 tokens. Forty capabilities therefore add roughly 6,000 to 10,000 tokens of prompt that must be processed before the first output token can be produced, on every single turn, including the seventy percent of turns that concern exactly one capability.

The following is **modelled**, from the stated assumption of a single-stream prefill rate around 25,000 tokens per second for an 8B-class model on one H100 at FP8. It is offered as arithmetic to be redone with measured numbers, not as a benchmark.

Table. Modelled prefill contribution to time to first token as the capability catalogue grows, at 200 tokens per capability description and 25,000 tokens per second single-stream prefill. The final column is the fraction of a 500 ms conversational budget consumed before any reasoning has happened. **Modelled**, not measured. {#tbl-prefill}

| Capabilities in prompt | Catalogue tokens | Modelled prefill contribution | Share of a 500 ms budget |
|---|---:|---:|---:|
| 4 | 800 | 32 ms | 6% |
| 12 | 2,400 | 96 ms | 19% |
| 40 | 8,000 | 320 ms | 64% |
| 120 | 24,000 | 960 ms | 192% |

Prefix caching mitigates this substantially and should always be used, but it mitigates the compute rather than the consequence. Two effects survive caching. The first is that the catalogue still occupies context window, competing with conversation history and retrieved evidence for the space that actually improves answers. The second is instruction dilution: as the number of simultaneously active instructions grows, adherence to any individual instruction degrades, and the degradation is not uniform. It falls hardest on the instructions that discriminate between similar capabilities, which is precisely the routing decision the prompt exists to make. A federated design confronts the model with a shortlist of two or three eligible capabilities produced by a cheap deterministic or Tier 1 step, so the discrimination problem the model faces is small regardless of how large the organisation's catalogue becomes.

### Mechanism three: prompt shadowing, the failure that domain evaluation cannot see {#sec-shadowing}

This mechanism deserves its own treatment because it is specific, it is common, and it is nearly invisible to the obvious tests.

Consider the reference implementation's rewards rule. Suppose the central prompt contains, from some earlier iteration, the sentence "point multipliers are 2x for everyday spending categories". Suppose the rewards team then discovers its multiplier bug and corrects its own guidance to state the restaurant 3x rule explicitly. In a federated architecture the corrected guidance lives inside the Rewards bundle, is the only rewards guidance in play, and the corrected behaviour is confirmed by case `c13` expecting 300 points.

In a single-agent architecture both statements are in the same prompt. Which one wins is a function of ordering, phrasing, recency and the model version, none of which the rewards team controls or can test against, because the rewards team does not own the file. Worse, the rewards team's own evaluation may pass, because the team will naturally test the capability in isolation with a prompt fragment that omits the contradicting sentence. The bug surfaces in production, intermittently, and diagnosis requires someone to notice a contradiction between two paragraphs written months apart by different people. This is a well-known category of defect in shared configuration, and language models make it harder to detect rather than easier, because the system does not fail loudly on contradictory instructions; it silently picks one.

### Mechanism four: every domain release becomes a system release {#sec-single-agent-release}

Because there is one deployable and one prompt, there is one release. A rewards correction and a transactions migration that happen to land in the same week are now coupled: they are tested together, released together, and rolled back together. The rewards team's urgent fix waits for the transactions team's risky migration to be ready, or the migration is rushed. Neither outcome is a technology problem, and neither is solvable by better tooling within this architecture, because the coupling is structural.

The observable consequence is a metric worth tracking in any organisation currently on this path: the elapsed time from a domain team's merge to that change being live, and specifically the fraction of that time spent waiting for other teams. When that fraction passes about a third, the architecture is imposing a tax that federation exists to remove.

### What would falsify this criticism {#sec-single-agent-falsify}

The criticism of the single-agent pattern is wrong if all of the following can be demonstrated. First, that routing accuracy over a catalogue of forty or more capabilities stays within about one point of the accuracy achieved over four, measured on a held-out set that includes near-miss pairs. Second, that a domain team can edit its own region of the prompt and merge without review by the prompt's owning team, with the effect of that edit confined provably to its own capabilities. Third, that the set of components requiring re-verification after a prompt edit can be computed from the diff rather than estimated. And fourth, that per-domain circuit breaking, quota and cost attribution can be implemented without a service boundary.

If those four hold, the single-agent design dominates on latency and operational simplicity and this document is recommending unnecessary machinery. In practice the first fails as catalogues grow, and the second fails for the reason described in Chapter 2: ownership is real, and a shared file has one owner.

## Alternative B: Peer to Peer, Without a Centre {#ch-peer-to-peer}

### The design in its strongest form {#sec-p2p-what}

Domain agents talk to each other directly. Rewards, needing a transaction, asks Transactions. Transactions, needing an entitlement decision, asks Policy. There is no orchestrator, no single point of failure, and no bottleneck team through which every new capability must pass. The topology is attractive on paper for real reasons: it removes the central team from the critical path of both requests and organisational change, it degrades gracefully in the sense that no single node's loss stops all communication, and it is a good model of how human organisations actually coordinate.

**Where it is genuinely the right answer.** Two systems with a stable, narrow, well-specified contract that has no reason to involve a third party. Cross-organisational settings where no participant can legitimately be appointed as the centre, which is the case protocols for agent interoperability are designed for. And workloads where quality is a statistical property of many attempts rather than a per-request guarantee, such as exploratory research pipelines, where emergent coordination is a feature.

### Mechanism one: nobody owns the end-to-end deadline {#sec-p2p-deadline}

This is the criticism that matters most, and it is not about the mean.

Each peer, reasonably, sets its own timeout for its own dependencies. No peer knows the user's remaining budget, because the budget was established at the edge and there is no mechanism carrying it. A chain of four or five delegations therefore has a latency distribution that is the convolution of independently chosen distributions, and the tail behaves much worse than intuition suggests. If each hop has a p99 of 400 ms, the chain's p99 is not 400 ms and it is not simply the sum either; it is dominated by the probability that at least one hop is slow, which rises with the number of hops. With four hops, the chance that none of them takes its p99 excursion is about 96 percent, so roughly one request in twenty-five experiences at least one worst-case hop, and that request has no mechanism to abandon the slow hop because no participant knows the deadline has already been exceeded.

The fix is a deadline propagated with the request and enforced at each hop against the remaining budget. That fix is exactly a central contract about how time is spent, and it requires someone accountable for setting the budget in the first place. The moment it exists, a centre exists.

### Mechanism two: no closed-world reachability, therefore no computable blast radius {#sec-p2p-reachability}

In the reference implementation, the auditor's `reachability-closed` check asserts by set comparison that the skills and tools the platform can reach are exactly the published set. That assertion is possible because there is one place through which delegation flows and one registry describing what may be delegated to.

In a peer topology, no participant can make that assertion, because reachability is a transitive property of a graph that no single node observes. If Rewards may call Transactions, and Transactions may call Policy, then Rewards can reach Policy, whether or not anyone intended it and whether or not Rewards is entitled to. Answering "what is this system permitted to do" requires collecting every peer's configuration and computing a transitive closure, which means it can only be answered as an offline audit exercise, which means it is stale by the time it is finished, which means it will not be done on every change. Consequently every claim of the form "we tested the affected surface" is unverifiable, and targeted evaluation stops being a sound practice and becomes an economy.

### Mechanism three: trust and compatibility edges grow quadratically {#sec-p2p-edges}

Each pair of communicating peers requires a contract, a version compatibility relationship, an authentication and authorisation relationship, an agreed error taxonomy, and a pair of integration tests. The number of such relationships is the number of edges in the communication graph.

Table. Relationship count as peer count grows, assuming a fully connected graph in the worst case and a realistic sparse graph at three connections per peer. The right-hand column is what actually breaks: each edge is an artefact somebody must own, version and test. **Modelled** from graph arithmetic. {#tbl-p2p-edges}

| Peers | Edges if fully connected | Edges at 3 connections per peer | Federated: hub relationships |
|---:|---:|---:|---:|
| 5 | 10 | 8 | 5 |
| 10 | 45 | 15 | 10 |
| 20 | 190 | 30 | 20 |
| 40 | 780 | 60 | 40 |

The honest version of this criticism acknowledges that real peer topologies are sparse, not complete, so the quadratic bound is a worst case rather than a forecast. But the middle column tells a story of its own: even sparsely connected, the number of pairwise artefacts exceeds the number of hub relationships and, more importantly, the relationships are heterogeneous. Twenty hub relationships are twenty instances of one contract shape, which can be tooled, validated and versioned uniformly. Thirty peer relationships are thirty bilateral negotiations, each with its own history.

### Mechanism four: delegation loops are emergent rather than designed {#sec-p2p-loops}

A calls B, B needs something and calls A. In a small deployment this is caught in review. In a deployment where each team independently decides its own dependencies, it appears as a production incident: a request that consumes resources on several nodes, produces no answer, and cannot be attributed to any single team's change. Preventing it requires a hop budget carried with the request, cycle detection over a graph somebody maintains, or a rule that delegation may only flow in one direction. All three are central coordination mechanisms.

### Mechanism five: no trace root, so attribution becomes archaeology {#sec-p2p-trace}

The reference implementation's step 11 trace shows the property this mechanism destroys. One trace, one root, a Transactions delegation succeeding, a Rewards delegation failing after 12 ms, an overall status of degraded. A reviewer can see in one artefact what was attempted, what failed, how long it took and what the customer was told.

Distributed tracing across peers is achievable, and mature organisations do it. But it is achievable precisely to the extent that all peers agree on a propagation format, a span naming convention, a sampling policy and a collector. That agreement is a central standard, enforced centrally, or it does not hold; and partial adoption is close to worthless, because a broken chain in the middle of a trace hides exactly the hop that is usually at fault.

### What would falsify this criticism {#sec-p2p-falsify}

The criticism is wrong if a peer topology can produce, on demand and without an offline exercise: an artefact stating the closed set of actions the system may currently take; a named owner of the end-to-end deadline with a mechanism that enforces it at each hop; and a single trace, rooted at the user request, spanning five delegations with per-hop cost and status. If all three exist, the criticism fails on its own terms. It is also worth noting the likely consequence of building them: a registry, a deadline contract and a trace standard together constitute a control plane, and a peer topology with a control plane is the design this document advocates, described differently. At that point the disagreement is terminological rather than architectural, which is a good outcome.

## Alternative C: The Monolith Repository {#ch-monolith}

### The design in its strongest form {#sec-monolith-what}

All domains live in one repository and deploy as one artefact. There is no service discovery, no network partition between components, no version skew, and no distributed transaction. Refactoring across domain boundaries is a single atomic commit. Testing is straightforward because the whole system can be instantiated in one process. A junior engineer can read the entire request path in an afternoon.

These are large advantages and this document does not dismiss them. Most organisations that decomposed early regret it, and the literature on premature decomposition is more persuasive than the literature encouraging it. If the choice is between a well-maintained monolith and a distributed system nobody can debug, the monolith is the better engineering outcome.

**Where it is genuinely the right answer.** Fewer than about three teams. A domain model still in flux, where the correct boundaries are not yet known. A latency budget so tight that inter-service hops cannot be afforded. And any organisation without the operational maturity to run a distributed system, because a distributed system operated badly is strictly worse than a monolith operated well.

### Mechanism one: release coupling compounds with team count {#sec-monolith-release}

If a shared release requires every participating team's changes to be ready and passing, then the probability that a given release proceeds on schedule is the product of each team's readiness probability. Even at a generous ninety-five percent readiness per team, six teams yield about a seventy-four percent chance of an unblocked release, and twelve teams about fifty-four percent.

Table. Modelled probability that a shared release is unblocked, as team count grows, at two per-team readiness rates. The consequence is not the arithmetic itself but the behaviour it induces: teams begin batching changes to reduce the number of releases they must pass through, which makes each release larger and riskier. **Modelled** from independence assumptions, which are optimistic. {#tbl-release-coupling}

| Teams sharing the release | At 95% per-team readiness | At 90% per-team readiness |
|---:|---:|---:|
| 3 | 86% | 73% |
| 6 | 74% | 53% |
| 12 | 54% | 28% |
| 20 | 36% | 12% |

The assumption of independence is optimistic, because teams blocked by the same shared dependency fail together. The induced behaviour is the real cost: as the probability of a clean release falls, teams batch more changes into each attempt, which raises the risk of each attempt, which increases the change-control burden, which lengthens the cycle further. Organisations in this state usually describe the problem as insufficient test automation. More automation helps, and it does not address the coupling.

### Mechanism two: continuous integration wall clock grows with total capability {#sec-monolith-ci}

A monolith's test suite covers the whole system, so its wall-clock duration grows with the total capability of the organisation rather than with the size of any change. Parallelisation buys a constant factor and then runs into shared fixtures, database migrations and integration tests that cannot be parallelised safely. Eventually the suite takes longer than the desired release interval, and at that point one of three things happens: the interval lengthens, the suite is subsetted by hand, or the suite is subsetted by a heuristic nobody has validated. The second and third are the common outcomes, and both quietly abandon the guarantee that made the monolith attractive.

The federated alternative does not eliminate this cost; it partitions it. Each domain's suite grows with that domain, and the platform's contract suite grows with the number of contracts rather than with the behaviour behind them.

### Mechanism three: one dependency vulnerability forces a full-platform redeploy {#sec-monolith-cve}

A critical vulnerability in a transitive dependency requires the whole artefact to be rebuilt, re-tested and re-released, including domains that do not use the affected code path. Under a remediation deadline this pulls every team into an unplanned release, and the risk of that release is the risk of everything currently on trunk, not the risk of the patch. Independently deployed domains upgrade on their own schedule, and the blast radius of the emergency is the domains that actually use the dependency.

### Mechanism four: no independent scaling, and no independent failure {#sec-monolith-scaling}

One process means one resource envelope. A retrieval-heavy domain that wants large memory forces that memory allocation on every replica, including the replicas serving requests that never touch it. More seriously, the failure modes are shared: a thread pool exhausted by one domain's slow dependency starves every domain in the same process, a memory leak in one module degrades all of them, and a garbage collection pause caused by one domain's allocation pattern is experienced by every request in flight. There is no per-domain circuit breaker to open, because there is no boundary at which to open one.

::: figure src=failure-isolation.svg id=fig-isolation width=full
The same fault under two architectures, and the mechanisms that make the difference. Note that fault containment is not a property of drawing boxes with gaps between them. It is the presence of six specific mechanisms: per-dependency budgets, per-domain breakers, bulkheaded pools, named partial results, idempotent writes, and a pre-agreed degraded mode.
:::

### What would falsify this criticism {#sec-monolith-falsify}

The criticism is wrong if a monolithic repository can demonstrate that a single team's change reaches production within an hour of merge without any other team's involvement; that the test subset required for a given change is computed from the change rather than chosen by a person; that a memory leak or thread pool exhaustion in one module can be contained without restarting the others; and that one domain's resource requirements can be satisfied without imposing them on all replicas.

Modular monoliths with strict module boundaries, per-module test selection, trunk-based development and feature flags get closer to this than critics usually allow, and an organisation that achieves it has captured most of federation's benefits at much lower operational cost. It is worth noticing what such a system has become, though: independently releasable units with enforced boundaries and computed change impact. The remaining difference is process isolation, which is the subject of Chapter 10.

## Alternative D: Federated, But Ungoverned {#ch-ungoverned}

### The design in its strongest form {#sec-ungoverned-what}

This is the nearest neighbour to the design this document advocates, and therefore the most important alternative to treat carefully. Domains are independently owned and deployed. A central runtime routes. Each domain publishes a card describing its capabilities. Each domain owns its own evaluation suites, and runs them before release. There is no independent auditor, because each team is trusted to test its own work, which is the normal and correct default in software engineering.

The steelman is strong. Teams are competent and accountable. Adding an auditor implies distrust, creates a bottleneck, and duplicates work the domain team is better placed to do. Most successful microservice organisations operate exactly this way, and they do so successfully.

### Mechanism one: evidence selected by the changing team is not independent evidence {#sec-ungoverned-evidence}

The argument here is not about trust; it is about the structure of the task.

To select the right evaluation suites for a change, someone must know the change's non-local effects. The team making the change knows the change best and its non-local effects least, because non-local effects are by definition outside the team's area of ownership. So the team best placed to select evidence is, for this specific question, poorly placed. Add the ordinary incentive that suite selection happens under release pressure, and the result is not misconduct but a systematic bias: the selected evidence is consistent with the belief that the change is safe.

The reference implementation makes the alternative concrete. The platform detected the change itself, by comparing runtime snapshots and observing the prompt fingerprint move from `8ab1` to `91fd`. It selected the suites from the change type, by rule. Case `c13`, the cross-domain calculation, was in that selection because a prompt change in a domain participating in cross-domain journeys implicates those journeys. It is entirely plausible that a rewards engineer, having verified that balance lookups still work and the multiplier language reads correctly, would not have chosen a cross-domain composition test. That case is precisely the one that failed.

### Mechanism two: declared capability drifts from actual capability {#sec-ungoverned-drift}

Without a check that the reachable surface equals the published surface, the two diverge, and they diverge in the direction that matters. A tool is added for a debugging purpose and remains callable. A skill is deprecated in the card and remains wired. A parameter schema is widened in code and not in the card. Each divergence is individually harmless and locally rational. Collectively they mean the card is documentation rather than a contract, and every downstream property that depends on it, including the entire targeted evaluation argument, is unfounded.

The check that prevents this is cheap. `reachability-closed` is a set comparison between the published bundle and what the runtime can reach. It requires no model, no human judgement and no negotiation, and it runs in milliseconds. The reason to make it independent of the changing team is not suspicion, it is that a check a team runs on itself is a check that can be disabled under pressure by the same team, whereas a check in the release gate cannot.

### Mechanism three: nothing establishes that evidence was gathered against the artefact being released {#sec-ungoverned-artifact}

The `eval-executed` and `manifest-published` checks exist to close a gap that is easy to miss. A team can run a full evaluation suite, pass it, then make one more small change, and release. The evidence is real, the verdict is genuine, and neither pertains to the artefact that shipped. Binding the verdict to a manifest hash makes the gap closed by construction rather than by process discipline.

### What would falsify this criticism {#sec-ungoverned-falsify}

The criticism is wrong if an ungoverned federation can produce, for an arbitrary past release chosen by someone else: the exact set of reachable capabilities at that moment; the evidence gathered, bound to that artefact's hash; and the rule by which that evidence was selected. If those three artefacts exist and were produced without the changing team's participation, then governance is present and the label is the only thing in dispute.

The strongest genuine objection to this chapter is that the auditor becomes a bottleneck. That objection is answered by construction rather than by argument: because every check is a hash comparison, a set comparison or a rule, the auditor is a function in the release pipeline that completes in milliseconds and requires no human. It is a bottleneck in the same sense that a type checker is a bottleneck.

## Alternative E: In-Process Orchestration Versus Service Federation {#ch-in-process}

### The design in its strongest form {#sec-in-process-what}

Modern agent frameworks support multi-agent composition inside a single process. A supervisor agent delegates to sub-agents; each sub-agent has its own prompt, its own tools, and its own evaluation suite. The code is genuinely modular, ownership can be expressed through code ownership rules, and none of the modularity is imaginary.

The advantages over service federation are real and should not be minimised. Delegation is a function call rather than a network round trip, saving perhaps 2 to 15 ms per hop plus serialisation, which is material inside a 460 ms budget. There is no service mesh, no discovery infrastructure, no distributed tracing requirement, and no partial failure between the supervisor and the sub-agent. Development is faster because the whole system runs locally. For a small number of domains this is not merely acceptable, it is the correct choice, and Chapter 31's roadmap begins here deliberately.

### Mechanism one: modularity without fault isolation {#sec-in-process-fault}

The distinction that matters is between logical and physical boundaries. In-process composition gives a logical boundary: clear ownership of code and prompts, separate evaluation, independent reasoning about behaviour. It gives no physical boundary, and every failure mode that crosses a physical boundary is therefore shared.

One sub-agent whose retrieval step allocates aggressively causes garbage collection pauses experienced by every request in the process. One sub-agent that exhausts a shared connection or thread pool starves the others. One unhandled fault that terminates the process terminates all domains simultaneously. The reference implementation's step 11 depends entirely on a physical boundary: Rewards failed in 12 ms while Transactions continued to serve in 130 ms, because Rewards was a separate address space with its own budget and its own breaker. In one process, "Rewards is unavailable" is not a state the system can be in.

### Mechanism two: one dependency graph, one runtime, one version {#sec-in-process-deps}

All sub-agents share a single dependency resolution. Two domains that need different major versions of the same library cannot both be satisfied. One domain's need for a newer runtime forces the upgrade on all of them. Over a few years this produces the familiar outcome where the whole platform is pinned to the oldest constraint any single domain imposes, and the team that needs to move cannot.

### Mechanism three: no independent deployment, so no independent cadence {#sec-in-process-deploy}

Because there is one process, there is one deployment, which recreates Chapter 8's release coupling at a smaller scale. The mitigations are the same, feature flags and trunk-based development, and so are their limits: a flag controls whether new code runs, not whether new code is present, and shipping a domain's change still means shipping every other domain's current state.

### Mechanism four: no per-domain resource governance {#sec-in-process-quota}

A shared process cannot easily enforce that one domain uses at most a given share of CPU, memory, model quota or connections. The result is that a single misbehaving domain's blast radius is the whole platform, which is the property federation exists to prevent.

### What would falsify this criticism {#sec-in-process-falsify}

The criticism is wrong if an in-process design can demonstrate that one sub-agent can be restarted or disabled without affecting the others; that one sub-agent's memory and CPU consumption can be bounded; that two sub-agents can depend on incompatible library versions simultaneously; and that one team can deploy without shipping another team's current trunk state. Mechanisms exist that approach some of these, including separate class loaders, per-task resource accounting and in-process sandboxes. They approach process isolation by reimplementing it, usually with fewer guarantees and less mature tooling than the operating system provides.

## Where This Design Is Worse {#ch-worse}

Everything above criticises alternatives. This chapter applies the same standard to the design this document advocates, without mitigation and without a rebuttal paragraph after each item. A reader who finds this chapter more persuasive than Chapters 6 to 10 should not adopt the architecture, and that is a legitimate outcome of a design review.

### It adds latency to every request, forever {#sec-worse-latency}

Two to four network hops are added to each journey. At 2 to 15 ms per hop including serialisation, that is roughly 5 to 60 ms of additional p50 latency, and materially more at p99 where connection pool exhaustion, retries and cold TLS handshakes appear. This cost is paid on every request, including the large majority that would have been resolved identically by a single in-process agent. It never amortises and it cannot be optimised away, only reduced.

### Debugging is genuinely harder, and the tooling debt comes first {#sec-worse-debug}

A single-process failure is a stack trace. A federated failure is a distributed trace, and only if tracing was correctly instrumented in every service before the incident. When it was not, engineers correlate logs across services by timestamp, which is slow and unreliable. The investment in tracing, correlation identifiers, structured logging and span conventions must be made before it pays for itself, which means it must be made at exactly the moment the team is least able to justify it. Organisations that skip it end up with a distributed system and monolithic debugging practices, which is the worst combination available.

### There is a platform team headcount floor, and it does not amortise at small scale {#sec-worse-headcount}

Someone must own the central runtime, the registry, the auditor, the guardrail cascade, the trace collector, the evaluation runner and the model plane. That is realistically four to eight engineers with a specific and not-easily-hired skill mix, described in Chapter 25. Below roughly five domains, those engineers are a larger investment than the coordination cost they remove, and the honest recommendation at that scale is a modular monolith with a good test suite.

### The control plane is a new correlated failure mode {#sec-worse-control-plane}

Federation trades many small failure domains for a few shared ones. If the capability registry is unavailable, routing fails for every domain simultaneously, which is a worse failure than any single domain outage the architecture was designed to contain. The mitigations are known: aggressive caching of the registry with a last-known-good fallback, static routes for critical journeys, and a degraded mode that does not consult discovery at all. Each mitigation is additional machinery that must itself be built, tested and exercised, and an untested fallback path is not a fallback.

### Contract and versioning overhead is a real tax on small changes {#sec-worse-contracts}

Adding one field to one response is, in a monolith, a one-line change. In this architecture it is potentially a schema version, a manifest hash change, a compatibility decision, a card update and a contract test. That overhead is proportionally trivial for a large change and disproportionately heavy for a small one, and it creates a standing incentive to batch small improvements, which is the behaviour the architecture is supposed to discourage.

### Evaluation cost is partitioned but not reduced, and coordination cost is added {#sec-worse-eval}

Each domain runs its own suites, and the platform runs contract, routing and cross-domain suites on top. Total evaluation compute is often higher than a monolith's, not lower; what improves is that the cost of any single change is bounded and attributable. Cross-domain journeys are also harder to evaluate, because doing it properly requires either a shared test environment where several domains are simultaneously at known versions, or contract-level mocking that risks passing tests while production composition is broken.

### Cognitive load rises for everyone, including people who did not ask for it {#sec-worse-cognitive}

A new engineer joining a domain team must understand the agent card format, the manifest and hash scheme, the registry, the delegation protocol, the trace conventions and the evaluation gate before shipping their first change. In a monolith they read the code. This cost is paid on every onboarding and it is a real drag on the pace of small teams.

### Summary of when not to adopt this design {#sec-worse-when-not}

Table. Conditions under which this document's architecture is the wrong choice, with the recommendation that is better. Presented without qualification, because a design document that cannot say when it does not apply is marketing. {#tbl-when-not}

| Condition | Better choice | Reason |
|---|---|---|
| Fewer than three teams contributing capability | Modular monolith, or a single agent with skills | Platform team cost exceeds the coordination cost removed |
| Domain boundaries not yet stable | Single agent, split later | Agent cards are expensive to move once they have consumers and history |
| No requirement for reproducible authority decisions | Simpler architecture, keep the guardrails | Most of the control plane exists to serve attribution requirements |
| Latency budget under about 300 ms end to end | In-process composition | The hop budget alone can consume a fifth of the allowance |
| No operational capability for distributed systems | Monolith, invest in operations first | A distributed system run badly is worse than a monolith run well |
| Exploratory or research workload | Peer to peer, or a single agent | Emergent coordination is an asset when per-request guarantees are not required |

## The Comparison, Quantified {#ch-comparison}

The table below summarises Part II. It is deliberately blunt, and every column has been defined observably in Chapter 5 so that a reader who disagrees with a cell can say what measurement would change it.

Table. Comparison across the six criteria of Chapter 5, at a scale of roughly twenty domains and six contributing teams. Cells marked as modelled derive from the arithmetic in the chapters above. This table would look materially different at three domains, where the right-hand column's advantages largely disappear. {#tbl-comparison}

| Criterion | Single agent with skills | Peer to peer, no centre | Monolith repository | In-process orchestration | Federated with a thin centre |
|---|---|---|---|---|---|
| Change surface for one domain edit | Whole prompt, all capabilities | Unbounded, not computable | Whole artefact | Whole process | One bundle, computed by rule |
| Is blast radius computable? | No, estimated by the author | No, requires transitive closure | No, estimated | No | Yes, from the manifest plus reachability check |
| Blast radius of one component failing | All journeys | Unpredictable, depends on graph | All journeys | All journeys | Journeys using that domain only |
| Authority integrity | Prompt dependent | Duplicated per peer, divergent | Enforceable, if code is disciplined | Enforceable, if code is disciplined | Enforced at one deterministic chokepoint |
| Attribution for one request | One trace, low resolution | Requires archaeology | One trace | One trace | One trace, per hop cost and status |
| Independent deployability | No | Yes | No | No | Yes |
| Deadline ownership | Implicit, single process | Nobody | Implicit, single process | Implicit | Explicit, the platform team |
| Serial hops on the critical path | 1 | 3 to 6, unbounded | 1 | 1 | 2 to 3, bounded by policy |
| Added p50 network latency | 0 ms | 20 to 90 ms, modelled | 0 ms | 0 ms | 5 to 60 ms, modelled |
| Relationships to maintain at 20 units | 1 shared prompt | 30 to 190 edges, modelled | 1 artefact | 1 process | 20 hub contracts |
| Probability a shared release is unblocked at 6 teams | 74%, modelled | Not applicable | 74%, modelled | 74%, modelled | Not applicable, releases are independent |
| Platform team floor | None | None | None | Small | 4 to 8 engineers |
| Onboarding cost for a domain engineer | Low | Medium | Low | Low | High |
| Where it is the right answer | 1 team, small catalogue | Cross-organisation, research | Under 3 teams, unstable boundaries | Under 5 domains, tight latency | Many teams, attribution required |

Read across the bottom two rows before reading the rest. The federated design wins on the criteria that dominate long-run cost in a large organisation, and it loses on the criteria that dominate short-run velocity in a small one. That is the trade, stated as plainly as it can be, and any presentation of this architecture that does not concede the last two rows is not making an argument.

# Runtime Design {#part-runtime}

Part III is the implementable core: what the central agent does stage by stage and how its latency budget is divided, how model capability is tiered so that most turns never reach a large model, what happens to the same journey when the control path is moved to a frontier API, and how input and output guardrails are placed, layered and evaluated.

## Anatomy of the Central Agent {#ch-central}

### Five responsibilities, and the refusal of a sixth {#sec-central-five}

The central agent is the only component every request passes through, which makes it the most dangerous place in the architecture to put anything. Every responsibility it accumulates becomes a responsibility that cannot be changed without a platform release, cannot be owned by a domain team, and cannot fail without failing everything. The discipline is therefore negative as much as positive: the centre does five things, and the list of things it must never do is treated as part of the design rather than as an omission.

The five are classification, discovery, planning, authority enforcement and composition. Classification decides what kind of request this is and how much risk it carries. Discovery decides which declared capabilities are eligible, using the registry rather than any knowledge held in a prompt. Planning decides the smallest sufficient sequence of domain calls. Authority enforcement decides, deterministically, whether the identity behind the request may cause the effects the plan implies. Composition turns domain results into a response that has passed output validation.

Notice what these have in common. Each is a decision about the shape of the interaction rather than about the content of any domain. None of them requires knowing what a rewards multiplier is, and the reference implementation demonstrates this by removing every domain from the platform and observing that the centre degrades to a truthful refusal in 48 ms rather than answering badly.

> **Design rule.** If a change to the central agent would be required in order to add, correct or remove a business rule, the boundary has been drawn in the wrong place. The centre may learn that a capability exists; it may never learn what the capability means.

### Stage by stage, with a budget {#sec-central-stages}

A budget that is not divided is not a budget. The following division is the one this document defends, and it is stated as a target rather than a measurement so that a reader can dispute individual lines.

::: figure src=central-pipeline.svg id=fig-pipeline width=full
The central agent decomposed into stages, with the p50 budget each stage is allowed and the model tier it uses. Two features of the diagram carry most of the argument: the critical path contains at most two model calls before domain execution, and everything in the lower band is assurance work that is measured continuously and never allowed to block a user.
:::

Table. The stage budget for a read-path journey, expressed as p50 targets summing to 460 ms, with p99 allowances stated per stage. The p99 column is a per-stage allowance, not a decomposition of end-to-end p99; the arithmetic of that distinction is discussed below. **Modelled** target budget, to be replaced by measurement. {#tbl-stage-budget}

| # | Stage | What it decides | Model tier | p50 budget | p99 allowance |
|---:|---|---|---|---:|---:|
| 1 | Edge, identity, session | Who is asking, in what session | none | 40 ms | 95 ms |
| 2 | Input rails, deterministic | Regex, DLP, allow lists, length | none | 8 ms | 14 ms |
| 3 | Input rails, classifier | Injection and harm, 86M-class | Tier 1 | 25 ms | 70 ms |
| 4 | Task and risk classification | Read, write, workflow, unknown | Tier 1 | 18 ms | 55 ms |
| 5 | Discovery and shortlist | Which capabilities are eligible | none | 12 ms | 40 ms |
| 6 | Plan | One hop, or decompose | Tier 1 or 2 | 55 ms | 220 ms |
| 7 | Escalation gate | Is the fast tier confident | none | 2 ms | 3 ms |
| 8 | Domain execution | The actual work, often parallel | domain | 180 ms | 900 ms |
| 9 | Authorization and validation | Entitlement, limits, idempotency | none | 35 ms | 90 ms |
| 10 | Compose | Structured template where possible | Tier 1 or none | 45 ms | 160 ms |
| 11 | Output rails | Groundedness, egress, schema | Tier 1 or 2 | 40 ms | 130 ms |
|  | **Total** | Time to first token | | **460 ms** | see below |

Three observations about this table matter more than the individual figures.

**The centre's own model usage is small and deliberately capped.** Stages 3, 4, 6, 10 and 11 may involve a model, but stages 3, 4, 10 and 11 are Tier 1 work of tens of milliseconds, and stage 6 is the only stage permitted to reach Tier 2 on an ordinary turn. The sum of central model time on a typical read is well under 150 ms. This is what makes a conversational budget achievable at all, and it is the direct consequence of the tiering discipline in Chapter 14.

**Domain execution is the largest single line and the platform team does not own it.** At 180 ms it is 39 percent of the budget, and it is spent inside systems the platform team cannot optimise. The only levers the centre holds are parallel fan-out where the plan permits it, per-dependency budgets that bound the damage when a domain is slow, and a named partial result when a budget is exceeded. This is why Section {sec:worse-latency} concedes network hops as a permanent cost: the hops are the price of the boundary that makes the 180 ms someone else's accountable number rather than an unowned one.

**Adding the p99 column is not the same as computing the p99.** The naive sum of the p99 allowances is 1,777 ms, and quoting that as the end-to-end p99 would be wrong, because it assumes every stage takes its worst case on the same request. The correct statement is weaker and more useful: the sum is an upper bound, the realistic end-to-end p99 is dominated by whichever single stage has the heaviest tail, and on this budget that is domain execution. The practical consequence is that tail-latency work should start at stage 8 and not at the stages the platform team finds most interesting to optimise.

### What the centre must never own {#sec-central-never}

The list below is the operative half of the design. Each row states a responsibility, why it is tempting to centralise it, and the specific failure that follows.

Table. Responsibilities excluded from the central agent by design, with the failure that follows from accepting each one. Every row has been accepted by some real system, which is why the list is worth writing down. {#tbl-central-never}

| Excluded responsibility | Why it gets centralised anyway | What breaks when it does |
|---|---|---|
| Domain policy semantics | It is faster to add one sentence to the central prompt than to wait for a domain release | The centre becomes the authority on rules it cannot evaluate, and prompt shadowing follows, as in Section {sec:shadowing} |
| Write authority | The model already knows what the user asked for, so letting it decide feels efficient | Authority becomes prompt dependent and cannot be reproduced for an auditor |
| Systems of record | A cache in the centre is quicker than a domain call | Two sources of truth, and the centre's copy is the one nobody owns |
| Durable workflow state | Holding the state in the session is simpler than adding an execution engine | A restart loses in-flight journeys, and long-running work cannot survive deployment |
| Domain evaluation rubrics | Central ownership makes the suites uniform | The team that can adjudicate correctness stops owning the definition of correct |
| Retry policy for domain internals | The centre sees the failure first | Retry storms amplify a domain incident, and idempotency assumptions leak across the boundary |

### Statelessness, sessions and the durable boundary {#sec-central-state}

The central agent should be stateless with respect to any single request beyond the request itself. Session context lives in a store the centre reads and writes but does not hold in memory across turns, because a stateful centre cannot be scaled horizontally without affinity, and affinity is the mechanism by which a routine deployment becomes a user-visible incident.

Long-running work sits behind a deliberate boundary. Anything that must survive a process restart, wait on a human decision, or run for longer than the conversational budget belongs in a durable execution engine invoked by the centre and owned separately. The distinction worth enforcing is between a journey and a turn: a turn has a latency budget of the kind divided above, and a journey may last days. Collapsing the two is the most common reason agent platforms cannot support approval steps without either blocking a request thread or losing state.

### The single chokepoint, and why it is worth the risk {#sec-central-chokepoint}

Concentrating classification, authority and composition in one component is a concentration of risk, and Section {sec:worse-control-plane} states that cost without mitigation. It is accepted for one reason: a deterministic chokepoint is the only place where an authority decision can be made once, logged once, and reproduced later. Distributing that decision to domains means implementing it many times, which means implementing it differently, which means the answer to "was this permitted" becomes a survey rather than a lookup.

The mitigation is not to weaken the chokepoint but to make it boring: no model in the authority path, no dependency on discovery that cannot fall back to a cached last-known-good registry, no shared mutable state between requests, and a degraded mode that is exercised in production regularly rather than documented and left to rot.

## The Model Tiering Ladder {#ch-tiering}

### Why tiering rather than one good model {#sec-tier-why}

The default architecture in most agent implementations is one capable model used for everything, on the reasonable grounds that a single model is simpler to operate, evaluate and reason about. The objection to it is not quality; it is that the distribution of work is extremely skewed, and a single model prices every turn at the cost of the hardest turn.

In a mature deployment the majority of turns are lookups with clear intent, unambiguous capability selection and a response that is mostly a template with values substituted in. Sending those turns through a large model buys nothing measurable and costs latency on the critical path, GPU capacity that could serve the hard turns, and money. Meanwhile the small minority of genuinely hard turns, which need cross-domain decomposition or contested policy interpretation, are exactly the turns that a small model answers confidently and wrongly. One model cannot be correctly sized for both populations. Tiering is the recognition that the correct model is a function of the turn.

::: figure src=model-tiers.svg id=fig-tiers width=full
The four tiers, with the work each is appropriate for, its per-call latency and the share of production turns it should absorb. The lower panel is the part that is usually missing from tiering discussions: an escalation policy that says when not to escalate is what keeps the ladder from collapsing into "always use the biggest model".
:::

### The four tiers {#sec-tier-four}

Table. The tiering ladder. Latency figures are per call and exclude queueing; share figures are the target distribution of production turns in a mature deployment, not a measurement of any specific system. **Modelled** targets. {#tbl-tiers}

| Tier | What it is | Appropriate work | Per-call latency | Target share of turns |
|---|---|---|---:|---:|
| Tier 0 | Deterministic code, no model | Exact and pattern intent match, cached and templated answers, rules, arithmetic, schema checks | 0 to 5 ms | 60 to 75% |
| Tier 1 | On-prem quantized small model, 1 to 4B, FP8 or INT4 | Task and risk classification, capability shortlisting, parameter extraction, rail scoring | 15 to 40 ms | 20 to 30% |
| Tier 2 | On-prem quantized mid model, 8 to 32B, FP8 | Multi-fact synthesis with citations, ambiguous single-domain routing, output groundedness adjudication | 120 to 400 ms | 5 to 12% |
| Tier 3 | Frontier reasoning, API or large on-prem mixture of experts | Cross-domain decomposition, novel or contested policy reasoning, plan repair after a failed attempt | 0.8 to 4 s | 1 to 4% |

The shares are targets, and treating them as such is the point: they are a design objective to be measured against, and a deployment where Tier 3 absorbs 20 percent of turns has either an unusually hard workload or, far more likely, a classifier that has not been tuned and an escalation policy that defaults to escalating.

Tier 0 deserves a defence because it is the tier most often skipped. A deterministic tier feels primitive next to a model that can handle phrasing variation, and it is the highest-leverage component in the system: it is free, it is instant, it never hallucinates, and it is trivially testable. "How many points do I have" is not a reasoning problem. The engineering task is to recognise it as such cheaply, which is a matching problem over a bounded set of intents plus a cache, and to escalate the moment matching is uncertain.

> **Design rule.** Escalation is a decision with a cost, not a default. A turn moves up a tier only when the tier below can name why it could not decide, and that reason is recorded on the trace. "The model was available" is not a reason.

### The escalation policy {#sec-tier-escalation}

An escalation policy needs both halves written down, and the second half is the one that gets omitted.

Escalate when the classifier's margin between its top two candidate intents is below a calibrated threshold; when two or more domains are required to answer, because composition is where small models produce plausible and wrong plans; when no capability matched the stated goal, because the correct output may be a decomposition into capabilities that do exist; when a previous attempt failed output validation, because plan repair is genuinely a reasoning task; or when the turn carries an irreversible effect and the plan's structure is not an exact match for a known-good shape.

Do not escalate when the answer is a lookup whose parameters were extracted with high confidence; when the tier below produced an answer that agreed with a deterministic check; when the only uncertainty is phrasing, which is a composition problem rather than a reasoning problem and belongs in a template; or when the remaining latency budget cannot accommodate the higher tier, in which case the correct behaviour is to answer at the current tier or return a named partial, not to blow the budget and hope.

That last clause is worth stating explicitly, because it is the difference between a budget and an aspiration. The escalation gate at stage 7 of {tbl:stage-budget} is a 2 ms deterministic check whose inputs include the time already spent. A system that escalates without consulting its remaining budget does not have a budget.

### Confidence gating, and what a margin actually means {#sec-tier-confidence}

Escalation policies frequently gate on a model's reported confidence, which is a mistake worth naming. A language model's token probabilities are not calibrated probabilities of correctness, and a classifier fine-tuned on routing data is calibrated only to the distribution it was trained on. Three practices make gating defensible.

Use margin rather than absolute score. The gap between the top two candidates is a far better signal of ambiguity than the top score alone, and it is more stable across model updates.

Calibrate the threshold against a labelled routing set, and recalibrate whenever the model, its quantization format or the capability catalogue changes. A threshold inherited from a previous model version is an unmeasured constant.

Track the two error rates separately and price them differently. Escalating a turn that did not need it costs latency and money. Failing to escalate a turn that needed it produces a wrong answer, and if that turn carried a write, it produces a wrong action. The threshold should be set from the ratio of those costs, and that ratio is a business input rather than an engineering one.

### The cost arithmetic that justifies the ladder {#sec-tier-cost}

The following is **modelled** from the tier shares and latencies above, for one million turns, to show where the saving actually comes from. It uses relative cost units rather than currency, taking a Tier 1 call as one unit, Tier 2 as eight, and Tier 3 as ninety, which is the right order of magnitude for on-prem GPU seconds versus frontier API pricing but should be replaced with local figures.

Table. Modelled control-path cost and mean added latency per million turns, comparing a tiered ladder against a single-model deployment at each tier. The single-model rows are what the same traffic costs when every turn is priced at the cost of the hardest turn. **Modelled** from the shares in {tbl:tiers}. {#tbl-tier-cost}

| Configuration | Relative control-path cost | Mean added latency per turn | Note |
|---|---:|---:|---|
| Tiered ladder as specified | 1.0x baseline | about 55 ms | 68% of turns cost nothing at all |
| Everything at Tier 1 | 0.7x | about 30 ms | Cheaper and faster, and wrong on the 6 to 16% of turns that need synthesis or reasoning |
| Everything at Tier 2 | 5.6x | about 260 ms | Conversational budget consumed by the control path alone |
| Everything at Tier 3 | 63x | about 1,900 ms | Not a viable interactive system at any price |

The second row is the important one, because it is the honest counter-argument to tiering: a single small model is cheaper and faster than a ladder. It is also unable to do the hard turns, and the failure is silent. The ladder's value is not that it minimises cost; it is that it minimises cost subject to keeping a capable model available for the turns that need one.

### Operating the ladder {#sec-tier-operating}

Three operational commitments make tiering work in practice rather than on a diagram.

**Every tier is separately observable.** The trace records which tier answered, why the tier below declined, the margin at the gate, and the latency contributed. Without this, the share distribution is unknown, and an unmeasured share distribution means the ladder cannot be tuned and its cost cannot be attributed.

**Tier boundaries are policy, not code paths scattered through the runtime.** The gate is one component with one configuration, so that changing when escalation happens is a configuration change with an evaluation suite attached, not a diff across the request path.

**Each tier has a defined behaviour when the tier above is unavailable.** If the frontier provider is unreachable, the system does not fail; it answers at Tier 2 with a recorded degradation, or returns a named partial. This is the local-fallback discipline that Chapter {ch:frontier} argues for at length, and it is the reason Tier 3 must never be the only path to any journey a customer depends on.

## On-Prem Quantized Versus Frontier API {#ch-frontier}

### The question, stated so that it can be answered {#sec-frontier-question}

The decision under examination is narrow, and most disagreements about it come from stating it too broadly. The question is not whether frontier models are better than small quantized ones; they plainly are, on the work that requires them. The question is not whether to use a frontier provider at all; this architecture uses one at Tier 3. The question is what should run on the control path that every single turn traverses, which in {tbl:stage-budget} means stages 3, 4, 6, 10 and 11.

Those stages have a specific character. They classify, shortlist, extract parameters, adjudicate groundedness and compose. They are high-volume, low-ambiguity, narrow-output tasks, and they are the tasks on which a well-tuned 3B model quantized to FP8 is close to indistinguishable from a frontier model. They are, in other words, precisely the stages where frontier capability buys the least and frontier latency costs the most.

### The same journey, twice {#sec-frontier-waterfall}

The waterfall below holds the domain work constant at 180 ms and changes only the model serving the control path. It is **modelled** from the stage budget of Chapter 13, using 30 to 55 ms per on-prem Tier 1 or Tier 2 call in the same rack, and 210 to 900 ms per frontier API call inclusive of network round trip, provider queueing and generation. Those API figures are representative of a well-behaved commercial endpoint reached from a private network with connection reuse; they are not worst cases, and they do not include the retry that a p99 excursion often triggers.

::: figure src=latency-waterfall.svg id=fig-waterfall width=full
The same journey with the control path on-prem and on a frontier API. Identical domain work of 180 ms appears in both bars, so the entire difference is architectural. The lower panels are the part of the comparison that latency alone does not show, and the closing note states the converse discipline: this is an argument about placement, not about model quality.
:::

Table. Stage-by-stage comparison of the same read-path journey with an on-prem quantized control path against a frontier-API control path. Domain execution and deterministic authority are identical in both columns by construction. **Modelled** from the assumptions stated above. {#tbl-waterfall}

| Stage | On-prem fast tier | Frontier API centre | Delta |
|---|---:|---:|---:|
| Edge and identity | 40 ms | 40 ms | 0 ms |
| Input rails | 33 ms | 210 ms | +177 ms |
| Classify and shortlist | 30 ms | 240 ms | +210 ms |
| Plan | 55 ms | 900 ms | +845 ms |
| Domain execution | 180 ms | 180 ms | 0 ms |
| Authorize and validate | 35 ms | 35 ms | 0 ms |
| Compose | 45 ms | 260 ms | +215 ms |
| Output rails | 40 ms | 250 ms | +210 ms |
| **Total** | **458 ms** | **2,115 ms** | **+1,657 ms** |
| Of which control path | 278 ms | 1,935 ms | 7.0x |

The end-to-end regression is a factor of 4.6, and the control-path regression is a factor of 7.0. The second figure is the honest one, because it isolates the part of the system the choice actually affects. A reader who believes the API figures are pessimistic should note that even at a uniform 120 ms per frontier call, four control-path calls plus rails still put the journey above 1.1 s, which is outside a conversational budget before any domain has been slow.

### Why the API penalty is structural rather than incidental {#sec-frontier-structural}

It is tempting to treat the gap as an engineering problem to be optimised away. Four components of it are not.

**The round trip is a floor.** A cross-region hop costs tens of milliseconds before the provider has done anything, and it is paid on every one of the four or five control-path calls, not once per turn.

**Prefill is repaid on every turn.** The control-path prompt includes instructions, the eligible capability shortlist and conversation context. On-prem, prefix caching is under your control and resident in your own KV cache. Through an API, caching behaviour is the provider's policy, varies by endpoint and version, and is not something you can size, pin or guarantee.

**Queueing is someone else's.** On-prem, a saturated router pool is a capacity problem you can see in your own metrics and fix by adding a card or shedding assurance load. On a shared endpoint, the queue ahead of your request contains other customers' traffic, and your only lever is a retry that lands on the same saturated endpoint. This is why the variance consequence in {fig:waterfall} matters more than the mean: p99 is set by a system you do not operate.

**Generation length is not free.** Even a short classification response incurs the provider's time to first token plus its decode rate, and a control-path call that returns forty tokens over an API is not meaningfully cheaper than one returning four hundred, whereas on-prem the difference is real and measurable.

### The second-order consequences {#sec-frontier-second-order}

Latency is the most visible cost and not the most dangerous one. Four consequences deserve to be argued explicitly, because they are the ones that surface months after the architecture has been chosen.

**Quota coupling turns assurance into an availability risk.** If user traffic, guardrail scoring and LLM-as-judge evaluation all draw on the same provider quota, then an evaluation run competes with customers. This is the failure this architecture works hardest to prevent, because it inverts the relationship between assurance and service: the mechanism that exists to protect quality becomes the mechanism that degrades availability. Chapter 27 makes quota isolation a hard requirement for exactly this reason.

**Availability is inherited rather than engineered.** If classification is an API call, then a provider incident means the platform cannot classify, which means it cannot route, which means it cannot answer at all. The fast path's availability becomes the product of your own availability and the vendor's, and no amount of retry logic fixes a dependency that is down. On-prem Tier 1 with Tier 0 fallback fails differently: deterministic routing and templated answers continue to serve the majority of turns.

**Cost per turn scales with traffic in the wrong currency.** On-prem serving is a capital and power cost that is fixed with respect to turn count once provisioned, so the marginal turn is close to free until the pool saturates. API serving is a variable cost per call, paid four or five times per turn, on the large majority of turns that never needed reasoning. The crossover is worth computing rather than asserting, and it is computed below.

**Data residency exposure is highest where capability gain is lowest.** The classification hop sees the raw utterance, before any redaction that a later stage might apply, and that utterance may contain account numbers, health information or anything else a customer chose to type. Sending it out of the estate to decide whether a request is a balance lookup or a dispute is the worst available trade: maximum exposure, minimal capability benefit. If one argument in this chapter survives disagreement about every latency figure, it should be this one.

### The crossover, computed {#sec-frontier-crossover}

The following is **modelled** and offered as arithmetic to be redone with real quotes and real hardware costs. It assumes 2.6 control-path model calls per turn, an average of 700 input and 120 output tokens per control-path call, a blended frontier price of 0.60 dollars per million tokens for a small commercial model, and an amortised on-prem cost of 3.20 dollars per GPU hour inclusive of power, cooling, hosting and a three-year depreciation on the card.

Table. Modelled monthly control-path cost at three traffic volumes, comparing frontier API serving against on-prem quantized serving sized for the same load with headroom. The GPU counts come from Chapter 22. Replace every input with a local figure before using this to decide anything. **Modelled**. {#tbl-frontier-cost}

| Monthly turns | Control-path calls | Frontier API cost | On-prem fleet | On-prem cost | Ratio |
|---:|---:|---:|---|---:|---:|
| 500,000 | 1.3 M | about 640 dollars | 1 GPU | about 2,300 dollars | 0.28x, API cheaper |
| 25,000,000 | 65 M | about 32,000 dollars | 5 GPUs | about 11,500 dollars | 2.8x, on-prem cheaper |
| 400,000,000 | 1,040 M | about 512,000 dollars | 40 GPUs | about 92,000 dollars | 5.6x, on-prem cheaper |

The shape of this table is the argument, not its values. At pilot volume the API is cheaper, and building a GPU fleet to serve half a million turns a month is capacity theatre. Somewhere in the low tens of millions of turns per month the fixed cost of a small fast-tier fleet is repaid, and past that the gap widens roughly linearly because API cost tracks volume while GPU cost tracks peak concurrency. This is also why the roadmap in Chapter 31 starts on APIs and moves the fast path in-house later: the correct sequence is to measure the workload with rented capacity, then buy hardware sized from measurement.

> **Decision.** Start on frontier APIs for everything, including the control path, and instrument it thoroughly. Move the control path on-prem when any one of the following becomes true: control-path spend exceeds the amortised cost of the fleet that would replace it, p99 conversational latency is dominated by API round trips, a residency or contractual constraint forbids raw utterances leaving the estate, or an evaluation burst has throttled user traffic even once.

### Where frontier models genuinely win {#sec-frontier-wins}

A chapter that only criticised the API path would be the caricature this document set out to avoid. Frontier models are the correct choice for Tier 3 work, and the reasons are specific.

They are substantially better at decomposing a goal into a plan when the goal spans domains and the correct sequence is not obvious. They are better at reasoning about policy language that contradicts itself or does not cleanly cover the case at hand, which is common in real regulatory text. They are better at plan repair, meaning the second attempt after an output validation failure, where the useful behaviour is to reconsider the approach rather than retry the same call. And they require no capacity planning, no quantization work, no serving expertise and no hardware, which at Tier S is not a minor consideration but the deciding one.

The design that follows from this is a ladder whose top rung is rented, whose lower rungs are owned, and whose escalation policy is tuned to make the rented rung rare. That is a different position from either "run everything locally" or "call the best model every time", and it is the position this document defends.

### What would falsify this chapter {#sec-frontier-falsify}

The argument for an on-prem fast path fails if any of the following can be shown on your own workload. That a frontier endpoint reachable from your network sustains a p99 under about 120 ms for a short classification call, including retries, over a full week of production traffic. That your control-path spend at target volume remains below the amortised cost of the equivalent GPU fleet. That the provider's caching, quota and availability behaviour can be contracted to a level that removes the coupling and inheritance arguments. Or that no raw utterance reaching the classification hop can contain regulated data, which is a claim about your input filtering rather than about your users.

Where those hold, the API-centred control path is simpler, cheaper to operate and requires none of the capabilities in Chapter 25. That is a real advantage and the honest recommendation for a large fraction of deployments, particularly at Tier S.

## Guardrails: Taxonomy and Placement {#ch-guardrails}

### What a guardrail is, and what it is not {#sec-rails-definition}

A guardrail is a control that constrains what enters or leaves a model-mediated boundary, evaluated independently of the model whose behaviour it constrains. The independence is the load-bearing part. An instruction in a system prompt telling a model not to reveal account numbers is not a guardrail; it is a request, evaluated by the same component whose failure it is supposed to catch, and it fails in exactly the circumstances where a control is needed.

Three distinctions are worth fixing before the taxonomy, because conflating them produces most guardrail design errors.

**A guardrail is not an authority check.** Entitlement, limits and write permission are decided by deterministic code reading structured state, as in stage 9 of {tbl:stage-budget}. Rails constrain content and shape. Authority constrains effect. A system that uses a rail to prevent an unauthorised transfer has made a category error, because rails are probabilistic and authority must not be.

**A guardrail is not an evaluation.** Rails run inline on every request and must answer within a latency budget. Evaluations run against a corpus and may take as long as they need. The two are frequently confused because both produce verdicts about quality, and the consequence of the confusion is either an evaluation on the critical path, which destroys latency, or a rail treated as sufficient evidence of quality, which is the mistake that step 7 of the reference implementation exists to illustrate.

**A guardrail is not a substitute for a bounded action space.** The strongest control over what an agent can do is what it is wired to be able to do. A rail that inspects a tool call for suspicious parameters is a weaker control than a tool that is not callable in this context at all, and the closed-world reachability check of Section {sec:auditor} is worth more than any inline inspection.

### The four boundaries where rails attach {#sec-rails-boundaries}

Rails belong at trust boundaries, and there are exactly four in this architecture. Placing them anywhere else produces controls that are either redundant or unenforceable.

::: figure src=guardrail-placement.svg id=fig-rails width=full
Where rails attach, and what each set is responsible for. The middle band is the one most often missing: retrieved documents and tool output cross a trust boundary and must be treated as hostile input, not as trusted context. The lower band is asynchronous assurance, which is deliberately never allowed to block a user, and the table states the fail-open or fail-closed posture per control.
:::

The first boundary is between the user and the centre, where the input rails sit. The second is between the centre and a domain capability, where the tool argument and entitlement scope checks sit. The third is between a tool or retrieval source and the model that will consume its output, which is the boundary most implementations omit. The fourth is between composition and the user, where output rails sit.

A useful test of whether a control is at a boundary: ask what the control protects against, and then ask whether the thing it protects against can reach the protected component by another route. If it can, the control is decorative.

### The input rail taxonomy {#sec-rails-input}

Table. Input rails, with the mechanism, the tier that implements it and where in the stage budget it sits. Latency figures are per-check contributions to stages 2 and 3 of {tbl:stage-budget}. Rows marked Tier 1 are model calls; the rest are deterministic. {#tbl-rails-input}

| Rail | What it catches | Mechanism | Tier | Budget |
|---|---|---|---|---:|
| Length, encoding and rate | Oversized payloads, encoding smuggling, abuse patterns | Deterministic limits and normalisation | Tier 0 | under 1 ms |
| Secret and credential detection | API keys, tokens and passwords pasted into a chat | Pattern and entropy detection | Tier 0 | 1 to 3 ms |
| PII detection and redaction | Regulated data entering logs, prompts or a third-party endpoint | Named-entity and pattern DLP | Tier 0 or 1 | 2 to 8 ms |
| Topic and scope allow list | Requests the platform has no business answering | Classifier against declared scope | Tier 1 | 10 to 20 ms |
| Prompt injection and jailbreak | Attempts to override instructions or extract the prompt | 86M-class classifier, escalating to a guard model | Tier 1, then 2 | 20 to 50 ms |
| Harm and hazard categories | Content the organisation has undertaken not to process | Guard model in no-think mode | Tier 2 | 40 to 90 ms |
| Identity and session integrity | Replayed, forged or expired sessions | Deterministic verification | Tier 0 | included in stage 1 |

Two rows deserve comment. PII redaction is placed early because everything downstream, including logs, traces, prompts and any third-party call, inherits whatever it fails to catch, which is the residency argument of Section {sec:frontier-second-order} restated as a control. And the injection rail is the only input rail permitted to escalate to a larger model, because it is the one whose false negatives are actively adversarial rather than accidental.

### Injection usually does not arrive in the user's message {#sec-rails-indirect}

The single most common gap in guardrail implementations is that all the effort goes on the user's utterance, which is the input an attacker controls least conveniently, and none on the text a tool or a retrieval source returns.

Consider the mechanism concretely. A domain capability returns a record containing a free-text field, perhaps a merchant description, a support note or a document chunk. That text is inserted into the composition prompt so the model can summarise it. If it contains an instruction, the model has no reliable way to distinguish it from the platform's own instructions, because both arrive as tokens in the same context. The attacker does not need access to the conversation at all; they need to have written text into a system that the platform later retrieves. In a retrieval-augmented deployment this includes any document corpus users can contribute to, which is most of them.

Four controls address this, and none of them is a prompt instruction.

Structure the boundary rather than relying on the model to respect it. Domain results are passed as structured fields with declared types, and free-text fields are marked as data. Composition prefers templates with substituted values over free generation, which is why stage 10 of {tbl:stage-budget} is labelled "structured template where possible" and is priced at 45 ms rather than at the cost of a generation.

Scan tool and retrieval output with the same injection rail used on user input, because the threat is identical and only the delivery route differs.

Never allow a tool result to expand the action space. If retrieved text names a capability, that is not a request the planner may honour; capability selection happens before composition and from the registry only. This is the property closed-world reachability makes checkable.

Bound the effect of composition. If composition can only emit text, injected instructions can at worst produce a misleading answer, which the output rails then examine. If composition can trigger a call, injected instructions can produce an action, and no output rail will save you.

> **Anti-pattern.** Instructing the model to ignore instructions found in retrieved content. This is a request made to the component under attack, evaluated by the component under attack, in the same channel as the attack. It reduces the success rate of naive attempts, which makes it worse than useless, because it produces the appearance of a control and the measurement of its absence.

### The output rail taxonomy {#sec-rails-output}

Output rails are the less developed half of most implementations, which is unfortunate, because they are the half that decides whether a wrong answer reaches a customer.

Table. Output rails, with what each one compares against. The third column is the important one: a rail that has nothing to compare against is a rail that is asking a model for an opinion. {#tbl-rails-output}

| Rail | What it catches | Compared against | Tier | Budget |
|---|---|---|---|---:|
| Schema and contract | Malformed or unparseable responses, missing required fields | The declared response contract | Tier 0 | under 1 ms |
| Groundedness | Claims not supported by any retrieved or returned evidence | The actual domain results in this turn | Tier 1 or 2 | 20 to 60 ms |
| Action assertion | A response claiming an effect that did not occur | The receipt or confirmation from the domain | Tier 0 | 1 to 3 ms |
| PII and data class egress | Regulated data leaving in a channel not cleared for it | The data classification of the destination channel | Tier 0 | 2 to 6 ms |
| Refusal correctness | Refusing for an unstated reason, or answering something that should have been refused | The recorded rail decision and reason code | Tier 0 | under 1 ms |
| Numeric and unit sanity | Impossible balances, mismatched currencies, sign errors | Domain-declared ranges and units | Tier 0 | 1 to 2 ms |
| Tone and disclosure policy | Missing mandated disclosures, prohibited advice framing | Policy templates for this journey class | Tier 0 or 1 | 5 to 20 ms |

The action assertion rail is the one to build first if only one output rail can be afforded. It is deterministic, it is cheap, and it catches the class of error with the worst consequences: a response that tells a customer something happened when it did not. Its implementation is a comparison between the claimed effects in the composed response and the receipts actually returned by the authority stage, which is possible only because authority is deterministic and produces receipts. This is an example of the general pattern in this architecture, where a deterministic guarantee at one stage makes a cheap check possible at a later one.

Groundedness is the rail most often over-scoped. It should ask whether the claims in this response are supported by the evidence returned in this turn, which is a bounded comparison. It should not ask whether the answer is correct in the world, which is unbounded, unanswerable inline, and belongs to domain evaluation. The wrong answer in step 7 of the reference implementation was perfectly grounded: the transaction was real, the amount was right, the arithmetic was wrong for a domain reason. No groundedness rail catches that, and none should be blamed for it.

### Fail open or fail closed, decided per control {#sec-rails-posture}

Every rail needs a documented posture for the case where it is unavailable, times out, or returns an error. The common mistakes are to choose one posture globally, or worse, to leave it as whatever the framework's default happens to be.

Table. Fail posture per control, with the reasoning. The pattern is that controls protecting authority and irreversible effects fail closed, and controls protecting quality fail open with a recorded degradation. {#tbl-rails-posture}

| Control | Posture | Reasoning |
|---|---|---|
| Authentication and entitlement | Fail closed | No identity, no answer. There is no acceptable degraded mode for authority |
| Write authorization | Fail closed | Authority is never inferred from text, and an unavailable check is not an approval |
| Injection classifier, read path | Fail closed to a safe path | Degrade to deterministic routing and templated answers rather than refusing outright |
| Injection classifier, write path | Fail closed | An unscreened input must not reach a stage that can cause an effect |
| PII egress rail | Fail closed | The cost of a leak is asymmetric and irreversible |
| Action assertion | Fail closed | If the receipt cannot be checked, the claim must not be made |
| Groundedness rail, inline | Fail open, logged and sampled | Blocking reads on an unavailable quality check trades a large availability loss for a small quality gain |
| Asynchronous quality judges | Fail open | Assurance is not availability, and a judge outage must never be user-visible |
| Telemetry and trace export | Fail open | Observability must not gate service, however tempting it is to make it mandatory |

The pattern generalises to a rule that is easier to apply than a table: fail closed where the failure is irreversible or where authority is involved, and fail open with a recorded degradation where the failure is a quality risk on a reversible read. What must never happen is an undocumented posture, because the default that a framework chooses under load is discovered during an incident.

## The Guardrail Cascade {#ch-cascade}

### The guardrail tax, and why chaining safety calls does not work {#sec-cascade-tax}

The straightforward way to implement thorough guardrails is to run every check on every request. It is also the way to destroy the latency budget, and the arithmetic is unforgiving. A guard model at 65 ms, a topic classifier at 20 ms, a groundedness adjudicator at 45 ms and a PII model at 25 ms is 155 ms of rail work on a 460 ms budget, before the platform has classified the request or a domain has done anything.

What makes this worse than a simple latency problem is the behaviour it induces. Once rails consume a third of the budget, someone is asked to make the system faster, and rails are the easiest thing to remove because their contribution is invisible when they are working. Rails then get disabled selectively, usually without a record of which ones and for which journeys, and the system arrives at the worst state available: the cost of having built controls, without the coverage.

> **Anti-pattern.** The guardrail tax. Chaining every safety model on the critical path of every request, then quietly disabling the ones that hurt most when latency becomes a complaint. The result is a control catalogue that does not describe the running system, which is more dangerous than having no catalogue, because it is trusted.

### The cascade {#sec-cascade-design}

The alternative is a cascade in which every turn pays for the cheapest checks, and only the turns that look ambiguous pay for the expensive ones. This is the same escalation logic as Chapter 14 applied to safety rather than capability, and it works for the same reason: the distribution of difficulty is skewed.

::: figure src=guardrail-cascade.svg id=fig-cascade width=full
The cascade, with the share of turns reaching each stage, the latency each stage contributes and the hardware it needs. The arithmetic panel is the argument: the same coverage that would cost 65 ms on every turn costs about 22 ms on average, because the deepest check only runs on the 12 percent of turns that reached it. The lower band is the part that keeps the cascade honest, which is that the rails themselves are evaluated.
:::

Table. The cascade stages, with the modelled share of turns reaching each, its latency contribution and the decision it makes. Shares are targets for a mature deployment and will differ substantially on adversarial or heavily regulated traffic. **Modelled**, with third-party latency figures noted in {tbl:guard-models}. {#tbl-cascade}

| Stage | Check | Share of turns reaching it | Latency when it runs | Hardware | Escalates when |
|---:|---|---:|---:|---|---|
| 0 | Deterministic: regex, deny lists, length, encoding, schema, rate and entitlement | 100% | 0.2 to 2 ms | none | A pattern matches, or the input is not obviously benign |
| 1 | Tiny classifier: 86M-class injection and harm scorer, quantized and batched | 38% | 20 to 50 ms | Shared GPU slice | Score exceeds a calibrated threshold, or margin is narrow |
| 2 | Guard model: 8 to 12B in no-think mode, hazard category adjudication | 12% | 40 to 90 ms | Dedicated pool | The category is one requiring human judgement, or confidence is low |
| 3 | Human review or hard block with a reason code | 3% | seconds or longer | none | Terminal |

The expected added latency is the share-weighted sum: about 1 ms on every turn, 35 ms on the 38 percent that reach stage 1, and 65 ms on the 12 percent that reach stage 2, which is about 22 ms of mean rail latency with a p99 near 120 ms on the escalating tail. Running stage 2 unconditionally would cost about 65 ms on every turn for the same coverage, which is roughly three times the rail tax for no additional protection.

Two design constraints keep this from degrading in practice. Stage 0 must be genuinely cheap, which means no model, no network call and no database lookup that is not already cached. And the escalation thresholds must be calibrated against measured traffic, because a stage 1 threshold that sends 80 percent of turns to stage 2 has quietly rebuilt the unconditional design while retaining the complexity of the cascade.

### Model choices at each stage {#sec-cascade-models}

The figures below are **third-party published** characteristics of guard models available at the time of writing, offered to make the cascade concrete rather than as a recommendation. Latency depends on input length, batch size, quantization and hardware, and every one of them should be re-measured with the recipe in Chapter 23.

Table. Representative guard models by cascade stage, with the size class and published purpose. All figures **third-party published**; latencies assume short inputs on a modern data-centre GPU with FP8 or equivalent quantization and batching, and are not vendor guarantees. {#tbl-guard-models}

| Stage | Model class | Size | Purpose as published | Indicative latency |
|---:|---|---|---|---:|
| 1 | Llama Prompt Guard 2 | 86M | Prompt injection and jailbreak detection on user and tool text | 20 to 50 ms |
| 1 | Granite Guardian HAP | 38M | Hate, abuse and profanity detection where the budget is tightest | under 20 ms |
| 2 | Llama Guard 4 | 12B | Multimodal hazard taxonomy classification for input and output | 40 to 90 ms |
| 2 | Granite Guardian 4.1 | 8B | Harm, groundedness and jailbreak checks, with a no-think mode for latency | 40 to 90 ms |
| 0 to 2 | NeMo Guardrails | orchestration | Rail definition, dialogue and flow constraints, and rail sequencing | 20 to 80 ms of orchestration overhead |

Two selection notes matter more than the specific models, because the models will change. First, prefer a small purpose-trained classifier over a general model with a safety prompt at stage 1: it is one to two orders of magnitude cheaper, it can be batched aggressively, and its failure modes are measurable on a labelled set. Second, use a guard model's no-think or non-reasoning mode at stage 2 unless the escalation genuinely needs deliberation, because reasoning traces are the difference between 60 ms and several seconds.

### The rails need their own evaluation {#sec-cascade-eval}

An unevaluated guardrail becomes a refusal machine. The failure is gradual: thresholds are tightened after an incident, nobody measures the effect on benign traffic, and the system slowly begins refusing legitimate requests. Because refusals look safe, the drift is invisible in the metrics teams usually watch.

Four measurements are the minimum, and they are properties of the rails rather than of the platform.

**False negative rate, by attack family and not in aggregate.** An aggregate number is dominated by whichever family is best represented in the test set, which is usually the easiest. Break it out by direct instruction override, indirect injection through retrieved content, encoding and obfuscation, multi-turn escalation, and tool-output smuggling. A rail can be excellent at the first and useless at the second.

**False positive rate on benign golden traffic, per journey.** Sampled from real production traffic that a human has confirmed benign, and reported per journey, because a rail that costs 0.5 percent of traffic overall may be costing 8 percent of one journey and making it unusable.

**Refusal correctness.** When the system refuses, did it refuse for the reason it stated, and was that reason a real policy? This catches the common failure where a rail fires for one reason and the response cites another, which destroys the audit trail and confuses the customer.

**Rail latency at p99, budgeted like any other dependency.** Rails are a dependency of the request path and should have a per-stage budget, a timeout, a circuit breaker and a documented fail posture from {tbl:rails-posture}. A rail without a timeout is an availability risk wearing the costume of a control.

### Who owns the thresholds {#sec-cascade-ownership}

Thresholds are policy, and policy has an owner. The arrangement that works is that the platform team owns the mechanism, the cascade shape and the latency budget; risk or security owns the acceptable false negative rate by attack family; and the domain owns the journey-level false positive tolerance, because the domain is accountable for whether its customers can complete their task.

The reason to name owners explicitly is that threshold changes are the highest-leverage and least-reviewed changes in the system. Moving one number can shift a tenth of production traffic from stage 1 to stage 2, change mean latency by tens of milliseconds, and alter the refusal rate of a journey, with no code change and often no evaluation. Threshold changes therefore belong in the change types of {fig:evals} that trigger a required evaluation suite, and the reference implementation's change-classification rule treats a guardrail threshold change as a first-class change type for exactly this reason.

# Sizing {#part-sizing}

Part IV converts a business number into a hardware decision through an explicit chain of assumptions, states the accuracy price of each quantization format rather than hiding it, sizes three deployment tiers, and gives the commands to replace every figure in it with a measurement.

## From a Business Number to a GPU Count {#ch-load}

### The question capacity planning is actually asked {#sec-load-question}

Sizing conversations begin with the wrong number. Someone has a registered user count, or a licence count, or a headline about how many customers the organisation serves, and the question is how many GPUs that requires. The number is unanswerable as posed, because none of those quantities appears anywhere in the arithmetic that determines hardware. What determines hardware is peak concurrent demand, the fan-out per request, and the token volume that results.

The purpose of this chapter is not to produce a GPU count for a hypothetical organisation. It is to make the chain of conversion explicit, so that when the answer turns out to be wrong, the specific assumption that was wrong can be identified and corrected. A capacity model that produces a number without exposing its assumptions cannot be debugged, and every capacity model is eventually wrong.

::: figure src=load-funnel.svg id=fig-funnel width=full
The conversion chain worked for the mid tier. Each row is an assumption, and the arrow between rows is where a local measurement must replace the value used here. The lower panels list the multipliers that are routinely underestimated: fan-out per turn and the amplification from retries, rails and assurance traffic, which together often exceed the base load they multiply.
:::

### The chain, stated as arithmetic {#sec-load-chain}

The chain below is worked for Tier M and every step is exact, so that a reader can substitute their own figures and follow the same arithmetic. The engagement ratios are **modelled** illustrative values, not industry benchmarks.

Table. The conversion chain from registered users to control-path tokens per second, worked for Tier M. Each row's value is the product of the row above and the stated multiplier, so any figure can be replaced and the chain recomputed. **Modelled** throughout. {#tbl-load-chain}

| Step | Quantity | Value | Multiplier applied | Where the real number comes from |
|---:|---|---:|---|---|
| 1 | Registered users | 10,000,000 | starting point | The business case |
| 2 | Monthly active users | 4,000,000 | 0.40 engagement | Product analytics, already measured |
| 3 | Daily active users | 800,000 | 0.20 of monthly | Product analytics, already measured |
| 4 | Assisted sessions per day | 240,000 | 0.30 use the agent | Unknown before launch; the largest uncertainty |
| 5 | Sessions in the peak hour | 48,000 | 0.20 in the busiest hour | Existing channel traffic shape |
| 6 | Concurrent sessions at peak | 3,000 | Little's Law at 225 s mean session | Measure session duration, do not guess it |
| 7 | In-flight requests at peak | 260 | 2.2 s mean service in a 25 s turn cycle | Time to first token plus streaming duration |
| 8 | Control-path model calls per second | 310 | 2.6 calls per turn | The tiering distribution of {tbl:tiers} |
| 9 | Control-path tokens per second | 62,000 | 200 output tokens per call | Measured from real prompts, not estimated |

Steps 6 and 7 are both applications of Little's Law, which in this setting says that the number of things in a system equals the rate at which they arrive multiplied by the time each spends there. At step 6 the things are sessions: 48,000 sessions arriving over 3,600 seconds, each lasting 225 seconds, gives 3,000 concurrent. At step 7 the things are requests: the 3,000 sessions produce a turn every 25 seconds, which is 120 turns per second, and each turn occupies the system for 2.2 seconds, giving about 260 requests in flight. The same law appears again in Chapter 24, where it explains why a saturated pool's queue wait dominates its service time.

Two steps in this chain deserve more scepticism than the others.

**Step 4 is the largest unknown and it is unknowable before launch.** What fraction of daily active users will choose the assisted channel is a product question, not an engineering one, and pre-launch estimates are routinely wrong by a factor of three in both directions. The correct response is architectural rather than analytical: make the fast tier horizontally scalable in units small enough to add quickly, run at a utilisation target that leaves genuine headroom, and reforecast from measurement within the first weeks of real traffic.

**Step 9 is where an unmeasured assumption becomes an expensive one.** Output tokens per control-path call is the difference between a router that emits a capability name and a router that emits a paragraph of reasoning. At 200 output tokens the fleet in Chapter 22 is adequate; at 800 it is not, and the difference is a prompt design decision that nobody thinks of as a capacity decision. Instrument it before sizing.

### Fan-out is the multiplier that ruins forecasts {#sec-load-fanout}

Every user turn produces more than one call to more than one thing, and the total is consistently underestimated because each contributing team accounts only for its own share.

A single turn typically issues two to four control-path model calls, one to six domain API calls, two to twelve database queries behind those APIs, and zero to three retrieval requests. On top of that base there is amplification: retries under partial failure at 1.1 to 3 times, guardrail calls at one to three per turn, judge sampling at 2 to 20 percent of turns, and shadow or canary traffic at up to 100 percent during a migration.

The identity worth writing on a whiteboard is this: effective load equals ingress rate times fan-out per request times retry amplification times the assurance multiplier, and only then times tokens per call. Every term is greater than or equal to one, and the product of five terms each modestly underestimated is a forecast that is wrong by a large factor. The most common single omission is shadow traffic during a migration, which can double the load on a fleet that was sized for the steady state and was therefore correctly sized right up until the migration began.

> **Design rule.** Size the fast tier for measured peak times fan-out times retry amplification, then add the assurance load as a separate line item with its own quota. Assurance traffic that shares a quota with user traffic is not headroom; it is a latent incident, as Section {sec:frontier-second-order} argues in the API case and Chapter 27 formalises for the on-prem case.

### What to measure in the first month {#sec-load-measure}

Because the chain above is a scaffold for local measurement rather than a result, the useful output of this chapter is a short list of instruments to install before sizing anything.

Session duration and turns per session, from which steps 6 and 7 follow directly. Time to first token and total response duration at p50, p95 and p99, separated by journey class, because a mean over mixed journeys is uninformative. Control-path calls per turn and output tokens per call, broken down by tier, which together give steps 8 and 9 and also reveal whether the escalation policy is behaving. Fan-out per turn to domains and to retrieval. Retry counts, attributed to the dependency that caused them. And the peak-to-mean ratio over both the day and the week, which is the figure that decides how much headroom the utilisation target must leave.

Every one of these is cheap to collect and expensive to reconstruct later, which is why Section {sec:tier-s-notes} names skipping telemetry as the expensive mistake at Tier S.

## Why Decode Is Memory-Bandwidth-Bound {#ch-roofline}

### The two phases have opposite bottlenecks {#sec-roofline-phases}

Nearly every sizing error in language model serving comes from treating inference as one workload. It is two, with different bottlenecks, different scaling behaviour and different hardware preferences.

**Prefill** processes the entire input prompt in parallel. Every token attends over every earlier token, the arithmetic is dense matrix multiplication, and the hardware's compute throughput is the limit. Prefill is compute-bound, it parallelises well across a batch, and it is why long prompts are expensive in a way that is proportional to their length.

**Decode** generates one token at a time, and each token requires reading the model's weights from memory. For a batch of one, generating a single token means moving every weight the model has through the memory system to perform a small amount of arithmetic on each. Decode is memory-bandwidth-bound, and no amount of additional compute makes it faster.

The consequence is the single most useful heuristic in GPU selection for this architecture: for interactive, latency-sensitive, short-output work, which is what the entire control path consists of, the specification that matters is memory bandwidth, not floating-point throughput.

### The arithmetic that makes this concrete {#sec-roofline-arithmetic}

A useful first-order bound on single-stream decode speed is that the time to generate one token is at least the time required to read the weights that must be read for it. For a dense model with all weights read per token, that is the model's size in bytes divided by the achievable memory bandwidth.

Table. First-order single-stream decode ceiling, computed as achievable bandwidth divided by model bytes per token, at 70 percent bandwidth efficiency. These are ceilings, not measurements: real throughput is lower because of attention over the KV cache, kernel launch overhead and sampling. **Modelled** from published bandwidth specifications. {#tbl-roofline}

| Model and format | Bytes read per token | On L40S at 0.86 TB/s | On H100 at 3.35 TB/s | On H200 at 4.8 TB/s |
|---|---:|---:|---:|---:|
| 4B at FP8 | about 4 GB | about 150 tok/s | about 586 tok/s | about 840 tok/s |
| 8B at FP8 | about 8 GB | about 75 tok/s | about 293 tok/s | about 420 tok/s |
| 8B at INT4 | about 4.3 GB | about 140 tok/s | about 545 tok/s | about 781 tok/s |
| 32B at FP8 | about 32 GB | does not fit | about 73 tok/s | about 105 tok/s |
| 70B at FP8 | about 70 GB | does not fit | does not fit on one card | about 48 tok/s |
| 70B at FP4 | about 35 GB | does not fit | about 67 tok/s | about 96 tok/s |

Three conclusions follow directly, and each one contradicts an intuition that costs money.

The first is that a 4-bit model is roughly twice as fast as the same model at 8-bit in single-stream decode, because it moves half the bytes. This is why {sec:quant-regime} recommends 4-bit for latency-critical single-stream work despite its accuracy cost.

The second is that the same card serves a 4B model roughly twice as fast as an 8B model, which is the quantitative case for using the smallest model that passes its evaluation suite on the fast path rather than the best model available.

The third is that batching changes the regime entirely. With a large batch, the weights read once serve many sequences, so the per-token cost of weight traffic falls and the bottleneck moves toward compute and toward the KV cache. This is why FP8 wins on saturated throughput while 4-bit wins on single-stream latency, and why a pool serving interactive routers should be configured differently from a pool serving batch synthesis.

### The KV cache is the constraint people forget {#sec-roofline-kv}

Weights are the easy part of the memory budget because they are fixed. The KV cache is proportional to concurrency times context length, and it is what actually decides whether a card is usable at the batch size the load requires.

For a transformer with grouped-query attention, the cache per token is approximately two, for keys and values, times the number of layers, times the number of key-value heads, times the head dimension, times the bytes per element. A useful shortcut: an 8B-class model with grouped-query attention at FP8 cache precision costs roughly 100 to 140 KB per token of context.

Table. Modelled KV cache footprint at 120 KB per token of context, showing why concurrency and context length are a capacity decision rather than a configuration detail. Compare against the memory left after weights: about 40 GB on an 80 GB H100 serving an 8B model at FP8 with headroom. **Modelled**. {#tbl-kv}

| Concurrent sequences | 2k context | 8k context | 32k context | 128k context |
|---:|---:|---:|---:|---:|
| 16 | 3.8 GB | 15 GB | 61 GB | 246 GB |
| 64 | 15 GB | 61 GB | 246 GB | 983 GB |
| 256 | 61 GB | 246 GB | 983 GB | 3.9 TB |

The table is the argument for two design positions taken elsewhere in this document. It is why the control path keeps prompts short, preferring a shortlist of two or three eligible capabilities over a catalogue of forty, as Section {sec:single-agent-prefill} argues on latency grounds and this table reinforces on capacity grounds. And it is why H200 exists in the decision tree of Chapter 20 as a memory purchase rather than a compute purchase: it has the same compute as H100 and 76 percent more memory, which buys concurrency at long context and nothing else.

The corollary is a diagnosis worth knowing. If a serving pool is rejecting or queueing requests while its GPU utilisation looks moderate, the constraint is almost always KV cache capacity rather than compute, and the fix is shorter contexts, cache quantization, fewer concurrent sequences per card, or more memory per card. Adding compute will not help.

## Choosing the GPU {#ch-gpu}

### Choose from the binding constraint {#sec-gpu-constraint}

GPU selection goes wrong in a predictable way: a team picks the most capable card the budget allows, then discovers that the constraint that actually binds their workload was something the card does not address. The discipline is to name the binding constraint first, in the language of Chapter 19, and select from it.

::: figure src=gpu-decision.svg id=fig-gpu width=full
The decision tree, ordered so that the cheapest sufficient answer is reached first. The lower panel lists the three sizing errors that cost real money, all of which are versions of the same mistake: selecting hardware from a specification that is not the binding constraint for the work in question.
:::

### The catalogue {#sec-gpu-catalogue}

The table below is **third-party published** vendor specification data at the time of writing, reduced to the three attributes that matter for this architecture: memory capacity, which decides what fits and how much concurrency is possible; memory bandwidth, which decides decode speed; and the lowest-precision format with hardware support, which decides whether the newest quantization work is available at all.

Table. GPU specifications relevant to serving decisions, with the role each card plays in this architecture. All specifications **third-party published** vendor figures; achievable bandwidth in practice is typically 60 to 80 percent of the peak figure. {#tbl-gpu}

| GPU | Memory | Bandwidth | Lowest native format | Role in this architecture |
|---|---:|---:|---|---|
| L40S | 48 GB GDDR6 | 0.86 TB/s | FP8 | Cheapest per served token for small routers, classifiers and guard models. No NVLink, no FP4 |
| RTX PRO 6000 Blackwell | 96 GB GDDR7 | about 1.79 TB/s | NVFP4 | The pragmatic single-node choice: several models co-resident with isolated caches, air cooled, PCIe |
| H100 SXM | 80 GB HBM3 | 3.35 TB/s | FP8 | Proven FP8 path with mature kernels for 8 to 32B decode pools. No FP4 |
| H200 SXM | 141 GB HBM3e | 4.8 TB/s | FP8 | A memory and bandwidth purchase: same compute as H100, for long context and high concurrency |
| B200 SXM | about 180 GB HBM3e | about 7.7 TB/s | FP4 | Changes the economics on 70B-class models through native FP4. Power and cooling are real constraints |
| GB200 NVL72 | rack scale | rack scale | FP4 | One NVLink domain for models larger than a node. Liquid cooled, long lead time |

### The three expensive mistakes {#sec-gpu-mistakes}

**Sizing decode capacity from floating-point throughput.** This is the error Chapter 19 exists to prevent. Decode reads the whole model per token, so bandwidth sets the ceiling, and a card chosen for its FLOPS may deliver a fraction of the tokens per second its specification sheet implies. The clearest illustration is a previous-generation card with no FP8 path: it loses roughly half of its potential modern throughput not because its compute is inadequate but because it must run a format that moves twice the bytes.

**Forgetting the KV cache.** Weights fit, the model loads, the demonstration works at batch one, and the pool then fails to reach the concurrency the load requires because the cache exhausted the remaining memory. {tbl:kv} is the arithmetic that prevents this, and it should be done before purchase rather than after.

**Buying the frontier card for a router.** A 4B classifier on a B200 wastes the asset. A B200's value is that it can monetise very high decode throughput on large models under saturation; a router that answers in 20 ms at batch eight uses almost none of that. Put routers and guard models on the cheapest card with sufficient bandwidth, and reserve the expensive cards for the pools whose utilisation can justify them.

> **Anti-pattern.** Homogeneous fleets. Buying one card type for every workload because it simplifies procurement. It also guarantees that either the routers are running on hardware three times more expensive than they need, or the synthesis pool is bandwidth-starved. A heterogeneous fleet of two or three card types, each matched to a pool, is the normal shape of an efficient deployment, and it is the shape the topologies in Chapter 22 use.

### Fitting the model to the card {#sec-gpu-fit}

A short procedure, which is worth following in this order because each step can eliminate the need for the next.

First, compute the weight footprint at the intended quantization format and add 15 to 20 percent for activations, fragmentation and the runtime's own allocations. Second, compute the KV cache requirement at the target concurrency and context length using {tbl:kv}, and confirm the sum fits with headroom. Third, check the single-stream decode ceiling from {tbl:roofline} against the latency target, remembering that real throughput is meaningfully below the ceiling. Fourth, decide whether the pool is latency-critical or throughput-critical, because that determines the quantization format in Chapter 21 and may change the answer to the first step. Only then choose a card.

If the model does not fit on one card, the next decision is not automatically a bigger card. Tensor parallelism across two cards adds communication on every token and is worth it when bandwidth per card is the constraint; a smaller or more aggressively quantized model that passes its evaluation suite is frequently the better engineering answer, and on the fast path it is almost always the better answer.

## Quantization Selection {#ch-quant}

### Quantization is a workload decision with a stated price {#sec-quant-decision}

Quantization reduces the numerical precision of weights, and sometimes activations and the KV cache, to move fewer bytes and use faster hardware paths. The benefit is throughput and capacity. The cost is accuracy, and the professional obligation is to state the cost rather than let it be discovered later by users.

::: figure src=quantization-tradeoff.svg id=fig-quant width=full
Published Qwen3-8B figures on a single H100 with vLLM. The upper panel is accuracy on MMLU, with the axis starting at 72.8 so that the INT4 gap is visible rather than flattened. The lower panel is saturated aggregate throughput, where FP8 wins because Hopper has native FP8 tensor cores. The two panels rank the formats differently, which is the entire point of the chapter.
:::

Table. **Third-party published** quantization results for Qwen3-8B on a single H100 under vLLM: accuracy on MMLU and aggregate throughput under saturated ShareGPT-shaped load. Re-measure on your own prompt and output mix before committing; these figures are a starting point, not a guarantee. {#tbl-quant}

| Format | MMLU | Delta from BF16 | Saturated throughput | Relative throughput |
|---|---:|---:|---:|---:|
| BF16 | 74.78 | baseline | 13,305 tok/s | 1.00x |
| FP8 static | 74.79 | +0.01 | 16,452 tok/s | 1.24x |
| FP8 dynamic | 74.75 | -0.03 | 15,276 tok/s | 1.15x |
| INT8 dynamic | 74.84 | +0.06 | not reported here | not reported here |
| INT4 W4A16 | not reported here | not reported here | 13,605 tok/s | 1.02x |
| INT4 AWQ | 73.59 | -1.19 | 9,756 tok/s | 0.73x |
| INT4 GPTQ | 73.26 | -1.52 | not reported here | not reported here |

The headline result is that FP8 is close to free on this model: static FP8 matched BF16 on MMLU to within measurement noise while delivering 24 percent more saturated throughput. The 4-bit formats cost between 1.2 and 1.5 MMLU points, which is not rounding error, and under saturation they were slower than FP8 rather than faster, because their gain is in bytes moved and their loss is in dequantization overhead and less mature kernels.

### The rule that reconciles the two panels {#sec-quant-regime}

The apparent contradiction between "4-bit is faster" from Chapter 19 and "FP8 is faster" from the table above resolves cleanly once the regime is specified.

**At batch size one, latency critical, 4-bit wins.** The limiter is weight traffic through the memory system, and 4-bit moves roughly half the bytes of 8-bit. Use it for interactive routers and classifiers where a single request must complete as fast as possible, and where the accuracy cost has been measured on the specific task rather than assumed from a general benchmark.

**Under saturation, throughput critical, FP8 W8A8 wins on Hopper and newer.** The limiter is tensor core occupancy rather than memory traffic, and FP8 has a native hardware path while 4-bit requires dequantization work. Use it for synthesis pools, batch work and anything where many requests are in flight simultaneously.

This is why the topologies in Chapter 22 specify formats per pool rather than for the deployment: a router pool at FP8 or INT4 depending on measured single-stream latency, a synthesis pool at FP8, and on Blackwell hardware an NVFP4 option for large-model decode where the format has native support.

### Where quantization loss actually shows up {#sec-quant-loss}

Aggregate benchmarks hide the failures that matter for an agent platform, and this is the most important paragraph in the chapter.

A 1.2 point drop in MMLU is not evenly distributed across tasks. In practice it concentrates in behaviours that aggregate benchmarks barely sample: strict adherence to an output schema, correctness of extracted tool arguments, calibration of refusals, and stability of the margin between two similar capabilities. A quantized model that loses 1.2 MMLU points can lose 5 or 6 points of strict tool-argument correctness, and it can shift the routing margin distribution enough to invalidate a threshold calibrated on the previous format. Both failures are invisible on a general benchmark and immediately visible in production.

The obligation that follows is specific. Before a quantized model reaches the fast path, evaluate it on your own routing set, your own parameter extraction set and your own refusal set, and compare against the unquantized model on the same sets. A quantization swap is a model change, and Chapter 26 treats it as a change type that triggers the full suite selection for exactly this reason.

> **Warning.** Recalibrate escalation thresholds after any quantization change. Thresholds are properties of a model's score distribution, and quantization changes that distribution. A threshold carried across a format change is an unmeasured constant governing what fraction of traffic reaches your most expensive tier.

### Calibration sets, and the work nobody schedules {#sec-quant-calibration}

Post-training quantization methods that require a calibration set, which includes AWQ and GPTQ, are sensitive to what that set contains. A calibration set drawn from generic web text produces a model tuned for generic web text, and the control path's traffic is not generic web text: it is short, imperative, domain-specific and heavily templated.

Building a calibration set from a few hundred to a few thousand real control-path prompts, with the tokenizer and context length the production system uses, is a few days of work that materially improves quantized accuracy on the task that matters. It is also the first thing dropped when a quantization exercise runs late, which is why Chapter 25 lists calibration set design as a distinct capability rather than as part of general model work.

## Three Sizing Tiers {#ch-tiers-sizing}

### How to use these tiers {#sec-tiers-use}

The three topologies below are worked examples, not products. Each states a load point, the pools it implies, the GPU count, the utilisation target and the failure budget, so that a reader can locate their own load between two tiers and interpolate with the arithmetic of Chapter 18 rather than by analogy.

The single most important line in each is the utilisation target, and it is the line most often overridden by a finance conversation. Utilisation targets in this architecture are low by the standards of stateless web services, for a reason developed in Chapter 24: an inference pool near saturation has queue wait that dominates its own service time, so a router with a 20 ms service time at 85 percent utilisation is not a 24 ms router, it is a router whose p99 has left the budget entirely.

### Tier S: fewer than 10 customers {#sec-tier-s}

::: figure src=topology-tier-s.svg id=fig-tier-s width=full
The single-node pilot topology. One GPU holds the router, the guard classifier and a small synthesis model with isolated caches; frontier work and judges are rented rather than hosted. The notes are the operational commitments that make this tier honest: a written degraded mode, no premature hardware, and telemetry from the first day.
:::

One GPU, chosen for capacity and format flexibility rather than for bandwidth, is enough. A 96 GB Blackwell-generation workstation card holds a 4B FP8 router, an 86M guard classifier and an 8B FP8 synthesis model simultaneously with isolated KV caches, which is exactly the co-residency case that makes it the pragmatic choice at this tier. The host needs enough CPU and memory to run the serving stack, the registry, the session store and a local trace collector without competing with the GPU for attention.

Frontier reasoning is an API with pay-as-you-go pricing, because Tier 3 volume at this scale does not justify reserved capacity. Judges run against the API in overnight batches rather than sampling live traffic, which costs nothing during the day and produces the evaluation history that Tier M will need.

Table. Tier S sizing, derived from the chain in {tbl:load-chain} at under 40 peak concurrent sessions. **Modelled**. {#tbl-tier-s}

| Quantity | Value |
|---|---:|
| Peak concurrent sessions | under 40 |
| In-flight requests at peak | 3 to 6 |
| Control-path model calls per second | 4 to 8 |
| Control-path tokens per second | 800 to 1,600 |
| GPU count, steady state | 1 |
| Utilisation target | 20 to 35% |

#### The three commitments that make Tier S worth building {#sec-tier-s-notes}

**Write the degraded mode down before you need it.** One GPU is a single point of failure, and that is an acceptable trade at this tier only if the behaviour when it is gone has been decided in advance: deterministic routing plus templated answers for the journeys that can be served that way, and an explicit unavailability message for the rest.

**Do not buy HBM-class hardware here.** The purpose of Tier S is to measure your own workload, not to serve throughput you cannot yet use. Hardware bought before measurement is hardware bought from a guess, and the guess is usually wrong in the direction of too much.

**Instrument everything, immediately.** The expensive mistake at this tier is skipping telemetry, because Tier M must be sized from measured traffic and traffic that was not instrumented is gone. Every quantity in Section {sec:load-measure} should be collected from the first day of the pilot.

### Tier M: 1,000 to 5,000 concurrent {#sec-tier-m}

::: figure src=topology-tier-m.svg id=fig-tier-m width=full
The regional production topology, with pools separated by function rather than merged for utilisation. The upper band is latency-critical and scaled for p99; the lower band is throughput work that must never be able to consume the fast path's capacity. The notes state the three failure modes this separation exists to prevent.
:::

At Tier M the deployment stops being a node and becomes a set of pools, and the pool boundaries are the architecturally significant decision. Merging pools raises average utilisation and looks efficient on a dashboard; it also re-couples the workloads that were separated on purpose, so that a judge burst or a guard-model retry storm consumes the capacity the fast path needs.

Table. Tier M pools at 3,000 peak concurrent sessions, matching the chain worked in {tbl:load-chain}. Card choices are per-pool and follow the regime rule of Section {sec:quant-regime}. **Modelled**. {#tbl-tier-m}

| Pool | Hardware | Serves | Why this card |
|---|---|---|---|
| Router pool | 3 x L40S or RTX PRO 6000 | Tier 1 4B FP8, pinned and never preempted | Latency critical, small model, cheapest sufficient bandwidth. Sized so one node may fail |
| Guard pool | 2 x L40S | 86M classifier and 8B guard model | Isolated from user traffic so a rail retry storm cannot starve routing |
| Synthesis pool | 4 x H100 or H200 | Tier 2 8 to 32B FP8, continuous batching | Throughput critical under saturation, where FP8 on Hopper wins |
| Judge pool | 2 x L40S, own quota | Asynchronous sampling at 5 to 20% of turns | Assurance must have hard concurrency caps and its own budget |
| Frontier tier | API with reserved capacity | Tier 3 on 1 to 4% of turns | Escalation volume is now predictable enough to reserve, and a local fallback is defined |
| Durable workers | CPU only | Queue, workflow and retry execution | No GPU work; separated so long-running journeys cannot occupy request capacity |

Table. Tier M sizing summary. **Modelled** from {tbl:load-chain}. {#tbl-tier-m-sizing}

| Quantity | Value |
|---|---:|
| Peak concurrent sessions | 3,000 |
| In-flight requests at peak | about 260 |
| Control-path model calls per second | about 310 |
| Control-path tokens per second | about 62,000 |
| Guardrail calls per second | about 340 |
| GPU count, steady state | 11 plus 2 spare |
| Utilisation target, fast tier | 45 to 60% |

Three notes carry the reasoning. Separate pools exist to stop assurance and rail traffic from consuming fast-path capacity, and one shared pool re-couples exactly what the architecture just separated. The fast tier is sized on p99 under burst rather than on mean throughput, which is why its utilisation target is well under saturation. And frontier capacity should be reserved once escalation volume is predictable, because pay-as-you-go quota becomes the binding constraint before the local GPUs do, and discovering that during a traffic peak is an avoidable incident.

### Tier L: more than 50,000 concurrent {#sec-tier-l}

::: figure src=topology-tier-l.svg id=fig-tier-l width=full
The cell-based multi-region topology. The unit of capacity is a region cell that is replicated rather than a pool that is enlarged, prefill and decode are disaggregated so that long prompts cannot stall the decode queue, and each region is sized so that two of three can absorb the whole load. The notes name the availability risk at this scale, which is the control plane rather than the GPUs.
:::

Two structural changes distinguish Tier L from a larger Tier M.

**Prefill and decode are disaggregated.** Because the two phases have opposite bottlenecks, as Chapter 19 establishes, running them on the same nodes means a long prompt's prefill work stalls the decode queue and inflates inter-token latency for every concurrent user. Separating them lets each pool be sized and scaled by its own driver: prefill scales with prompt length and decode scales with concurrency. The cost is a new failure domain in the KV transfer path between them, and it is worth paying only once measurement shows one pool clearly starving the other.

**Capacity is bought in cells.** A cell is a complete regional unit with known behaviour. Growth adds cells rather than enlarging pools, because a pool that grows past its measured envelope degrades non-linearly at the tail, whereas a second cell behaves like the first.

Table. Tier L per-region cell at 50,000 plus peak concurrent sessions across three regions, each sized so that two surviving regions carry the full load. **Modelled**. {#tbl-tier-l}

| Component | Hardware | Scaling driver |
|---|---|---|
| Prefill nodes | 8 x B200 with NVFP4 | Compute bound; scales with prompt length |
| Decode nodes | 16 x H200 or B200 | Bandwidth bound with resident KV; scales with concurrency |
| KV transfer | NVLink and RDMA fabric | The prefill to decode handoff, and the new failure domain |
| Guard fleet | 6 x L40S per region | Scales with turns, not with tokens |
| Judge fleet | 8 x L40S, global | Batch, off-peak, hard budget |
| Frontier tier | Provisioned throughput | Committed capacity, not on-demand |
| Control plane | Replicated, with regional caches | Must survive the loss of a region |

Table. Tier L sizing summary. **Modelled** from {tbl:load-chain} scaled to the Tier L load point. {#tbl-tier-l-sizing}

| Quantity | Value |
|---|---:|
| Peak concurrent sessions | 50,000 plus |
| In-flight requests at peak | about 4,300 |
| Control-path model calls per second | about 5,200 |
| Control-path tokens per second | about 1,040,000 |
| Regions | 3, each sized for 2 of 3 surviving |
| GPU count per region | about 30 plus spares |
| Utilisation target, decode | 60 to 75% with admission control |

At this scale the availability risk moves from the GPUs to the control plane, which is the cost Section {sec:worse-control-plane} conceded in Part II arriving in its most expensive form. A registry outage that blocks routing takes every region down simultaneously, so regional last-known-good caches and static routes for critical journeys stop being good practice and become mandatory.

The other Tier L discipline is a hard budget for assurance traffic. At 50,000 concurrent sessions, sampling 10 percent of turns for judging is a larger inference workload than most Tier M deployments serve in total. Assurance at this scale is a capacity line item with its own fleet, its own quota and its own off-peak schedule, and treating it as an incidental overhead is how a quality initiative becomes a production incident.

### Reading between the tiers {#sec-tiers-between}

Table. The three tiers side by side. The ratios between columns are more useful than the absolute numbers: GPU count grows roughly linearly with concurrency once past the fixed cost of the first node, while operational complexity grows in steps at the points where a new isolation boundary is introduced. **Modelled**. {#tbl-tiers-compare}

| Dimension | Tier S | Tier M | Tier L |
|---|---:|---:|---:|
| Peak concurrent sessions | under 40 | 3,000 | 50,000 plus |
| Control-path tokens per second | 800 to 1,600 | about 62,000 | about 1,040,000 |
| GPUs, steady state | 1 | 11 plus 2 spare | about 90 across 3 regions |
| Distinct serving pools | 1 | 5 plus CPU workers | 7 per region plus global |
| Fast-tier utilisation target | 20 to 35% | 45 to 60% | 60 to 75% |
| Frontier posture | Pay as you go | Reserved capacity | Provisioned throughput |
| Judge posture | Overnight batch | 5 to 20% live sampling, own pool | Dedicated global fleet, off peak |
| Redundancy | None; written degraded mode | One node may fail per pool | Two of three regions carry full load |
| Platform engineers | 2 to 3 | 4 to 8 | 12 plus, with on-call rotation |

## Inference Performance, and How to Re-Measure It {#ch-perf}

### Why this chapter refuses to give you a number {#sec-perf-why}

Every published inference benchmark is a measurement of a specific model, at a specific quantization, on specific hardware, with a specific input and output length distribution, at a specific concurrency, on a specific version of a serving stack. Change any one of those and the result changes, sometimes by more than a factor of two. Quoting such a figure as a capacity planning input without reproducing its conditions is the most common way that sizing exercises produce confident wrong answers.

The figures below are therefore presented as anchors: they establish the order of magnitude and the shape of the relationships, and they are labelled **third-party published** so that no reader mistakes them for a guarantee about their own workload. The section that follows them is the operative part of the chapter, because it gives the commands to replace them.

### Published anchors {#sec-perf-anchors}

Table. **Third-party published** inference figures used as anchors in this document, with the conditions under which each was measured. Conditions are part of the figure; a number quoted without them is not a measurement. {#tbl-perf}

| Model and configuration | Measured result | Conditions as published |
|---|---|---|
| Llama 3.1 8B, H100, FP8 KV cache | 517.5 output tokens per second aggregate, 742.8 ms median time to first token | 150 requests at concurrency 8, roughly 20k input and 2k output tokens per request |
| Qwen3-8B, FP8 static, H100 | 16,452 tokens per second aggregate | Saturated ShareGPT-shaped traffic under vLLM |
| Qwen3-8B, INT4 AWQ, H100 | 9,756 tokens per second aggregate | Same harness and traffic as the FP8 row |
| Llama 3.3 70B, FP4, B200 | About 4x the H200 throughput on the same model | Vendor-reported comparison, FP4 against FP8 |
| Llama 3.3 70B, cost per million tokens | About 0.15 dollars on B200 against 0.37 dollars on H200 | Derived from the same vendor comparison, at published instance pricing |

Two observations about how to read these. The 742.8 ms median time to first token in the first row is not a contradiction of the 460 ms budget in Chapter 13; it is a measurement at 20,000 input tokens, which is roughly thirty times the control path's prompt length, and it illustrates precisely why the control path keeps prompts short. And the 4x claim in the fourth row is a format comparison as much as a hardware comparison: FP4 halves the bytes moved per token relative to FP8, and Blackwell has a native path for it, so the gain compounds.

### The re-measurement recipe {#sec-perf-recipe}

The following produces figures for your own model, hardware and traffic shape. Run it before buying anything, and again after every model, format or serving-stack change.

Start the server with the configuration you intend to run in production, not a default one. The context length, cache precision and memory fraction are all capacity decisions and all change the result.

```
vllm serve <model> \
  --quantization fp8 \
  --kv-cache-dtype fp8 \
  --max-model-len 8192 \
  --gpu-memory-utilization 0.90 \
  --max-num-seqs 64
```

Then drive it with the input and output length distribution your control path actually produces. Measuring with a generic dataset when your prompts are 700 tokens in and 120 tokens out will mislead you in both directions at once.

```
vllm bench serve \
  --model <model> \
  --dataset-name random \
  --random-input-len 700 \
  --random-output-len 120 \
  --max-concurrency 32 \
  --num-prompts 500 \
  --percentile-metrics ttft,tpot,itl,e2el
```

Sweep concurrency rather than measuring one point. A single concurrency figure tells you nothing about where the pool's knee is, and the knee is the only number that matters for capacity planning.

```
for c in 1 2 4 8 16 32 64 128; do
  vllm bench serve --model <model> --dataset-name random \
    --random-input-len 700 --random-output-len 120 \
    --max-concurrency $c --num-prompts $((c * 20)) \
    --percentile-metrics ttft,tpot,itl,e2el \
    --result-filename bench-c$c.json
done
```

### What to record, and what to conclude {#sec-perf-record}

Record six quantities at each concurrency point: time to first token at p50 and p99, time per output token, aggregate output tokens per second, request throughput, and the fraction of requests that were queued rather than served immediately. Plot aggregate throughput and p99 time to first token against concurrency on the same axis.

The shape of that plot is the deliverable. Throughput rises with concurrency and then flattens; p99 latency is flat and then rises sharply. The knee is where they cross your latency requirement, and the capacity of one card is the concurrency at that knee, not the concurrency at maximum throughput. Sizing from maximum throughput is how pools end up operating past their knee, where adding load adds queue wait and no throughput at all.

Two derived figures are worth computing immediately. Tokens per second per GPU at the knee, which converts the token demand from {tbl:load-chain} into a card count directly. And cost per million tokens at the knee, computed from the amortised hourly cost of the card, which is the figure that makes the on-prem versus API comparison of Chapter 15 a local calculation rather than an inherited one.

> **Design rule.** No hardware purchase without a knee curve for the intended model, format and traffic shape, produced on a rented or borrowed instance of the candidate card. The cost of a day of cloud rental is negligible against the cost of a fleet sized from someone else's benchmark.

## Behaviour Under Overload {#ch-overload}

### Every system is a queue, and this one has an unusually harsh one {#sec-overload-queue}

Inference pools behave worse under saturation than most services engineers have intuitions for, and the reason is that a GPU pool cannot shed work gracefully by degrading quality. It has a fixed rate of tokens it can produce, requests either fit in the batch or wait, and waiting requests hold their KV cache allocation while they wait, which reduces the memory available for the batch that is running.

Little's Law describes the consequence. Since the number in the system equals arrival rate times time in the system, and time in the system is service time plus queue wait, an arrival rate approaching the service rate makes queue wait grow without bound. In practice a pool at 85 percent utilisation with a 20 ms service time has queue wait several times its own service time, so the observed p99 is dominated by waiting rather than by working. This is the arithmetic behind the low utilisation targets in Chapter 22, and it is why "the GPUs are only 60 percent utilised" is a report of correct operation rather than of waste.

### Admission control is a design feature, not a failure {#sec-overload-admission}

A system without admission control does not avoid overload; it distributes the damage across every request instead of concentrating it in the requests it chose to reject. That is strictly worse, because it converts a partial outage into a total one and destroys the latency of the requests that would otherwise have succeeded.

Admission control needs three components. A measured signal that leads saturation rather than following it, which is queue depth or estimated wait rather than GPU utilisation, since utilisation is already at its maximum by the time the queue is long. A priority order decided in advance, so that when capacity is short the system knows what to protect: interactive user turns first, then rails, then asynchronous assurance, then shadow and canary traffic. And a rejection path that produces a useful response, meaning a named degradation with a retry hint rather than a timeout.

### The degradation ladder {#sec-overload-ladder}

Degradation should be a sequence of decided steps rather than an emergent property of what fails first. The ladder below is ordered by increasing user impact, and each rung is a control the platform can actuate deliberately.

Table. The degradation ladder, in the order it should be applied. Each rung has an actuation mechanism and a user-visible consequence, and both should be tested in production regularly rather than documented and hoped for. **Modelled** design guidance. {#tbl-degradation}

| Rung | Action | User-visible consequence | Actuated by |
|---:|---|---|---|
| 1 | Stop shadow, canary and replay traffic | None | Traffic manager, automatic on queue depth |
| 2 | Reduce judge sampling rate to zero | None; assurance history has a gap | Sampling policy, automatic |
| 3 | Disable Tier 3 escalation, answer at Tier 2 | Slightly weaker answers on the hardest 1 to 4% of turns | Escalation gate, automatic |
| 4 | Shorten context and disable optional retrieval | Less contextual answers, more clarifying questions | Planner policy, automatic |
| 5 | Serve Tier 0 templated answers for known intents | Terse but correct answers on common journeys | Router policy, automatic |
| 6 | Admission control: reject new sessions, protect existing ones | New users see a named unavailability message | Edge, automatic with a manual override |
| 7 | Read-only mode: refuse write journeys explicitly | Writes are refused with a clear reason and a retry channel | Manual, with an incident record |

Two properties make this ladder useful rather than decorative. The first four rungs are invisible to users and reclaim a substantial fraction of capacity, because assurance, escalation and long contexts are disproportionately expensive relative to the traffic they serve. And every rung is reversible automatically when the signal recovers, which matters because a ladder that requires a human to climb back down will be left at the bottom.

> **Warning.** An untested degraded mode is not a degraded mode. Each rung should be exercised in production on a schedule, at low traffic, with the results recorded. The failure to discover during an incident is that rung 5's templated answers were never wired to the current intent set.

### What to alert on {#sec-overload-alerts}

Alerting on GPU utilisation is a common mistake, because a healthy pool at its target utilisation looks identical to a saturated one until the queue is already long. Alert instead on queue depth and estimated wait time, on the p99 of time to first token by journey class, on the escalation rate to Tier 3, which spikes before a quality incident becomes visible, on rejection and degradation-rung activation counts, and on the ratio of retry traffic to first-attempt traffic, which is the earliest signal of a retry storm.

## The AI Engineering Capability Model {#ch-skills}

### Why this chapter exists {#sec-skills-why}

Architecture documents describe systems and omit the people, which is how organisations end up with a design they cannot staff. The capabilities below are the ones this architecture actually requires, stated so that a hiring plan or an outsourcing decision can be made from them. Intensity in the tables means depth of skill needed, not headcount: **aware** is being able to follow a runbook, **capable** is being able to operate and tune, and **deep** is being able to diagnose novel failures and extend the system.

::: figure src=skills-matrix.svg id=fig-skills width=full
The capability matrix by sizing tier, with the intensity required at each and where the capability usually sits organisationally. The lower panels are the two things worth taking from this chapter: the staffing anti-pattern that produces a single point of failure in a person, and a build order that front-loads evaluation because every later decision depends on being able to measure it.
:::

### The capabilities {#sec-skills-capabilities}

Table. Capabilities required by tier, with intensity and usual organisational home. Intensity is depth, not headcount; several capabilities can and should live in the same person at Tier S. {#tbl-skills}

| Capability | Tier S | Tier M | Tier L | Usually sits with |
|---|---|---|---|---|
| Inference serving: vLLM or SGLang operation | capable | deep | deep | Platform or ML infrastructure |
| Capacity modelling and load testing | aware | capable | deep | Platform |
| GPU scheduling, MIG and multi-tenancy | aware | capable | deep | ML infrastructure |
| Rollout, canary and rollback of model weights | aware | capable | deep | ML infrastructure |
| Quantization and calibration set design | aware | capable | deep | ML engineering |
| Distillation of routers and classifiers | not needed | capable | deep | ML engineering |
| Task fine-tuning, LoRA and adapters | aware | capable | deep | ML engineering |
| Tokenizer, context and prompt budgeting | capable | capable | deep | Shared |
| Evaluation engineering and golden set curation | capable | deep | deep | Domain plus platform |
| LLM-as-judge calibration against humans | aware | capable | deep | Evaluation owner |
| Safety, red teaming and rail tuning | aware | capable | deep | Security plus ML |
| Regression corpus and drift monitoring | aware | capable | deep | Platform |
| Distributed tracing and AgentOps | capable | deep | deep | Platform |
| Contract and manifest tooling | capable | capable | deep | Platform |
| Cost attribution per journey | aware | capable | deep | Platform plus finance |

### The four capabilities that are hardest to acquire {#sec-skills-scarce}

**Evaluation engineering.** The scarcest and most undervalued capability in the list. It is not writing test cases; it is deciding what correctness means for a domain, curating a golden set that stays representative as traffic changes, designing suites whose failure is diagnostic rather than merely red, and maintaining the regression corpus that grows from production incidents. Organisations reliably underinvest here because evaluation produces no visible feature, and reliably regret it, because every other decision in this document depends on being able to measure whether a change made things worse.

**Judge calibration.** Using a model to score outputs is easy; knowing whether those scores agree with human judgement is the hard part, and it requires periodic human labelling, agreement statistics, and recalibration whenever the judge model changes. An uncalibrated judge is a random number generator with a confident tone, and Chapter 27 treats it as such.

**Quantization with task-specific validation.** Running a quantization tool is a day of work. Knowing that the resulting model still extracts tool arguments correctly, still refuses what it should refuse, and still produces routing margins compatible with the calibrated thresholds is the work that actually matters, and it requires the evaluation capability above as a prerequisite.

**Distributed tracing for agent systems.** Conventional application tracing skills transfer, but agent traces have properties that conventional systems do not: spans carry model, tier, token count and cost; a single logical turn may involve retries and escalations that must be attributable; and the interesting question is usually why a decision was made rather than how long it took. Chapter 28 develops the semantics this requires.

### The staffing anti-pattern {#sec-skills-antipattern}

> **Anti-pattern.** One ML generalist owning serving, quantization, evaluation, safety and cost. It works during the pilot, because at Tier S the work genuinely fits in one competent person's head. It becomes the bus factor in production, and the first responsibility that gets dropped under pressure is always evaluation, because it is the only one with no immediate external consequence. The system then continues to ship changes with no measurement of whether they made it worse, which is the state this entire architecture exists to prevent.

The mitigation is not to hire five specialists at Tier S, which is unaffordable and unnecessary. It is to make ownership explicit even when it lives in one person, to write down what is being deferred rather than allowing it to be quietly dropped, and to treat the first additional hire as the one that removes the evaluation dependency rather than the one that adds a model capability.

### A defensible build order {#sec-skills-order}

The order below is chosen so that each capability makes the next one measurable, which is why it starts somewhere counter-intuitive.

**First, evaluation engineering, before any model is chosen.** Without it, model selection is aesthetic and every subsequent change is unfalsifiable. The first artefact of a serious agent platform should be a golden set, not a prompt.

**Second, serving and observability, then quantization.** You cannot quantize responsibly without being able to measure the result, and you cannot measure the result without traces and evaluation. Serving expertise also produces the knee curves of Chapter 23, which are the input to every hardware decision.

**Third, safety and rail tuning, as traffic grows.** Rails need real traffic to calibrate, because false positive rates on synthetic benign traffic are not informative about real users.

**Fourth, distillation and fine-tuning, last.** These have the highest ceiling and the highest prerequisite cost, and they are only worth doing once the workload is stable enough that a specialised model will not be obsolete before it is deployed. A team that starts here builds a beautifully tuned router for a routing problem that has since changed.

### Build, hire or outsource {#sec-skills-sourcing}

Table. Sourcing guidance by capability class. The pattern is that anything on the critical path of a release decision should be owned internally, and anything that is a one-off transformation can be bought. {#tbl-sourcing}

| Capability class | Recommendation | Reasoning |
|---|---|---|
| Evaluation engineering and golden sets | Build and own, always | It encodes what correctness means in your domains, which cannot be outsourced without outsourcing accountability |
| Judge calibration | Build, with external human labelling capacity | The method is portable; the labels are yours and need domain knowledge |
| Inference serving operation | Build at Tier M and above; managed service at Tier S | It is on the critical path of every request, and vendor abstractions leak exactly when latency matters |
| Quantization and distillation | Outsource or consult initially, internalise at Tier L | It is project-shaped work with clear deliverables, and the tooling changes fast |
| GPU infrastructure and scheduling | Cloud or colocation at Tier S and M; consider owning at Tier L | The crossover follows the same arithmetic as {tbl:frontier-cost} |
| Red teaming | External, on a schedule, plus internal continuous replay | Independence is the point, and internal teams develop blind spots by construction |
