# 🚀 Nasdaq is God (미국 주식 자동매매 및 백테스팅 플랫폼)

미국 주식 시장(NASDAQ, S&P 500)을 타겟으로 한 **풀스택 자동매매, 백테스팅 및 AI 분석 플랫폼**입니다. 시니어 퀀트 개발자의 전문 지식과 현대적인 웹 기술을 결합하여 데이터 중심의 하이브리드 매매 환경을 제공합니다.

## 🔗 주요 문서 바로가기
- **[시스템 실행 가이드 (RUN_GUIDE.md)](RUN_GUIDE.md)**: DB, API, 웹을 띄우는 방법과 상태 확인 명령어.
- **[프로젝트 현재 상태 (PROJECT_STATUS.md)](PROJECT_STATUS.md)**: 최신 개발 진행 상황 및 향후 계획.
- **[개발 로드맵 (ROADMAP.md)](ROADMAP.md)**: 프로젝트의 전체 비전과 단계별 마일스톤.
- **[프로젝트 규칙 (PROJECT_RULE.md)](PROJECT_RULE.md)**: 코드 컨벤션, 기술 스택, Git 배포 규칙.

## 🌟 핵심 기능
- **백테스팅 엔진 (5대 주식 매매기법)**: 과거 1년 주가 데이터 기반으로 수수료/슬리피지가 반영된 수익률, CAGR, MDD, Sharpe Ratio, Profit Factor 산출.
- **AI 뉴스 & 소셜/트위터 감성 분석**: StockTwits 실시간 소셜 트윗 + 월가 대가(Elon Musk, Cathie Wood, Warren Buffett) 소셜 데이터 + 뉴스를 Gemini/Ollama AI가 통합 분석하여 감성 점수(0~100점) 도출.
- **하이브리드 자동매매 엔진**: 기술적 지표 점수 + AI 감성 점수를 가중 조합하여 최종 매매 시그널(BUY/SELL/HOLD) 자동 발동.
- **전략 가이드북 & 시뮬레이터 UI**: Flutter 웹 대시보드에서 백테스트 시뮬레이션 실행, 하이브리드 AI 진단, 전략 설명서 및 가이드북 제공.
- **실시간 주가 스트리밍 & 알림**: WebSocket 시세 반영 및 텔레그램 알림 체계 구축.

## 🛠 기술 스택
- **Backend**: Python 3.10+, FastAPI, SQLAlchemy, SQLModel, AsyncIO
- **Quant Engine**: Pandas, yfinance, Gemini AI (Google), StockTwits API
- **Frontend**: Flutter Web (Material 3, Dark Mode, Glassmorphism UI)
- **Infra**: Docker (PostgreSQL 15), Coolify CI/CD

## 📂 프로젝트 구조
- `core/`: 퀀트 분석 (`backtest_engine.py`, `hybrid_strategy.py`), 소셜/감성 분석 (`social_service.py`, `sentiment_engine.py`), AI 서비스, 매매 로직, 워커 스케줄러.
- `bot/`: 텔레그램 핸들러 및 알림 서비스.
- `frontend/`: Flutter 웹 앱 소스 및 백테스트/가이드 화면 (`strategy_screen.dart`, `guide_screen.dart`).
- `scripts/`: DB 마이그레이션 및 시스템 통합 점검 스크립트.
- `tests/`: 시스템 안정성을 위한 유닛 테스트 (Pytest 24개 통과).

## 🤝 기여 방법
작업 시작 전 반드시 **[PROJECT_RULE.md](PROJECT_RULE.md)**를 숙지하고 컨벤션을 준수해 주세요.