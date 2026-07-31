# 🚀 Project Rules: nasdaq-is-god

### 1. 작업 시작 전 필수 절차
- **Update First**: 모든 AI 작업 및 코드 수정 전에는 반드시 `git pull` 또는 현재 상태를 최신화한다.
- **Context Sync**: AI에게 작업을 요청할 때 `PROJECT_STATUS.md`를 먼저 읽게 하여 현재 진행 단계를 인지시킨다.

### 2. 자율 작업 및 승인 규칙 (Autonomous Execution)
- **파일 I/O 자동화**: 파일 생성, 수정, 읽기 등의 작업 시 사용자에게 일일이 확인을 묻지 않고 자율적·연속적으로 작업을 진행한다.
- **자동 커밋 및 푸시 (Auto Commit & Push)**: 기능 작성 및 유닛 테스트 통과 후, 로컬 커밋 및 원격 저장소 푸시(`git push origin <branch>`)를 자동 진행한다.
- **자동 도커 재배포 및 시스템 점검**: 코드 변경 완료 시 항상 `./scripts/check_system.sh`로 무결성을 점검하고, 도커 기반 재배포(`docker compose -f docker-compose.coolify.yml up -d --build --force-recreate`) 및 헬스 체크를 수행하여 이상 유무를 항상 확인한다.

### 3. 기술 스택 및 아키텍처
- **Backend**: Python(FastAPI)을 기반으로 하며, `yfinance` 및 `pandas`를 이용한 퀀트 및 멀티 에이전트 로직은 `core/`에 위치시킨다.
- **Database**: PostgreSQL을 기본 DB로 사용하며, 모든 스키마 변경은 마이그레이션 도구(Alembic 등)를 고려한다.
- **Frontend**: API-first 디자인을 준수하며, 웹/앱에서 호출 가능하도록 RESTful 규약을 따른다.
- **Async First**: 모든 I/O 작업(API 호출, DB)은 `async/await`를 사용한다.
- **Security**: API 토큰, DB 접속 정보 등은 절대 코드에 노출하지 않으며 `.env` 파일로 관리한다. CORS 설정 시 허용된 도메인만 접근 가능하도록 제한한다.

### 4. API 및 데이터 관리
- **Documentation**: 모든 API 엔드포인트는 FastAPI의 자동 Swagger 문서(`/docs`)를 통해 명세가 관리되어야 한다.
- **Data Validation**: Pydantic 모델을 사용하여 입출력 데이터의 유효성을 엄격히 검증한다.
- **Error Handling**: 전역 예외 처리기(Global Exception Handler)를 통해 일관된 에러 응답 포맷을 유지한다.

### 5. 코드 컨벤션
- 모든 함수와 클래스에는 한국어 Docstring을 작성한다.
- 새로운 기능 추가 시 `tests/` 폴더 내에 유닛 테스트를 반드시 포함한다.

### 6. Git, Docker 및 자동 배포 절차
- **Integrity Check**: 모든 코드 수정 완료 및 커밋 전에는 반드시 `./scripts/check_system.sh`를 실행하여 시스템의 무결성을 점검한다.
- **Frontend Build Sync**: 프론트엔드 코드 수정 시 반드시 `flutter build web`을 미리 수행하여 정적 웹 빌드를 갱신한다.
- **Docker Auto Re-deployment**: 코드 변경 검증 후 `docker compose -f docker-compose.coolify.yml up -d --build --force-recreate`로 도커 이미지를 재빌드하고 강제 재기동하여 자동 배포 및 동작을 점검한다.
- `main` 및 `dev` 브랜치는 항상 배포 가능하고 정상 동작하는 상태를 유지한다.
- Docker 환경에서 동작 가능하도록 의존성(`requirements.txt`)을 엄격히 관리한다.
