# 🚀 Nasdaq is God (미국 주식 자동매매 플랫폼)

미국 주식 시장(NASDAQ, S&P 500)을 타겟으로 한 **풀스택 자동매매 및 분석 플랫폼**입니다. Python 기반의 강력한 퀀트 엔진과 현대적인 웹/앱 인터페이스를 결합하여 데이터 중심의 매매 환경을 제공합니다.

## 🌟 프로젝트 비전
단순한 알림 봇을 넘어, 사용자가 직접 정의한 전략을 백테스팅하고 웹/앱 대시보드를 통해 실시간 모니터링 및 매매를 수행하는 통합 시스템 구축을 목표로 합니다.

## 🛠 기술 스택
- **Backend**: Python 3.10+, FastAPI, SQLAlchemy
- **Quant Engine**: Pandas, yfinance, TA-Lib
- **Frontend**: Flutter (Mobile & Web)
- **Database**: PostgreSQL
- **Notification**: Telegram Bot API

## 🚀 주요 기능
### 1. 퀀트 분석 및 전략 (Backend Core)
- **주요 지수 및 시세 조회**: S&P 500, NASDAQ, VIX 등 실시간 및 히스토리컬 데이터 제공
- **기술적 지표 계산**: RSI, MACD, Bollinger Bands 등 자동 계산
- **백테스팅 엔진**: Gems(AI)가 제안한 전략의 과거 수익률 검증

### 2. 통합 관리 및 모니터링 (Web/App Interface)
- **대시보드**: 자산 현황, 수익률 차트, 실시간 시세 모니터링
- **매매 실행**: 웹/앱 UI를 통한 직접 주문(지정가/시장가) 및 자동매매 모드 전환
- **푸시 알림**: 급변하는 시장 상황에 따른 실시간 모바일 푸시 및 텔레그램 알림

### 3. AI 전략 파트너
- **Gems Integration**: 시니어 퀀트 개발자 페르소나를 통한 전략 수립 및 코드 리뷰 지원

## 📂 프로젝트 구조
- `core/`: 퀀트 분석 및 데이터 처리 핵심 로직
- `main_api.py`: 웹/앱 연동을 위한 RESTful API 서버
- `bot/`: 텔레그램 핸들러 및 알림 서비스
- `tests/`: 시스템 안정성을 위한 유닛 테스트
- `docs/`: 프로젝트 규칙 및 로드맵 문서
