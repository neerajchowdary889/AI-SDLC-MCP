# AI‑SLDC Mob Collaboration System — Detailed System Design (v1)

- *_Note: This is not proper documentation to refer to. This document is completely by AI so ignore document._*

## 0) What is “Mob Collaboration” in AI‑SLDC?

**Mob Collaboration** extends the idea of *mob programming* to the entire SDLC: a shared, always‑current **Mob Context** that every role (Dev, DevOps, QA, PM, Security, Leadership) and every **AI tool** can subscribe to via MCP. Instead of people pushing status to tools, tools stream status to the **Central Context Engine (CCE)**, which assembles role‑aware context packages on demand.

> North Star: Any teammate or AI agent can ask a question and receive a consistent, auditable snapshot that fuses code, tasks, docs, decisions, deployments, incidents, metrics, and **test results**.

---

## 1) High‑Level Architecture

```
External Tools (Jira/GitHub/Slack/Confluence/CI/CD/Monitoring)
      │  webhooks + scheduled pulls
      ▼
[Integration Layer]
  ├── Ingestion Gateways (REST/Webhooks/gRPC)
  ├── Normalizers (Common Context Schema)
  ├── Retry & DLQ (Kafka topics)
      │  normalized events
      ▼
[Context Processing Pipeline]
  ├── Enrichment (entity linking, summarization, PII redaction)
  ├── Vectorization (embeddings)
  ├── Indexing (Graph + Vector + Time‑series + Relational)
  ├── Versioning & Event Sourcing
      │  context updates
      ▼
[Central Context Engine (CCE)]
  ├── Context Graph Service (Neo4j)
  ├── Semantic Index (Weaviate/Pinecone)
  ├── Temporal Store (Timescale/InfluxDB)
  ├── Metadata & ACLs (Postgres)
  ├── Cache (Redis)
  ├── Context Assembler & Query Planner
      │  formatted context views
      ▼
[MCP Gateway]
  ├── REST + WebSocket (Server‑Sent Events optional)
  ├── Role‑Based Filters & ABAC/RBAC
  ├── Rate limiting / Quotas
      │  responses & subscriptions
      ▼
AI Tools / Agent Runtimes / Dashboards / Copilots
```

---

## 2) Core Services & Responsibilities

### 2.1 Integration Layer

* **Connectors**: Jira, GitHub/GitLab/Bitbucket, Confluence/Notion, Slack/Teams/Discord, Jenkins/GitHub Actions/GitLab CI, Datadog/New Relic/Grafana, S3/Artifactory, PagerDuty.
* **Mechanics**: Webhooks for realtime, scheduled sync for backfill; idempotent ingestion; exponential backoff; **DLQ** for poison messages.
* **Artifacts handled**: Issues, PRs, commits, build/deploys, incidents, logs, metrics, **test results**, documents, ADRs, meeting notes.

### 2.2 Context Processing Pipeline

1. **Ingestion** → 2) **Normalization** (Common Context Schema) →
2. **Enrichment** (NER/entity linking to repos, services, epics; auto‑summaries; PII redaction) →
3. **Vectorization** (text/code embeddings, code chunking by symbols) →
4. **Indexing** (Graph relations, Vector store, Time‑series signals, Postgres metadata) →
5. **Notify** (publish `context.update` events).

### 2.3 Central Context Engine (CCE)

* **Context Graph Service (Neo4j)**: nodes = `Repo`, `Service`, `Issue`, `PR`, `Commit`, `Build`, `Deploy`, `Incident`, `Doc`, `Decision`, `TestSuite`, `TestCase`, `TestRun`; edges = `relates_to`, `blocks`, `depends_on`, `verifies`, `introduced_by`, `affects`, `observed_in`.
* **Semantic Index**: per‑project namespaces; hybrid search (BM25 + vector); RAG chunk store with provenance.
* **Temporal Store**: CI timings, incident MTTR/MTBF, test flakiness, error budgets, throughput.
* **Assembler**: Plans optimal retrieval across stores; builds **Role‑Aware Context Packages** with verifiable provenance.
* **Versioning**: Event sourced; per‑entity **version vectors**; context diffs.

### 2.4 MCP Gateway

* **Interfaces**: REST + WebSocket; OAuth2/JWT; HMAC webhook verification; mTLS (internal).
* **Controls**: Rate limits (token bucket), quotas per AI tool, field‑level redaction.
* **Formats**: LLM‑friendly JSON with size caps; pagination; `since=timestamp` for incremental.

### 2.5 AI Tool Orchestrator

* Tool registration, API keys, scopes; **Context Subscription** topics; A/B test of prompts/context shape; usage analytics.

---

## 3) Data Model (Common Context Schema)

```json
{
  "id": "ctx_01H...",
  "org_id": "org_...",
  "project_id": "proj_...",
  "type": "issue|pr|commit|doc|decision|build|deploy|incident|test_run|test_case|test_suite",
  "source": {"system": "github|jira|confluence|jenkins|datadog", "external_id": "..."},
  "timestamps": {"created": "...", "updated": "...", "observed": "..."},
  "acl": {"visibility": "internal", "roles": ["dev","qa","pm"], "tags": ["pii_sanitized"]},
  "summary": "LLM/heuristic summary with provenance links",
  "content": {"raw": {}, "normalized": {}},
  "vectors": {"text": "vector_id", "code": "vector_id"},
  "relations": [{"type": "depends_on", "target_id": "ctx_...", "weight": 0.82}],
  "version": {"seq": 17, "hash": "sha256:...", "vv": {"github": 102, "jira": 342}},
  "provenance": [{"url": "...", "sha": "...", "line_range": [10,42]}]
}
```

### 3.1 Relationship Types (examples)

* `depends_on`, `blocks`, `relates_to`, `duplicates`, `child_of`, `owned_by`, `introduced_by` (commit→bug), `verifies` (test→feature), `observed_in` (incident→service), `deployed_by` (deploy→service).

### 3.2 Test‑Results Entities

* **TestSuite**: logical grouping; links to repo, service, and feature areas.
* **TestCase**: name, stable id, flakiness score, last 20 outcomes.
* **TestRun**: start/end, env, SHA/PR, artifacts, pass/fail/skips, coverage deltas.

---

## 4) Event & Topic Design (Kafka)

**Topics** (with compaction + tiered storage):

* `ingestion.raw.<system>` — raw webhook payloads.
* `ingestion.normalized` — Common Context messages.
* `context.updates` — post‑enrichment/indexing notifications.
* `context.search_audit` — audit of queries (who/what/why).
* `quality.test_results` — JUnit/xUnit/pytest/Allure normalized.
* `alerts.policy` — OPA/ABAC violations, PII detections.

**Normalized test result event (example)**

```json
{
  "type": "test_run",
  "project_id": "proj_xyz",
  "repo": "git@github.com:org/app",
  "sha": "abc123",
  "pr": 4821,
  "suite": "api_e2e",
  "env": "staging",
  "started_at": "2025-08-21T09:43:12Z",
  "ended_at": "2025-08-21T09:47:18Z",
  "summary": {"passed": 142, "failed": 3, "skipped": 2, "duration_sec": 246},
  "cases": [{"name": "orders_create_ok", "status": "passed", "duration_ms": 812}, {"name": "refund_flow", "status": "failed", "error": "500"}],
  "artifacts": ["s3://ci-logs/abc123/report.html"],
  "links": {"workflow_run": "https://github.com/..."}
}
```

---

## 5) MCP Gateway — API Surface (v1)

```
GET  /api/v1/context/{project_id}/full?since=ISO8601&limit=...
GET  /api/v1/context/{project_id}/tasks?role=dev&status=open
GET  /api/v1/context/{project_id}/code?repo=...&path=...&since=...
GET  /api/v1/context/{project_id}/docs?query=... (hybrid search)
GET  /api/v1/context/{project_id}/decisions?since=...
GET  /api/v1/context/{project_id}/role/{role}
GET  /api/v1/context/{project_id}/quality/tests?sha=...&suite=...
WS   /api/v1/subscribe  (events: context.update, test.run, incident.opened)
```

**Response contract (role view excerpt)**

```json
{
  "role": "dev",
  "as_of": "2025-08-23T12:00:00Z",
  "summary": "Feature X nearing completion; 3 failing tests; prod deploy paused",
  "highlights": [
    {"type": "issue", "id": "ctx_...", "title": "Fix flaky refund flow", "priority": "high"},
    {"type": "test_run", "suite": "payments_e2e", "failed": 2, "sha": "abc123"}
  ],
  "links": {"deep": ["ctx_...", "ctx_..."]}
}
```

---

## 6) Role‑Aware Context Views

* **Developer**: related PRs/commits, failing tests mapping to code owners, open issues, recent ADRs; local reproduction recipe.
* **DevOps/SRE**: latest deploys per service, error budgets, incident correlations to commits; runbooks.
* **QA**: flakiness map, coverage deltas per module, recent regressions tied to PRs.
* **PM/Leadership**: milestone burndown, critical path risks, blocked items, forecast vs plan; confidence bands.
* **Security**: vulns by severity, exposed secrets detections, SBOM diffs.

Each view is a **template** over the Common Context Schema + graph queries + time‑series slices.

---

## 7) Security, Compliance, Governance

* **AuthN**: OAuth2/OIDC; service accounts for CI; short‑lived JWTs; mTLS internal.
* **AuthZ**: RBAC + **ABAC** (project, repo, component sensitivity). OPA/Rego for policy decisions.
* **Data Protection**: AES‑GCM at rest (KMS), TLS 1.3 in transit; field‑level encryption for secrets; PII redaction in Enrichment.
* **Audit**: immutable access logs (WORM bucket); signed context packages; query purpose strings for AI tools.
* **Residency**: per‑tenant data plane choice; key‑scoped S3 buckets; DPA addenda.

---

## 8) Performance & Scalability

* **SLOs**: p99 context retrieval < 150 ms (warm), enrichment pipeline < 5 s for 95% of updates.
* **Sharding**: by `org_id/project_id`; graph and vector indexes co‑located.
* **Caching**: Redis for hot role views; etags + `since` cursors; write‑through on updates.
* **Backpressure**: circuit breakers per integration; bounded mailboxes; adaptive sampling of low‑value events.
* **Idempotency**: dedupe keys = (source, external\_id, revision);
* **Consistency**: eventual; monotonic reads per subscription; conflict resolution via **CRDT‑style** merges for tags/labels and last‑writer‑wins for scalar fields.

---

## 9) Observability & Reliability

* **Metrics**: ingestion lag, enrichment latency, index freshness, WS fanout time, error budgets.
* **Tracing**: OpenTelemetry across connectors → pipeline → CCE → MCP.
* **Logs**: structured JSON; correlation IDs from webhooks to responses.
* **Resilience**: multi‑AZ Kafka; DLQ reprocessing jobs; snapshot + PITR for Neo4j/Postgres; blue‑green MCP.

---

## 10) Test Results — End‑to‑End Flow

1. **GitHub Actions** job emits JUnit/Allure/pytest JSON + coverage.
2. **Uploader step** (action) posts to `POST /ingest/test-results` with repo, SHA, PR, suite, env, artifacts.
3. Ingestion → Normalization → `quality.test_results` → Enrichment (link to PR/Issues/Services) → Indexing.
4. Updates published on `context.update` and `test.run` WS channels; QA view updates flakiness scores.

**GitHub Action snippet (example)**

```yaml
- name: Upload test results to MCP
  uses: actions/upload-artifact@v4
  with:
    name: junit
    path: reports/junit.xml
- name: Post to MCP
  run: |
    curl -sS -X POST "$MCP_URL/ingest/test-results" \
      -H "Authorization: Bearer $MCP_TOKEN" \
      -H "Content-Type: application/json" \
      --data @<(jq -n --arg repo "$GITHUB_REPOSITORY" --arg sha "$GITHUB_SHA" \
        --arg pr "$PR_NUMBER" --arg suite "api_e2e" \
        --argfile junit reports/parsed_junit.json '{repo:$repo,sha:$sha,pr:$pr|tonumber?,suite:$suite,format:"junit",payload:$junit}')
```

**Webhook Receiver sketch (Go/Python)**

```pseudo
POST /ingest/test-results
  verify JWT + scope("ingest:test")
  parse payload → normalize cases
  publish to Kafka("quality.test_results")
  respond 202 Accepted
```

---

## 11) Deployment Blueprint

* **Kubernetes** (EKS/GKE/AKS), **Istio** service mesh, **ArgoCD** GitOps.
* **Data Plane**: Postgres (Cloud SQL/RDS), Neo4j Aura or self‑managed, Weaviate/Pinecone, Kafka (MSK/Confluent), TimescaleDB.
* **Secrets**: External Secrets Operator + cloud KMS; short‑lived tokens.
* **CDN**: for docs previews & reports; signed URLs for artifacts.

---

## 12) MVP → Phase Plan (team‑sized)

**Phase A (Weeks 0‑3)**

* Bootstraps: Org/Project/ACL model, OAuth, ingestion for GitHub, Jira.
* Minimal CCE: Postgres + Redis; later add Neo4j/Vector.
* Basic MCP endpoints: `/role/dev`, `/tasks`, `/quality/tests`.

**Phase B (Weeks 4‑7)**

* Add Neo4j, Vector store, Enrichment (summaries, entity linking), WS subscriptions.
* CI/CD connectors (GH Actions/Jenkins) + **test results** pipeline.

**Phase C (Weeks 8‑10)**

* Role templates for Dev/DevOps/QA/PM; dashboards; analytics (flakiness, lead time, DORA).
* Security hardening (OPA, audit trails), quotas, org‑level sharding.

---

## 13) Example Queries

* **Find failing tests tied to a feature in the last 48h**: graph traverse `(Feature) <-verifies- (TestCase) <-in- (TestRun{status=failed, t>now-48h})` then fetch commits.
* **Get PM snapshot**: open epics w/ blockers, PR age histogram, deploy readiness, risk register deltas.
* **Dev ask**: "What changed around refunds yesterday that broke staging?" → commits touching `refund*`, failed e2e, incident #, rollback.

---

## 14) Success Metrics (starter set)

* **Latency**: p99 MCP role view < 150 ms; WS update fanout < 1 s.
* **Freshness**: 95% of webhooks processed < 10 s.
* **Quality**: −50% flakiness in 6 weeks; +30% PR throughput; −40% time‑to‑context for incident triage.
* **Adoption**: ≥80% of repos integrated; ≥70% queries via MCP by month 2.

---

## 15) Risks & Mitigations

* **Tool API limits** → backoff + mirror caches + incremental sync.
* **LLM hallucinations** → provenance links + signed context + constrained prompts.
* **Data sprawl** → lifecycle policies, tiered storage, TTLs per artifact class.
* **Multi‑tenant isolation** → per‑tenant namespaces, network policies, per‑org KMS keys.

---

## 16) Next Steps (actionable)

1. Stand up skeleton MCP (Auth, `/role/dev`, `/quality/tests`).
2. Implement GitHub + Jira connectors; stream test results.
3. Add Neo4j + minimal vector index; wire Context Assembler.
4. Ship Dev/QA role templates; iterate with real usage.

---

## 17) “Attach‑Your‑AI” Contract (MCP‑First DX)

**Goal:** Any AI app/agent can request right‑sized, role‑aware context with provenance and safety guarantees.

### 17.1 Context Pack (portable contract)

```json
{
  "as_of": "2025-08-23T12:00:00Z",
  "project_id": "proj_...",
  "purpose": "qa|coding|planning|incident|pm-brief",
  "role": "dev|qa|pm|sre|lead",
  "scope": {"repos": ["app","svc-pay"], "time_window_h": 48, "entities": ["issue","pr","test_run","deploy","decision","doc"]},
  "budget_tokens": 6000,
  "pack": {
    "highlights": [ {"type":"issue","id":"ctx_...","title":"Refund flow failing"} ],
    "facts": [ {"k":"deploy.status","v":"paused","prov":"ctx_deploy_..."} ],
    "events": [ {"t":"2025-08-22T18:09Z","type":"test_run","summary":"2 failed"} ],
    "diffs": [ {"target":"svc-pay","sha":"abc123","summary":"changed refund handler"} ],
    "relations": [ {"src":"ctx_issue_1","rel":"verifies","dst":"ctx_test_9","w":0.83} ],
    "docs": [ {"title":"ADR‑042 Refunds","summary":"...","url":"..."} ],
    "citations": [ {"id":"ctx_...","url":"...","sha":"...","line_range":[10,42]} ]
  },
  "safety": {"redactions":["pii","secrets"], "license":"internal"}
}
```

### 17.2 MCP Gateway DX Endpoints (v1)

```
POST /api/v1/mcp/tools/register         # register an AI tool; returns tool_id, api_key, scopes
GET  /api/v1/mcp/capabilities           # available views, entities, limits
POST /api/v1/context/packs              # request a Context Pack (body: role, purpose, scope, budget_tokens)
WS   /api/v1/subscribe                   # topics: context.update, test.run, deploy, incident
POST /api/v1/feedback                   # user/tool feedback on usefulness & correctness
```

**Auth:** OAuth2 (client‑credentials) for servers, PAT for dev, short‑lived JWT for clients. Scopes: `read:context`, `read:tests`, `subscribe:*`, `ingest:*`.

### 17.3 Response shaping

* `budget_tokens` honored with hierarchical compression (dedupe, quote‑squeeze, abstractive summaries w/ citations).
* `since` and `cursor` for incremental packs.
* `accept: application/vnd.mcp.contextpack+json;v=1` for versioning.

---

## 18) Canonical Query Patterns → Answer Plans

**Why:** Make AIs reliably useful with templated retrieval + reasoning.

1. **Resolve a question (Q\&A/RAG)**

```
Input → classify(intent, role) → fetch Context Pack → inject into system prompt →
constrained answer with inline citations → refusal if provenance missing.
```

**Prompt scaffold (system):**

```
You are an assistant for {role}. Use ONLY the Context Pack and cite with [ctx_id].
If missing evidence, say what else is needed. Prefer concise bullet answers.
```

2. **Code better (coding copilot)**

* Retrieve: nearest code chunks (symbol‑aware) + related PRs + failing tests.
* Tools: `get_diff`, `find_related`, `tests_for(symbol)`, `owner_for(path)`.
* Output: patch suggestions + references to tests to run.

3. **Understand the whole thing (map view)**

* Graph traversal: service ←deploys← build ←commit ←PR ←issue; include ADRs.
* Render: service overview + dependency risks + last 24h changes.

4. **What’s happening across the team (situational awareness)**

* Roll‑up: issues opened/closed, PR aging, failing suites, incidents, deploys.
* SLOs: DORA metrics slice + notable outliers.

5. **What to build next (planning)**

* Inputs: roadmap epics, blockers, customer signals, risk register, test debt.
* Heuristic: value × confidence ÷ effort; governance: policy check via OPA.

---

## 19) Planning APIs — “Now / Next / Later”

```
GET /api/v1/planning/nnl?project_id=...&horizon_weeks=4
→ {
  "as_of":"2025-08-23T12:00Z",
  "now":[{"id":"ctx_issue_42","why":"unblocks payments deploy","effort":"M"}],
  "next":[{"id":"ctx_epic_9","why":"largest user impact","confidence":0.7}],
  "later":[{"id":"ctx_techdebt_3","why":"reduces flakiness 30%"}],
  "evidence":["ctx_test_run_...","ctx_decision_..."],
  "constraints":["error_budget_low","oncall_saturated"]
}
```

---

## 20) Example Clients

### 20.1 TypeScript (Node) — Q\&A with Context Pack

```ts
import fetch from "node-fetch";
const token = process.env.MCP_TOKEN!;

async function getPack(q: string) {
  const res = await fetch(`${process.env.MCP_URL}/api/v1/context/packs`, {
    method: "POST",
    headers: {"Authorization":`Bearer ${token}","Content-Type":"application/json"},
    body: JSON.stringify({ role:"dev", purpose:"qa", scope:{ time_window_h:48 }, budget_tokens:6000, query:q })
  });
  return res.json();
}

(async () => {
  const pack = await getPack("Why did refund tests fail yesterday?");
  // inject `pack` into your LLM system prompt and ask the model to answer with [ctx_id] citations
})();
```

### 20.2 Python — Streaming updates (WebSocket)

```python
import websockets, asyncio, json, os
async def main():
    async with websockets.connect(os.getenv("MCP_WS"), extra_headers={"Authorization":f"Bearer {os.getenv('MCP_TOKEN')}"}) as ws:
        await ws.send(json.dumps({"action":"subscribe","topics":["context.update","test.run"]}))
        async for msg in ws:
            event = json.loads(msg)
            handle(event)  # route to your AI agent
asyncio.run(main())
```

---

## 21) Safety, Redaction, Minimization

* **Least‑Context Principle:** Default to minimal sufficient context; expand on demand.
* **Field‑level redaction:** PII/secrets masked at enrichment; policy‑gated rehydration by role.
* **Signed Context Packs:** include `hash` and signature; AIs verify integrity.
* **Hallucination guard:** require citations; answer size caps; block speculative commands.

---

## 22) KPIs & Experiments

* **Context Hit‑Rate\@k** (did the pack include the needed doc/commit/test?).
* **Attribution\@k** (answer cited correct sources).
* **Time‑to‑Useful‑Answer (TTUA)** and **PR Throughput Δ** post‑adoption.
* **Quality**: Test flakiness −X%, Incident MTTR −Y%.
* **A/B**: context shapes (flat vs graph‑heavy), summary lengths, token budgets.

---

## 23) Rollout Checklist (Team of 10–30)

1. Wire GitHub + Jira + CI test results (MVP packs for `dev`, `qa`).
2. Ship WS subscriptions and `/planning/nnl` for PMs.
3. Add Neo4j relations + vector RAG for docs/ADRs.
4. Enforce OPA policies + signed packs + audit trails.
5. Dogfood with your IDE copilot + Slack bot; iterate on prompts.
