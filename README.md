# 🚀 Nasdaq is God (미국 주식 자동매매 플랫폼)

미국 주식 시장(NASDAQ, S&P 500)을 타겟으로 한 **풀스택 자동매매 및 분석 플랫폼**입니다. 시니어 퀀트 개발자의 전문 지식과 현대적인 웹 기술을 결합하여 데이터 중심의 매매 환경을 제공합니다.

## 🔗 주요 문서 바로가기
- **[시스템 실행 가이드 (RUN_GUIDE.md)](RUN_GUIDE.md)**: DB, API, 웹을 띄우는 방법과 상태 확인 명령어.
- **[프로젝트 현재 상태 (PROJECT_STATUS.md)](PROJECT_STATUS.md)**: 최신 개발 진행 상황 및 향후 계획.
- **[개발 로드맵 (ROADMAP.md)](ROADMAP.md)**: 프로젝트의 전체 비전과 단계별 마일스톤.
- **[프로젝트 규칙 (PROJECT_RULE.md)](PROJECT_RULE.md)**: 코드 컨벤션, 기술 스택, Git 배포 규칙.

## 🌟 핵심 기능
- **실시간 주가 스트리밍**: WebSocket을 통한 끊김 없는 시세 반영.
- **기술적 지표 분석**: RSI, MACD, 볼린저 밴드 실시간 계산 및 시각화.
- **Gemini AI 감성 분석**: 최신 뉴스를 AI가 분석하여 투자 심리 점수 도출.
- **잔고 기반 매매 엔진**: 초기 자본금 내에서 실시간 주가로 주문 실행 및 ROI 트래킹.
- **자동매매 전략 워커**: 24시간 백그라운드에서 지표를 감시하고 자동 주문 실행.

## 🛠 기술 스택
- **Backend**: Python 3.10+, FastAPI, SQLAlchemy, SQLModel
- **Quant Engine**: Pandas, yfinance, Gemini AI (Google)
- **Frontend**: Flutter Web (Material 3, Dark Mode)
- **Infra**: Docker (PostgreSQL 15), Multithreaded Python Web Server

## 📂 프로젝트 구조
- `core/`: 퀀트 분석, AI 서비스, 매매 로직, 워커 스케줄러.
- `bot/`: 텔레그램 핸들러 및 알림 서비스.
- `frontend/`: Flutter 웹 앱 소스 및 실행 스크립트.
- `scripts/`: DB 마이그레이션, 시스템 통합 점검, 설치 스크립트.
- `tests/`: 시스템 안정성을 위한 유닛 테스트.

## 🤝 기여 방법
작업 시작 전 반드시 **[PROJECT_RULE.md](PROJECT_RULE.md)**를 숙지하고, 커밋 전 `./scripts/check_system.sh`를 실행하여 무결성을 확인해 주세요.