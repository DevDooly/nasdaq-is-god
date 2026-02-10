# Project Status: Nasdaq is God

## 프로젝트 현재 상태 (2026-02-10 기준)

미국 주식 시장을 최우선 타겟으로 하여 로드맵이 재구성되었으며, 전략 수립을 위한 AI 페르소나 설정이 완료되었습니다.

### 1. 주요 변경 사항
- **로드맵 재구축**: 미국 주식(NASDAQ, S&P 500) 중심의 개발 계획으로 수정 (`roadmap.md`)
- **Gems 페르소나 정의**: 전략 수립을 돕는 'Expert Quant Developer' 프롬프트 작성 완료 (`GEMS_PROMPT.md`)
- **코어 로직 분리**: `core/stock_service.py`를 통해 `yfinance` 기반의 미국 주식 시세 조회 기능 안정화
- **FastAPI 도입**: 기본 API 서버(`main_api.py`) 및 엔드포인트 구축 완료

### 2. 현재 아키텍처
- `core/`: 핵심 비즈니스 로직 및 외부 API 연동 (`stock_service.py`)
- `bot/`: 텔레그램 봇 인터페이스 및 핸들러
- `main.py`: 텔레그램 봇 실행 진입점
- `main_api.py`: FastAPI 서버 실행 진입점
- `GEMS_PROMPT.md`: 전략 수립용 AI 프롬프트 가이드

### 3. 향후 계획
- 미국 주식 기술적 지표 계산 모듈 추가 (Pandas 기반)
- 매매 시그널 생성 및 텔레그램 알림 기능 고도화
- 백테스팅 환경 구축 (Backtrader 또는 VectorBT 검토)

---
**변경 이력**
- 2026-02-10: 미국 주식 우선 로드맵 수정 및 Gems 프롬프트 추가
- 2026-01-25: 비즈니스 로직 분리(`core/`) 및 FastAPI 서버 추가