---
name: code-flow-audit
description: "Trace system behavior from entry points to data stores — understand unfamiliar backend codebases by reading controllers, hubs, services, models, and SQL generation in the right order."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [code-review, architecture, audit, flow-analysis, backend]
    related_skills: [requesting-code-review, systematic-debugging, codebase-inspection, github-code-review]
---

# Code Flow Audit

Understand how an unfamiliar backend system works by tracing code paths systematically from entry points to data stores. Designed for complex systems where the user has an existing mental model and needs validation, gap analysis, or architecture review.

## When to Use

- User shares their analysis of a system and asks "did I miss anything?"
- User asks "how does X flow through the system?" — trace from API → logic → DB
- Need to understand a complex module before making changes
- Architecture review of a subsystem (controllers, hubs, services, models)
- Security audit of data flow (where does user input reach SQL?)

**Not for:** pre-commit verification (use `requesting-code-review`), LOC metrics (use `codebase-inspection`), debugging a specific runtime bug (use `systematic-debugging`), or READ-ONLY API surface documentation (see **Variant: API Surface Documentation** below).

---

## Variant: API Surface Documentation

Sometimes the user doesn't want flow analysis — they want the **complete API call specification** (REST endpoints + SignalR methods + response formats). This variant compiles the full surface rather than tracing execution paths.

### When to Use

- User says "API 호출 스펙을 알려줘" or "tell me the API spec" or "그 api 호출 스펙"
- User needs a reference document for integration, client development, or testing
- Need a comprehensive endpoint inventory before writing tests or docs
- Quick onboarding to a new codebase's API surface

### Workflow

1. **Find all entry points** — list all `.cs` files, identify controllers and hubs. Pay attention to partial classes (SignalR Hubs often span multiple `*.cs` files)

2. **Read routing config** (`Program.cs` or `Startup.cs`):
   - `MapControllers()`, `MapHub<>()`, `UsePathBase()`, CORS
   - Connection strings / DB config (databases, contexts)
   - Static file paths
   - Swagger/OpenAPI settings
   - Authentication scheme (JWT Bearer, etc.)

3. **Extract all controllers** — for each, scan the file for:
   - `[Route("[controller]")]` template (controller class name = URL path)
   - `[ApiController]` attribute
   - Constructor dependencies (DB contexts, services)
   - Every public endpoint method with `[HttpGet]`/`[HttpPost]`/`[HttpPatch]`/`[HttpDelete]`/`[HttpPut]`
   - Method parameters — `[FromQuery]`, `[FromBody]`, path `{id}`
   - `[Authorize]` / `[AllowAnonymous]` attributes
   - Any `#if RELEASE` conditional auth guards
   - Pagination filter params (`page_number`, `page_size`, `search_field`, `search_word`)

4. **Extract SignalR Hub methods** — for each Hub partial class file:
   - Hub endpoint path (from `MapHub<SignalHub>("/hub")`)
   - Every `public async/void Task` method — these are client→server invocations
   - Every `Clients.*.SendAsync("ReceiveEventName", ...)` call — these are server→client events
   - `OnConnectedAsync` / `OnDisconnectedAsync` overrides
   - Connection/session management patterns (`Session.LoginUser`, connection ID tracking)

5. **Identify response wrapper** — find the common response envelope classes:
   - Single item: `{ data, succeeded, message, errors }`
   - Paged: `{ data, pageNumber, pageSize, totalPages, totalRecords, succeeded, message, errors }`
   - Error: `{ data: null, succeeded: false, message, errors: [...] }`

6. **Group endpoints by domain** — organize into logical groups (Auth, Users, Scenarios, Nodes, Analysis, Catalog, Home) with a readable table format:

   ```
   | Method | Endpoint | Auth | Description |
   |--------|----------|------|-------------|
   | GET    | /login   | ❌   | Login → JWT |
   ```

7. **Document SignalR methods in two tables:**
   - Client → Server (invokable methods with parameter types)
   - Server → Client (receive events with payload descriptions)

8. **Compile and deliver** — present as a comprehensive API reference. Mention Swagger UI URL if enabled. Save the session-specific spec as a `references/<project-name>-api-surface.md` file under this skill for future reuse (existing examples: `references/allre-be-api-surface.md`, `references/allre-be-node-flow-audit.md`).

### Comparison: Flow Audit vs Surface Documentation

| Aspect | Flow Audit | Surface Documentation |
|---|---|---|
| Goal | Understand execution path | Compile complete endpoint inventory |
| Reading depth | Deep (full handler logic) | Shallow (signatures + routing only) |
| Output | Architecture analysis + issues | Reference document (table format) |
| When | Fixing bugs, making changes | Integration, testing, documentation |
| SignalR | Trace specific method flows | List ALL methods and events |
| Auth check | Contextual (who calls what) | Systematic (endpoint by endpoint) |

---

## Step 1 — Map the Project Structure

Find all entry points first. In a .NET backend:

```bash
find /path/to/project -type f -name "*.cs" | sort
```

Identify:
- **Controllers** (`*Controller.cs` or route-decorated classes) — REST API entry points
- **Hubs** (`*Hub.cs`) — WebSocket/SignalR entry points
- **DataContext** / DbContext files — database boundaries
- **Models** — data shapes (entity classes)
- **Services / Business Logic** — processing layer
- **Signal / Event handlers** — async processing entry points

For other backends, map equivalent layers (e.g., Django: views → serializers → services → models; NestJS: controllers → services → repositories → entities).

## Step 2 — Read the User's Existing Analysis First

When the user provides their own analysis, read it **before** the code. This:
- Establishes the domain model and terminology
- Highlights what the user already knows
- Reveals their mental model so you can validate it against code

Save the user's analysis structure as a comparison template. Compare:
- **Entities/flow steps the user listed** vs what the code actually does
- **Flow order** (user's expected sequence vs actual sequence)
- **Missing types/handlers** (node types, API endpoints, execution paths)
- **Wrong assumptions** (e.g., classifying "copy" as a type when it's really a creation mode)

## Step 3 — Read Entry Points (Controllers)

Read the relevant controller files to understand the API surface:

```csharp
// Key things to note:
// 1. Route templates ([Route] attributes)
// 2. HTTP method + parameters
// 3. Validation logic (early returns)
// 4. Where control is handed off (Hub, Service, direct DB calls)
// 5. Creation vs configuration vs execution boundaries
```

Focus on:
- **POST endpoints** — they usually trigger state changes or creation
- **What gets saved to DB vs what gets queued for async execution**
- **Parameter mapping** — especially `type` fields that drive switch/case logic

## Step 4 — Read the Core Processing Logic (SignalR Hubs / Services)

This is where the real work happens. Read in dependency order:

1. **Dispatcher** (e.g., `Signal_Run.cs`) — the routing switch that picks the handler by type
2. **Common utilities** (e.g., `Signal_Common.cs`) — helper methods, validation, error handling
3. **Main handler** (e.g., `Signal_General.cs`) — the primary flow for the most common type
4. **Special handlers** — each unique type that branches off

For each handler, trace the full pipeline:

```
Validation → Data Cleanup → SQL Generation → SQL Execution → Result Update → Client Notification
```

Identify validation patterns that repeat across handlers — these are refactoring candidates.

## Step 5 — Read Data Models

Understand what data each entity carries by reading the model classes:

- **Primary keys** and relationships
- **Computed/NotMapped properties** — client-side logic disguised as model properties
- **Nullable fields** — indicate optional configuration paths
- **String fields used as enums** — look for switch/case values (e.g., `type: "union" / "general" / "general_DrugExposure"`)
- **Error flag fields** — (e.g., `valid_err`, `join_err`, `condition_err`) — reveal state tracking complexity

## Step 6 — Read SQL Generation in Detail

Dynamic SQL generation is where most bugs and security issues hide. Focus on:

1. **String interpolation points** — does user/field input appear directly in SQL strings?
2. **Table/column name escaping** — are identifiers backtick-quoted? What happens if a name contains special chars?
3. **DROP/CREATE patterns** — temporary table lifecycle management
4. **Transaction boundaries** — are DROP + CREATE + INSERT wrapped in a single transaction?
5. **Stored procedure generation** — dynamic CREATE PROCEDURE is especially risky (syntax errors at runtime)

```csharp
// Dangerous pattern — file at node_result.cs line ~92
search_query = $"\tAND ({filter.search_field} LIKE '%{filter.search_word}%')";
// Input directly interpolated — SQL injection vector
```

## Step 7 — Cross-Reference User Analysis vs Code Reality

Build a delta list:

| User's claim | Code reality | Impact |
|---|---|---|
| "copy is a node type" | Copy is a creation mode; real type comes from source node | Minor classification issue |
| "3 node types" | 5+ types including general_DrugExposure, general_DrugPattern | Missing execution paths |
| "result_column is redundant" | Partially true — but needed for code/tree join queries in result viewer | Hard to fully remove |

Separate into:
- **Conceptual gaps** — user didn't know about certain paths
- **Architecture issues** — real problems that need fixing
- **Data integrity risks** — injection, connection leaks, stale state

## Step 8 — Identify Cross-Cutting Issues

Check for these across ALL handlers:

- **SQL Injection** — any `$"string{userInput}"` in SQL context
- **Code Duplication** — same validation/cleanup/update logic in 3+ files
- **Connection Management** — are connections closed on both success AND error paths?
- **Transaction Safety** — are DDL statements (DROP/CREATE) inside transactions?
- **Static State** — is there static/global mutable state (Session.Command) that won't scale?
- **Concurrent Execution Guards** — what prevents two runs of the same node simultaneously?
- **Error Message Leakage** — do exceptions expose SQL or internal details to the client?

## Step 9 — Summarize for the User

Present findings in order of severity:

1. **Critical** — SQL injection, data corruption, security
2. **Architecture** — redundancy, coupling, scalability
3. **Code quality** — duplication, naming, consistency
4. **Gaps** — things the user missed in their analysis

Keep the same tone and terminology the user used in their analysis for coherence.

## Pitfalls

1. **Don't trust a single file.** Cross-reference — a controller might call a hub that calls a stored procedure. The full picture spans 3+ files.
2. **Language barrier.** If the code has non-English comments/identifiers (`환자번호`, `대장님`), note the terminology but don't let it distract from logic analysis.
3. **Static state is invisible.** `Session.Command`, `Session.LoginUser` — these are in-memory dictionaries, not in DB. They don't survive restarts or scale out. Don't miss them.
4. **Check both graph representations.** If both an Edge table and a Node.source field exist, verify they're consistent — dual representation is a common source of bugs.
5. **Dynamic SQL = higher risk.** Code that generates SQL at runtime (especially stored procedures) has a different error surface than ORM queries. Syntax errors surface at runtime, not compile time.
6. **Missing disconnection handler.** SignalR Hubs have `OnDisconnectedAsync` — if `Session.LoginUser` entries aren't cleaned up there, stale connections accumulate.
7. **topological sort vs numeric sort.** If RunNodeAll sorts target nodes by ID before executing, that's NOT a topological sort and may violate dependency order.
