# AllRe-BE REST API + SignalR Surface

**Project:** .NET 7, C#, MySQL (3 databases), SignalR  
**Analyzed:** 2026-07-13  
**Codebase:** AllreBE.RestAPI + AllreBE.Models + AllreBE.Common  

## System Overview

| Property | Value |
|---|---|
| Framework | .NET 7 Web API |
| Auth | JWT Bearer (`Authorization: Bearer ***` |
| DB | MySQL × 3: `allre` (main), `fact` (analysis), `result` (analysis results) |
| SignalR Hub | `/hub` |
| Static Files | `/File` → `C:\Allre\File` |
| Swagger | `/swagger` (development mode — `#if !RELEASE` disables auth) |
| CORS | AllowCredentials + AllowAnyHeader + DELETE/GET/PATCH only |

## Base URL Pattern

All controllers use `[Route("[controller]")]` — the URL is the **controller class name** in lowercase.

**PaginationFilter query params** (common): `?page_number=1&page_size=20&search_field=제목&search_word=검색어`

---

## REST API Endpoints

### Common (인증/사용자/기관)

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/login` | ❌ | Login → JWT token. Body: `{ User_id, Adata }` |
| `GET` | `/login` | ✅ | Login status check |
| `GET` | `/auth?auth_id={id}` | ❌ | 권한 목록 조회 (admin: 하위권한까지) |
| `GET` | `/user` | ✅ | 사용자 목록 (paginated, filterable) |
| `GET` | `/user/{id}` | ✅ | 사용자 상세 (user_info + user_request) |
| `POST` | `/user` | ❌ | 회원가입 (status="대기") |
| `PATCH` | `/user/{id}` | ✅ | 사용자 정보 수정 (partial) |
| `DELETE` | `/user/{id}` | ✅ | 회원 탈퇴 (soft delete, status="탈퇴") |
| `GET` | `/org` | ❌ | 기관 목록 |
| `GET` | `/group` | ❌ | 그룹 목록 |
| `GET` | `/fact` | ❌ | 팩트/통계 정보 |
| `POST` | `/upload_file` | ❌ | 파일 업로드 |

**auth query params:** `auth_id` (optional — empty = all, set = filter by level)

### Scenario (시나리오 + 노드)

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/scn` | ✅ | 시나리오 목록. Params: `user_id, auth_id, tab_menu, scn_type, is_scn` |
| `GET` | `/scn/{id}` | ✅ | 시나리오 상세 (`?user_id=xxx`) |
| `POST` | `/scn` | ✅ | 시나리오 생성. Body: `{ user_id, title, note, org_id, is_scn }` |
| `PATCH` | `/scn/{id}` | ✅ | 시나리오 수정 |
| `DELETE` | `/scn/{id}` | ✅ | 시나리오 삭제 |
| `GET` | `/tab` | ❌ | 열려있는 탭(시나리오) 정보 |
| `GET` | `/node?scn_id={id}` | ✅ | 노드 목록 (시나리오별 full tree) |
| `GET` | `/node/{id}` | ✅ | 노드 상세 |
| `POST` | `/node` | ✅ | 노드 생성 |
| `PATCH` | `/node/{id}` | ✅ | 노드 수정 |
| `DELETE` | `/node/{id}` | ✅ | 노드 삭제 |
| `GET` | `/node_table` | ❌ | 노드 테이블 설정 조회 |
| `GET` | `/node_join` | ❌ | 노드 조인 키 설정 |
| `GET` | `/node_result` | ❌ | 노드 실행 결과 데이터 |
| `GET` | `/condition` | ❌ | 조건(WHERE) 설정 |
| `GET` | `/condition_item` | ❌ | 조건 항목 |
| `GET` | `/condition_drug` | ❌ | 약물 조건 |
| `GET` | `/condition_in` | ❌ | 조건 IN절 |
| `GET` | `/condition_nearest` | ❌ | 근저값 조건 |
| `GET` | `/addition` | ❌ | 변수추가 설정 |
| `GET` | `/addition_in` | ❌ | 변수추가 IN값 |
| `GET` | `/addition_item` | ❌ | 변수추가 항목 |
| `GET` | `/addition_when` | ❌ | CASE WHEN 조건 |
| `GET` | `/output` | ❌ | 출력 컬럼 설정 |
| `GET` | `/result_column` | ❌ | 결과 컬럼 메타데이터 |
| `POST` | `/copy` | ✅ | 시나리오/노드 복사 |
| `GET` | `/funnel` | ❌ | 퍼널 정보 |
| `GET` | `/preset` | ❌ | 프리셋 목록 |
| `GET` | `/scn_bookmark` | ❌ | 즐겨찾기 목록 |
| `GET` | `/scn_user` | ❌ | 시나리오 공유 사용자 |

**scn tab_menu:** `전체시나리오`, `나의시나리오`, `즐겨찾기`  
**scn scn_type:** `선택안함`, `공유`, `비공개`  
**node type values:** `general`, `union`, `intersection`, `difference`, `general_DrugExposure`, `general_DrugPattern`, `general_Nearest`, `catalog`

### Analysis (분석 시각화)

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/analysis` | ✅ | 분석 목록. Params: `scn_id, node_id, standby_node_id` |
| `POST` | `/analysis` | ✅ | 분석 생성. `analysis_type`: treemap, sankey, sunburst, psm, eda |
| `PATCH` | `/analysis/{id}` | ✅ | 분석 수정 (name) |
| `DELETE` | `/analysis/{id}` | ✅ | 분석 삭제 (하위 stored proc + 결과 테이블 정리) |
| `GET` | `/analysis_item` | ❌ | 분석 항목 |
| `GET` | `/analysis_pattern` | ❌ | 분석 패턴 |
| `GET` | `/analysis_psm` | ❌ | PSM 설정 |
| `GET` | `/analysis_content` | ❌ | 분석 컨텐츠 |
| `GET` | `/analysis_file` | ❌ | 분석 파일 |
| `GET` | `/analysis_set` | ❌ | 분석 세트 |
| `GET` | `/analysis_eda` | ❌ | EDA 설정 |
| `GET` | `/analysis_sankey` | ❌ | Sankey 차트 데이터 |
| `GET` | `/analysis_sunburst` | ❌ | Sunburst 차트 데이터 |
| `GET` | `/analysis_treemap` | ❌ | Treemap 차트 데이터 |
| `GET` | `/eda` | ❌ | EDA 데이터 |

**analysis_type values:** `treemap` (auto-creates 2 items: operation+icd9cm, drug+atc), `sankey` (auto-creates pattern_type=3), `sunburst` (auto-creates pattern_type=3), `psm` (auto-creates caliper=0.1), `eda`

### Catalog (PICOT / 카탈로그)

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/picot` | ❌ | PICOT 설정 |
| `GET` | `/picot_in` | ❌ | PICOT 입력값 |
| `GET` | `/picot_item` | ❌ | PICOT 항목 |
| `GET` | `/catalog_result` | ❌ | 카탈로그 실행 결과 |

### Home

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/notice` | ❌ | 공지사항 |
| `GET` | `/qna` | ❌ | Q&A 목록 |
| `GET` | `/qna_reply` | ❌ | Q&A 답변 |
| `GET` | `/chart` | ❌ | 대시보드 차트 데이터 |
| `GET` | `/cro` | ❌ | CRO 정보 |

### Fact (팩트 테이블)

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/disease` | ❌ | 질병 목록 |
| `GET` | `/fact_table` | ❌ | 팩트 테이블 목록 |
| `GET` | `/fact_column` | ❌ | 팩트 컬럼 목록 |

---

## 🔌 SignalR Hub (`/hub`)

### Client → Server (Invokable Methods)

| Method | Parameters | Description |
|---|---|---|
| `Connect` | `(string user_id)` | Register connection session |
| `RunNode` | `(string user_id, string node_id)` | Execute a single node |
| `RunNodeAll` | `(string user_id, string node_id)` | Execute node + all children (BFS traversal) |
| `CancelNode` | `(string user_id, string node_id)` | Cancel running node |
| `RunNodeTest` | `(string node_id)` | Node test execution (for development) |
| `SendMessage` | `(string user, string message)` | Chat test (broadcasts to all) |

### Server → Client (Received Events)

| Event Name | Payload Description | When |
|---|---|---|
| `ReceiveResult` | `{ node_id, scn_id, status, success, message, ... }` | Node execution status change |
| `AnalysisResult` | `{ node_id, scn_id, analysis_id, status, success, message, error }` | Analysis execution result |
| `ReceiveMessage` | `(string user, string message)` | Chat message broadcast |

**ReceiveResult status values:** `running`, `success`, `fail`

### Hub Implementation Details

- **Partial class** — spread across `Signal_Run.cs`, `Signal_Common.cs`, `Signal_General.cs`, `Signal_UID.cs`, `Signal_Test.cs`, `Signal_Drug.cs`, `Signal_DrugPattern.cs`, `Signal_Nearest.cs`, `Signal_EDA.cs`, `Signal_Sankey.cs`, `Signal_Sunburst.cs`, `Signal_Treemap.cs`, `Signal_Cox.cs`, `Signal_Kaplan.cs`, `Signal_Logistic.cs`, `Signal_Comparison.cs`, `Signal_PSM.cs`, `Signal_RunCatalog.cs`
- **Connection tracking:** `Session.LoginUser` static dictionary (connection_id → user_id)
- **Execution tracking:** `Session.Command` static dictionary (node_id → DbCommand for cancellation)
- **Broadcast:** `ReturnJsonAll()` sends to all users who have the scn tab open (uses `tab` table)
- **Node dispatch type switch:** `union`/`intersection`/`difference` → `StartNodeUID`, `general_DrugExposure` → Python, `general_DrugPattern`/`general_Nearest` → handlers, default → `StartNode` (general node)

---

## 📦 Response Wrapper Format

### Success (Single Item)
```json
{
  "data": { ... },
  "succeeded": true,
  "message": "...",
  "errors": null
}
```

### Success (Paged)
```json
{
  "data": [ ... ],
  "pageNumber": 1,
  "pageSize": 20,
  "totalPages": 5,
  "totalRecords": 100,
  "succeeded": true,
  "message": null,
  "errors": null
}
```

### Error
```json
{
  "data": null,
  "succeeded": false,
  "message": "...",
  "errors": ["..."]
}
```

---

## 🗄️ Database Contexts

| Context | Connection Key | Purpose |
|---|---|---|
| `DataContext` | `localConnection` | Main app DB: users, scenarios, nodes, settings |
| `DataContextFact` | `factConnection` | Analysis fact data (drug, diagnosis, procedure) |
| `DataContextResult` | `resultConnection` | Analysis result tables (dynamically created) |

---

## 🔐 Auth Notes

- `[Authorize]` is wrapped in `#if RELEASE` on many controllers — in **Development** mode auth is bypassed
- JWT token returned by `POST /login` contains: `User_id`, `Guid_id`, `user_name`, `auth_id`, `status`, `org_id`
- Auth levels: `admin` > `manager` > `member` > `none`
- CORS only allows `DELETE`, `GET`, `PATCH` methods (notably missing POST and PUT)

## 📁 Static File Serving

```
URL: /File/{filename}
Path: C:\Allre\File\{filename}
```