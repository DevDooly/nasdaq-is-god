# 📈 주식 자동매매 시스템 개발 로드맵 (Stock Auto-Trading System)

## 1. 프로젝트 개요
- **목표:** 웹 기반 대시보드를 통한 주식 자동매매 및 AI 기반 매매 전략 수립
- **핵심 타겟:** 국내 주식 (SK하이닉스 등) 및 미국 주식 확장 고려
- **주요 기술:** Java (Spring Boot), Python (Analysis), Kafka, Jenkins, KIS Open API

## 2. 단계별 진행 계획 (Phases)

### Phase 1: 환경 설정 및 기획 (Environment & Setup)
| 상태 | 작업명 | 상세 내용 | 비고 |
| :---: | :--- | :--- | :--- |
| ⬜ | **KIS API 발급** | 한국투자증권 개발자 센터 계좌 개설 및 App Key/Secret 발급 | 실전/모의투자 구분 |
| ⬜ | **Repo 생성** | Spring Boot(Backend) 및 Python(Analysis) Git Repository 초기화 | |
| ⬜ | **Gems 구성** | 'Quant Developer' 페르소나 Gems 생성 및 프롬프트 튜닝 | 전략 수립 파트너 |
| ⬜ | **DB 설계** | 주가 데이터, 매매 로그, 사용자 정보 테이블 스키마 설계 | MySQL/MariaDB 추천 |

### Phase 2: 코어 백엔드 개발 (Core Backend - Java)
| 상태 | 작업명 | 상세 내용 | 기술 스택 |
| :---: | :--- | :--- | :--- |
| ⬜ | **API 연동** | OAuth2 토큰 자동 발급 및 갱신(Scheduler) 로직 구현 | Spring Boot |
| ⬜ | **시세 조회** | 실시간 현재가/호가 조회 API 구현 (WebSocket 고려) | KIS API |
| ⬜ | **주문 모듈** | 지정가/시장가 매수, 매도 주문 인터페이스 구현 | |
| ⬜ | **잔고 관리** | 예수금 및 보유 주식 현황 조회 기능 | |
| ⬜ | **로깅 시스템** | 매매 이력 및 시스템 에러 로깅 (Logback/SLF4J) | |

### Phase 3: 데이터 분석 및 전략 엔진 (Analysis Engine - Python)
| 상태 | 작업명 | 상세 내용 | 기술 스택 |
| :---: | :--- | :--- | :--- |
| ⬜ | **데이터 수집기** | OHLCV(시가/고가/저가/종가/거래량) 데이터 수집 및 전처리 | Pandas, yfinance |
| ⬜ | **백테스팅 환경** | Gems가 제안한 전략(변동성 돌파 등) 과거 데이터 검증 | Backtrader |
| ⬜ | **AI 분석 (Optional)** | 뉴스/Reddit(SK Hynix 관련) 감성 분석 모델 연동 | FinBERT, LangChain |
| ⬜ | **시그널 생성** | 매수/매도 시그널 생성 후 메시지 큐(Kafka)로 전송 | Python Producer |

### Phase 4: 인프라 및 통합 (Infrastructure & Integration)
| 상태 | 작업명 | 상세 내용 | 기술 스택 |
| :---: | :--- | :--- | :--- |
| ⬜ | **Kafka 구축** | Python(Producer) -> Java(Consumer) 간 데이터 파이프라인 구축 | Apache Kafka |
| ⬜ | **DB 연동** | 매매 시그널 및 주문 체결 내역 DB 영구 저장 | JPA / Hibernate |
| ⬜ | **도커라이징** | 각 서비스(Backend, Analysis, Kafka, DB) Docker Compose 구성 | Docker |

### Phase 5: 웹 대시보드 (Web Frontend)
| 상태 | 작업명 | 상세 내용 | 기술 스택 |
| :---: | :--- | :--- | :--- |
| ⬜ | **UI 레이아웃** | 대시보드 기본 레이아웃 구성 (사이드바, 헤더 등) | React or Thymeleaf |
| ⬜ | **차트 시각화** | 주가 차트 및 매매 시점 표시 (TradingView Chart 라이브러리 등) | Chart.js / ApexCharts |
| ⬜ | **제어 패널** | 봇 시작/중지 스위치, 수동 매수/매도 버튼 연동 | |
| ⬜ | **로그 뷰어** | 실시간 시스템 로그 및 매매 체결 내역 화면 표시 | |

### Phase 6: 운영 및 배포 (DevOps)
| 상태 | 작업명 | 상세 내용 | 기술 스택 |
| :---: | :--- | :--- | :--- |
| ⬜ | **CI/CD 파이프라인** | Git Push 시 자동 빌드 및 테스트, 배포 설정 | Jenkins |
| ⬜ | **모니터링** | 서버 상태 및 리소스 사용량 모니터링 대시보드 (Optional) | Prometheus/Grafana |
| ⬜ | **알림 시스템** | 매매 체결 시 Slack/Telegram 알림 전송 | Webhook |

---

## 3. Backlog (아이디어 저장소)
- [ ] Reddit 'WSB' 또는 'Stock' 서브레딧 트렌드 분석 기능 추가
- [ ] SK하이닉스 외 관심 종목(엔비디아 등) 자동 발굴 스크리너 개발
- [ ] 수익률 리포트 일간/주간 자동 생성 및 메일 발송

