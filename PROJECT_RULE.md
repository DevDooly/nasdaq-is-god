# 🚀 Project Rules: nasdaq-is-god

### 1. 작업 시작 전 필수 절차
- **Update First**: 모든 AI 작업 및 코드 수정 전에는 반드시 `git pull origin main`으로 현재 상태를 최신화한다.
- **Context Sync**: AI에게 작업을 요청할 때 `PROJECT_STATUS.md`를 먼저 읽게 하여 현재 진행 단계를 인지시킨다.

### 2. 단일 브랜치 중심 자율 작업 및 승인 규칙 (Main Branch Autonomous Execution)
- **단일 브랜치 지침 (Main Only)**: 모든 작업, 개발, 테스트 및 배포는 단일 기본 브랜치인 `main`에서 직접 진행한다. (`dev` 브랜치는 사용하지 않는다)
- **파일 I/O 자동화**: 파일 생성, 수정, 읽기 등의 작업 시 사용자에게 일일이 확인을 묻지 않고 자율적·연속적으로 작업을 진행한다.
- **자동 커밋 및 메인 푸시 (Auto Commit & Push to Main)**: 기능 작성 및 유닛 테스트 통과 후, 로컬 커밋 및 `main` 원격 저장소 푸시(`git push origin main`)를 자동 진행한다.
- **자동 도커 재배포 및 시스템 점검**: 코드 변경 완료 시 항상 `./scripts/check_system.sh`로 무결성을 점검하고, 도커 기반 재배포(`docker compose -f docker-compose.coolify.yml up -d --build --force-recreate`) 및 헬스 체크를 수행하여 이상 유무를 항상 확인한다.

### 3. 디렉터리 구조 및 폴더 관리 수칙 (Directory Structure & Code Organization Rules)
프로젝트 디렉터리는 목적에 따라 엄격히 분리 및 정돈된 상태를 유지해야 한다.

```text
nasdaq-is-god/
├── core/                       # 퀀트 지표, 비동기 서비스, 멀티 에이전트, DB 모델 및 스케줄러
├── bot/                        # 텔레그램 봇 및 핸들러 모듈
├── frontend/                   # Flutter Web 프론트엔드 소스코드
├── tests/                      # Pytest 유닛 및 통합 테스트 수트
├── docs/                       # 프로젝트 문서 및 매뉴얼
│   ├── deployment/             # Deploy & Coolify 관련 배포 가이드
│   ├── guides/                 # 운영, 가이드 및 EFK 로깅 문서
│   └── ROADMAP.md              # 프로젝트 로드맵
├── scripts/                    # 프로젝트 실행 및 유틸리티 스크립트 모음
│   ├── check_system.sh         # 시스템 무결성 점검 스크립트
│   ├── update_recent_changes.py# Recent Changes 갱신 스크립트
│   ├── validate_pages.py       # 페이지 유효성 검증 스크립트
│   ├── simulations/            # AI 멀티 에이전트 시뮬레이션 및 백테스트 스크립트
│   ├── telegram/               # 텔레그램 디버깅 및 ID 수집 유틸 스크립트
│   └── tools/                  # DB 초기화 및 매매 실행 스크립트
├── logs/                       # 시스템 실행 로그 모음 (.gitignore 대상)
├── main_api.py                 # FastAPI 백엔드 메인 엔트리포인트
├── main.py                     # 트레이딩 바이크/엔진 엔트리포인트
├── Dockerfile.backend          # 백엔드 도커 컨테이너 정의
├── Dockerfile.frontend         # 프론트엔드 도커 컨테이너 정의
├── Dockerfile.bot              # 텔레그램 봇 도커 컨테이너 정의
├── docker-compose.coolify.yml  # 프로덕션 도커 컴포즈 셋업
├── docker-compose.yml          # 개발 도커 컴포즈 셋업
├── requirements.txt            # 파이썬 종속성 패키지 정의
├── pytest.ini                  # Pytest 실행 환경 설정
├── PROJECT_RULE.md             # 프로젝트 규칙 및 수칙 문서
├── PROJECT_STATUS.md           # 프로젝트 진행 상황 문서
└── README.md                   # 프로젝트 메인 안내 문서
```

- **루트 디렉터리 청결 유지**: 루트에는 메인 실행 파일(`main_api.py`, `main.py`), 도커 설정, 필수 프로젝트 제어문서만 배치하며, 단발성 임시 파일이나 임의의 로그 파일(.log)을 방치하지 않는다.
- **스크립트 생성 위치 지침**: 유틸리티, 시뮬레이션, 디버깅 목적의 새로운 파이썬 스크립트 작성 시 반드시 `scripts/` 하위 적절한 디렉터리(`scripts/simulations/`, `scripts/telegram/`, `scripts/tools/`)에 추가한다.
- **로그 저장 위치**: 시스템 실행 중 생성되는 로그 파일은 `logs/` 디렉터리에 모아서 기록하며, `.gitignore`에 등록하여 형상 관리에 포함되지 않도록 유지한다.

### 4. 기술 스택 및 아키텍처
- **Backend**: Python(FastAPI)을 기반으로 하며, `yfinance` 및 `pandas`를 이용한 퀀트 및 멀티 에이전트 로직은 `core/`에 위치시킨다.
- **Database**: PostgreSQL을 기본 DB로 사용하며, 모든 스키마 변경은 마이그레이션 도구(Alembic 등)를 고려한다.
- **Frontend**: API-first 디자인을 준수하며, 웹/앱에서 호출 가능하도록 RESTful 규약을 따른다.
- **Async First**: 모든 I/O 작업(API 호출, DB)은 `async/await`를 사용한다.
- **Security**: API 토큰, DB 접속 정보 등은 절대 코드에 노출하지 않으며 `.env` 파일로 관리한다. CORS 설정 시 허용된 도메인만 접근 가능하도록 제한한다.

### 5. API 및 데이터 관리
- **Documentation**: 모든 API 엔드포인트는 FastAPI의 자동 Swagger 문서(`/docs`)를 통해 명세가 관리되어야 한다.
- **Data Validation**: Pydantic 모델을 사용하여 입출력 데이터의 유효성을 엄격히 검증한다.
- **Error Handling**: 전역 예외 처리기(Global Exception Handler)를 통해 일관된 에러 응답 포맷을 유지한다.

### 6. 코드 컨벤션
- 모든 함수와 클래스에는 한국어 Docstring을 작성한다.
- 새로운 기능 추가 시 `tests/` 폴더 내에 유닛 테스트를 반드시 포함한다.

### 7. Git, Docker 및 자동 배포 절차
- **Integrity Check**: 모든 코드 수정 완료 및 커밋 전에는 반드시 `./scripts/check_system.sh`를 실행하여 시스템의 무결성을 점검한다.
- **Frontend Build Sync**: 프론트엔드 코드 수정 시 반드시 `flutter build web`을 미리 수행하여 정적 웹 빌드를 갱신한다.
- **Docker Auto Re-deployment**: 코드 변경 검증 후 `docker compose -f docker-compose.coolify.yml up -d --build --force-recreate`로 도커 이미지를 재빌드하고 강제 재기동하여 자동 배포 및 동작을 점검한다.
- `main` 브랜치는 항상 배포 가능하고 실서버에 적용 준비가 완료된 깨끗한 상태를 유지한다.
- Docker 환경에서 동작 가능하도록 의존성(`requirements.txt`)을 엄격히 관리한다.
