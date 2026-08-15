# Federated Agent Platform Demo

A visual-first local prototype of a federated enterprise agent architecture.

**Centralize orchestration, assurance, and observability. Federate domain intelligence and delivery.**

## Phase 1 — Guided visual demo

Phase 1 is a polished Next.js console. A presenter can walk the full architectural story with Next / Back. No LLM credentials, A2A servers, Langfuse, or other external services are required.

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). Use **Next** / **Back**, arrow keys, or `?step=7` to jump to a guided step.

## White paper

The architecture behind the prototype is documented in full in
[`docs/whitepaper/whitepaper.md`](docs/whitepaper/whitepaper.md), with a typeset
PDF at
[`docs/whitepaper/out/Federated_Enterprise_Agent_Platform_v1.0.pdf`](docs/whitepaper/out/Federated_Enterprise_Agent_Platform_v1.0.pdf).
It covers the adversarial design rationale, the guardrail cascade, the on-prem
quantized versus frontier-API trade, and hardware sizing across three load
tiers. Both artifacts are generated from the same source; see
[`docs/whitepaper/README.md`](docs/whitepaper/README.md) to rebuild.

## Modes

- **Guided Demo Mode** — deterministic mocked events, presentation-ready.
- **Live Mode** — reserved for Phase 2 FastAPI services. If the live backend is unavailable, the UI stays in demo mode.

## Architecture (Phase 2 target)

Three independently runnable FastAPI services plus this UI:

| Service        | Port |
| -------------- | ---- |
| Central        | 8000 |
| Rewards        | 8001 |
| Transactions   | 8002 |
| Next.js UI     | 3000 |
