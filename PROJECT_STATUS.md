# 📊 Project Status: Nasdaq is God

## 프로젝트 현재 상태 (2026-07-30 기준)

주식 백테스팅 시뮬레이션, AI 뉴스 및 트위터/StockTwits 감성 분석, 그리고 기술 지표와 AI 감성을 결합한 **하이브리드 자동매매 플랫폼** 구현을 완료했습니다.

### ✅ 최근 완료된 주요 기능 (2026-07-30)
- **백테스팅 엔진 (`core/backtest_engine.py`)**: 과거 1년 주가 데이터 기반 수수료 및 슬리피지가 반영된 5대 주요 주식 매매기법(SMA, RSI, MACD, 볼린저밴드, 모멘텀) 백테스팅 시뮬레이터 개발. 성과 지표(Total Return, CAGR, MDD, Sharpe Ratio, Profit Factor) 자동 산출.
- **뉴스/소셜/트위터 AI 감성 분석 엔진 (`core/social_service.py`, `core/sentiment_engine.py`)**: StockTwits 실시간 소셜 트윗 + 월가 대가(Elon Musk, Cathie Wood 등) 소셜 포스트 + 뉴스를 Gemini/Ollama AI가 통합 분석하여 감성 점수(0~100점) 도출 및 DB 저장.
- **하이브리드 가중 결합 자동매매 시그널 엔진 (`core/hybrid_strategy.py`)**: 기술적 지표 점수 + AI 센티먼트 점수를 가중 조합하여 BUY/SELL/HOLD 자동 판정 및 주문 연동.
- **프론트엔드 대시보드 UI & 가이드북 페이지 (`frontend/lib/screens/strategy_screen.dart`, `guide_screen.dart`)**:
  - 백테스팅 성과 시뮬레이터 및 실시간 하이브리드 AI 진단 카드 UI 구현.
  - 백테스트 검증 파라미터를 즉시 실전 자동매매 전략으로 등록/활성화하는 기능 제공.
  - 사용자용 주식 매매기법 및 하이브리드 자동매매 설명서 가이드북 구축.

### 🏗️ 현재 시스템 아키텍처
- **Backend**: Python (FastAPI) - 9095/9000 포트
- **Frontend**: Flutter Web (Material 3, Dark Mode) - 8081/80 포트
- **Engine**: BacktestEngine, HybridStrategyEngine, SentimentEngine, TradingWorker, AIService
- **Database**: PostgreSQL 15

---
**변경 이력**
- 2026-07-30: 백테스팅 엔진, AI 소셜/뉴스 센티먼트 엔진, 하이브리드 자동매매 엔진 및 전략 가이드북 UI 구축 완료
- 2026-02-14: Guru Archive 구현, 트럼프 추가, 실시간 연동 플랜 수립
- 2026-02-13: Guru Watch (소셜 센티먼트 분석) 모듈 및 UI 개발 완료
- 2026-02-11: WebSocket 실시간 시세, AI 감성 분석, 잔고 관리 및 자동 로그인 구현 완료
