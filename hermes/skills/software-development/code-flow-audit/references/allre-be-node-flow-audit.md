# AllRe-BE Node Processing Flow Audit

**Project:** .NET 7, C#, MySQL, SignalR  
**Analyzed:** 2026-07-13  
**Codebase:** AllreBE.RestAPI + AllreBE.Models + AllreBE.Common  

## System Architecture

```
Client (React FE)
  │  REST API (Controllers)
  │    POST /node          → 노드 생성 (general/copy/union/intersection/difference)
  │    POST /node_table    → 조인 테이블 메타 저장
  │    POST /node_join     → 조인 키 저장
  │    POST /condition*    → WHERE 조건 저장
  │    POST /addition*     → 집계/계산 변수 저장
  │    POST /output        → 출력 컬럼 저장
  │
  │  SignalR Hub (/hub)
  │    RunNode(user_id, node_id)       → 단일 노드 실행
  │    RunNodeAll(user_id, node_id)    → 하위 전체 실행
  │    CancelNode(user_id, node_id)    → 실행 취소
```

## Node Type Dispatch (Signal_Run.cs)

```
RunNode()
  ├─ case "union" / "intersection" / "difference"
  │     → StartNodeUID()          [Signal_UID.cs]
  ├─ case "general_DrugExposure"
  │     → PythonStart_Drugexposure_mysql()  [Signal_Drug.cs, 2696줄]
  ├─ case "general_DrugPattern"
  │     → StartNodeDrugPattern()  [Signal_DrugPattern.cs]
  ├─ case "general_Nearest"
  │     → StartNodeNearest()      [Signal_Nearest.cs, 1230줄]
  └─ default (general)
        → StartNode()             [Signal_General.cs, 2276줄]
```

## 일반 노드 실행 파이프라인 (Signal_General.cs → StartNode())

```
1. 노드 설정 로드 (node_table, node_join, condition*, addition*, output, selection)
2. Validation:
   - node_table 존재 확인
   - node_join 컬럼 입력 확인
   - condition_item 테이블 존재 확인
   - addition 유효성 체크 (case/일반/계산 세분기)
   - 중복 컬럼명 체크
   - 상위 result 컬럼 존재 확인 (re alias)
3. result_column + EDA 데이터 삭제 (node_id 기준)
4. DROP TABLE IF EXISTS result.result_{node_id}
5. CREATE TABLE result.result_{node_id} (output + addition → result_column → sql_type)
6. 차일드 노드 느낌표 검증 (상위 컬럼 존재 여부 체크, 400줄)
7. INSERT INTO result.result_{node_id} (SELECT ... FROM/FROM/JOIN/WHERE)
8. SQL 실행 (ExecuteNonQueryAsync, 3600초 타임아웃)
9. COUNT(DISTINCT 환자번호) + COUNT(*) → node.pat_count, node.count 업데이트
10. 차일드 노드 상태 업데이트
```

## 집합 노드 (Signal_UID.cs → StartNodeUID())

```
1. source 노드들의 result_column 병합 (차집합: 첫 번째 소스만)
2. result_column + output 삭제 후 재생성
3. DROP + CREATE TABLE
4-1. UNION (합집합): 각 source SELECT 결과를 UNION
4-2. INTERSECTION (교집합): 첫 소스에 나머지 INNER JOIN
4-3. DIFFERENCE (차집합): 첫 소스에서 나머지 NOT IN
5. SQL 실행 + 카운트 업데이트
```

## 발견된 주요 이슈

### 1. SQL Injection
- `node_result.cs` L92: `search_word`를 LIKE절에 문자열 보간
- INSERT 컬럼 목록을 `output.name`에서 직접 가져옴 (L909-917)

### 2. 위상 정렬 누락
- `RunNodeAll`에서 `targetIds.Sort()`로 단순 숫자 정렬 후 실행
- 의존성 무시 → 오류 가능성

### 3. 이중 그래프 표현
- Edge 테이블 + Node.source 필드 모두 그래프 정보 저장
- 데이터 일관성 문제 발생 가능

### 4. 심각한 코드 중복
- result_column/EDA 삭제 로직: Signal_General, Signal_Nearest, Signal_Drug, Signal_UID
- addition 유효성 체크: Signal_General, Signal_Nearest
- 차일드 노드 느낌표 로직 (400줄): Signal_General, Signal_Nearest

### 5. Connection 관리
- `CloseConnection()`이 일부 성공 경로에서만 호출됨
- 에러 경로에서 `NodeError`가 닫지만, 모든 경로 검증 필요

### 6. Static 상태
- `Session.Command` (static Dictionary) → scale-out 불가
- 연결 해제 시 `OnDisconnectedAsync`에서 Session cleanup 확인 필요

### 7. 성능
- 복제(copy) 시 `node_table` 루프 내 매번 `db.SaveChanges()` 호출
- 여러 테이블/조인/조건이 있는 경우 수십 번의 DB 왕복

### 8. 약물노출도 복잡성
- 2696줄, MySQL Stored Procedure 동적 생성
- 커서 루프 + 조건 분기 + 다중 파라미터
- 런타임 SQL 구문 오류 시 디버깅 난이도 극상
