# 🚀 Project Rules: nasdaq-is-god

### 1. 작업 시작 전 필수 절차
- **Update First**: 모든 AI 작업 및 코드 수정 전에는 반드시 `git pull` 또는 현재 상태를 최신화한다.
- **Context Sync**: AI에게 작업을 요청할 때 `PROJECT_STATUS.md`를 먼저 읽게 하여 현재 진행 단계를 인지시킨다.

### 2. 기술 스택 및 아키텍처
- **Core**: `yfinance` 기반 비즈니스 로직은 `bot/`에서 분리하여 `core/` 라이브러리화한다.
- **Async First**: 모든 I/O 작업(API 호출, DB)은 `async/await`를 사용한다.
- **Security**: API 토큰, DB 접속 정보 등은 절대 코드에 노출하지 않으며 `.env` 파일로 관리한다.

### 3. 코드 컨벤션
- 모든 함수와 클래스에는 한국어 Docstring을 작성한다.
- 새로운 기능 추가 시 `tests/` 폴더 내에 유닛 테스트를 반드시 포함한다.

### 4. Git 및 배포
- `main` 브랜치는 항상 배포 가능한 상태를 유지한다.
- Docker 환경에서 동작 가능하도록 의존성(`requirements.txt`)을 엄격히 관리한다.
