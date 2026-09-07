# Governance peer compatibility matrix

Snapshot: 2026-08-13. Source: #161.

Full machine-readable detail: `docs/research/governance-peer-compatibility-matrix.json`.

The completed research covers 60 peers/systems. 52 have a bounded interoperability candidate surface and 8 are retained as conceptual/control alignment only. No entry is claimed as a production validated integration.

| Family | Reviewed peers | Result |
|---|---|---|
| Governance / control planes | Microsoft Agent Governance Toolkit (AGT), Coral Server / CoralOS, Cordum, Gate22, IBM MCP Context Forge, Invariant Guardrails, LiteLLM, Proofpane Architecture, Regulus, TrinityGuard | 9 candidate, 1 alignment |
| Temporal policy | Dogwood | 1 candidate, 0 alignment |
| Attestation / trust evidence | TRACE, Agent Manifest, cMCP, cA2A, Agent Passport System, Signed Decision Receipts, SourceryKit | 7 candidate, 0 alignment |
| Identity / attestation | SPIFFE / SVID, W3C Decentralized Identifiers (DID) | 2 candidate, 0 alignment |
| Confidential runtime / attestation | OPAQUE Systems / OPAQUE platform | 1 candidate, 0 alignment |
| Policy as code | Cedar, Open Policy Agent (OPA), SpiceDB, Apache Casbin | 4 candidate, 0 alignment |
| Observability / trace | OpenTelemetry, Arize Phoenix, Langfuse, Provena, AgentOps, MLflow, Helicone, traceAI | 8 candidate, 0 alignment |
| Security / adversarial evidence | NVIDIA garak, Microsoft PyRIT, Snyk Agent Scan, CyberSecEval, Microsoft Counterfit, HouYi | 6 candidate, 0 alignment |
| Agent frameworks | LangGraph, OpenAI Agents SDK, Google ADK, Microsoft Agent Framework, AutoGen, Semantic Kernel, CrewAI, PydanticAI, LlamaIndex, AgentScope, smolagents | 11 candidate, 0 alignment |
| Standards / controls / protocols | OWASP AISVS, Model Context Protocol (MCP), Agent2Agent (A2A), PIC Standard, SPDX 3 AI/Dataset/Security profiles, NIST AI RMF / Generative AI Profile, OWASP Agentic Applications Top 10, CSA Agentic Trust Framework, Singapore IMDA Agentic AI governance framework, CoSAI Risk Map | 3 candidate, 7 alignment |

## Cross-cutting result

Existing Agent Memory generic boundaries cover the reviewed landscape: governance-context projection, external evidence normalization, monotonic policy composition, runtime correlation, adversarial-evidence normalization, framework lifecycle events, standards crosswalks, and explicit reusable-grant transitions.

Dogwood is included as a history-aware policy comparator. Its event history is not canonical Agent Memory state, and a prior matching event does not by itself become reusable permission.

Comparator/profile evidence is kept distinct from production integration. Future peer-specific adapters should be added only for concrete use cases. Broader memory architecture discovery continues under #67.
