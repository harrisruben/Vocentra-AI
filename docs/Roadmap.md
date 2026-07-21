# Vocentra AI - Product Development Roadmap

This document outlines upcoming feature pipelines and scalability enhancements.

---

## 1. Upcoming Architectural Milestones

### Milestone 1: Live WebSocket Streaming
Currently, ongoing calls and latency telemetry are updated via HTTP polling. The next iteration will migrate the active call streams to WebSockets:
```
Telephony Stream -> Vapi WebSocket -> Vocentra API -> Client React WebSocket
```
This enables real-time visual transcripts without polling overhead.

### Milestone 2: pgvector Native Integration
For larger knowledge documents, we will upgrade the SQLite mock embeddings store to a PostgreSQL pgvector extension instance, supporting fast Cosine Similarity index lookups (`ivfflat` or `hnsw`).

### Milestone 3: Telephony Media Stream Call Control
Bypass external voice aggregators (like Vapi) to feed Twilio Media Streams directly into a local Vocentra LLM/STT/TTS loop, reducing caller response latency to < 500ms.

---

## 2. Enterprise Feature Backlog

*   **SAML / SSO Integrations**: Support corporate identity provider integrations (Okta, Azure AD).
*   **Prometheus Metrics Scrapers**: Expose request latencies and rate limiter triggers for Grafana visualizations.
*   **Self-Hostable n8n Templates**: Provide n8n workflow blueprints in the repository for quick one-click cloud deployments.
