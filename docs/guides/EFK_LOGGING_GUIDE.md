# 📊 Nasdaq is God - EFK 로깅 및 모니터링 연동 가이드

이 문서는 `nasdaq-is-god` 서비스에서 발생하는 모든 로그(DB 접속 성공/실패, API 요청/응답, 봇 동작 및 예외 Traceback)를 중앙 **EFK(Elasticsearch + Fluent Bit + Kibana)** 스택과 연동하여 감시하는 가이드입니다.

---

## 1. 🔍 EFK 중앙 모니터링 구조

```text
[nasdaq-is-god 서비스]
 ├── 백엔드 API (FastAPI) ───(JSON 로그)───┐
 ├── 프론트엔드 Web (Nginx) ──(Access 로그)─┼─> [Fluent Bit] ─> [Elasticsearch] ─> [Kibana (Port 5601)]
 └── PostgreSQL DB & 봇 ───────────────────┘
```

백엔드에는 **JSON 구조화 로거(JSONFormatter)**가 적용되어 수집기에 전달될 때 아래와 같은 필드로 자동 분헤되어 Elasticsearch에 보관됩니다:
- `@timestamp`: 로그 발생 시각
- `level`: INFO, WARNING, ERROR
- `service`: `nasdaq-backend`
- `message`: HTTP 요청/응답 경로, 소요시간(ms) 및 예외 에러 메시지

---

## 2. 🖥️ Kibana에서 로그 확인하는 3단계

1. 브라우저에서 **Kibana 대시보드** (`http://192.168.0.2:5601`) 접속
2. 좌측 메뉴 **`Discover`** 탭 클릭
3. 검색창에 쿼리 입력하여 필요한 로그만 필터링:
   - **백엔드 모든 로그 보기**: `service: "nasdaq-backend"`
   - **에러 로그만 필터링**: `level: "ERROR"`
   - **DB 관련 로그만 보기**: `message: *Database*`

---

## 3. 🚀 Mini PC 구동 순서

가장 먼저 `ai-ops-hub`의 EFK 로깅 인프라를 실행한 후 `nasdaq-is-god` 서비스를 실행하는 것을 권장합니다:

```bash
# 1. EFK 로깅 인프라 구동 (최우선)
cd /d/dev/repository/ai-playground/ai-ops-hub
docker compose -f docker-compose.logging.yml up -d

# 2. nasdaq-is-god 서비스 구동
cd /d/dev/repository/nasdaq-is-god
docker compose -f docker-compose.coolify.yml up -d --build
```
