# 🚀 Project Rules: nasdaq-is-god

### 1. 작업 시작 전 필수 절차
- **Update First**: 모든 AI 작업 및 코드 수정 전에는 반드시 `git pull` 또는 현재 상태를 최신화한다.
- **Context Sync**: AI에게 작업을 요청할 때 `PROJECT_STATUS.md`를 먼저 읽게 하여 현재 진행 단계를 인지시킨다.

### 2. 기술 스택 및 아키텍처
- **Backend**: Python(FastAPI)을 기반으로 하며, `yfinance` 및 `pandas`를 이용한 퀀트 로직은 `core/`에 위치시킨다.
- **Database**: PostgreSQL을 기본 DB로 사용하며, 모든 스키마 변경은 마이그레이션 도구(Alembic 등)를 고려한다.
- **Frontend**: API-first 디자인을 준수하며, 웹/앱에서 호출 가능하도록 RESTful 규약을 따른다.
- **Async First**: 모든 I/O 작업(API 호출, DB)은 `async/await`를 사용한다.
- **Security**: API 토큰, DB 접속 정보 등은 절대 코드에 노출하지 않으며 `.env` 파일로 관리한다. CORS 설정 시 허용된 도메인만 접근 가능하도록 제한한다.

### 3. API 및 데이터 관리
- **Documentation**: 모든 API 엔드포인트는 FastAPI의 자동 Swagger 문서(`/docs`)를 통해 명세가 관리되어야 한다.
- **Data Validation**: Pydantic 모델을 사용하여 입출력 데이터의 유효성을 엄격히 검증한다.
- **Error Handling**: 전역 예외 처리기(Global Exception Handler)를 통해 일관된 에러 응답 포맷을 유지한다.

### 4. 코드 컨벤션
- 모든 함수와 클래스에는 한국어 Docstring을 작성한다.
- 새로운 기능 추가 시 `tests/` 폴더 내에 유닛 테스트를 반드시 포함한다.

### 5. Git 및 배포
- **Integrity Check**: 모든 코드 수정 완료 및 커밋 전에는 반드시 `./scripts/check_system.sh`를 실행하여 시스템의 무결성을 점검한다.
- `main` 브랜치는 항상 배포 가능한 상태를 유지한다.
- Docker 환경에서 동작 가능하도록 의존성(`requirements.txt`)을 엄격히 관리한다.
