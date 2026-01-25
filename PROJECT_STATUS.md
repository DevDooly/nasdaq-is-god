# Project Status: Nasdaq is God

## 프로젝트 현재 상태 (2026-01-25 기준)

주요 로직의 분리 및 확장성 확보를 위한 리팩토링과 API 서버 기본 설정이 완료되었습니다.

### 1. 주요 변경 사항
- **코어 로직 분리**: `bot/finance_api.py`를 `core/stock_service.py`로 이동 및 리팩토링하였습니다.
- **FastAPI 도입**: `core/stock_service.py`를 활용하는 FastAPI 기반의 API 서버(`main_api.py`)를 추가하였습니다.
- **종속성 업데이트**: `fastapi`, `uvicorn`이 `requirements.txt`에 추가되었습니다.

### 2. 현재 아키텍처
- `core/`: 핵심 비즈니스 로직 및 외부 API 연동 (`stock_service.py`)
- `bot/`: 텔레그램 봇 인터페이스 및 핸들러
- `main.py`: 텔레그램 봇 실행 진입점
- `main_api.py`: FastAPI 서버 실행 진입점

### 3. 향후 계획
- FastAPI 엔드포인트 확장 (차트 데이터 제공 등)
- 텔레그램 봇과 API 서버의 공통 설정 관리 체계 개선
- 자동화 테스트 코드 추가

---
**변경 이력**
- 2026-01-25: 비즈니스 로직 분리(`core/`) 및 FastAPI 서버 추가