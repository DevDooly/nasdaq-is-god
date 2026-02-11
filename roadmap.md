# 📈 주식 자동매매 시스템 개발 로드맵 (Nasdaq is God)

## 1. 프로젝트 개요
- **목표:** 웹 기반 대시보드를 통한 주식 자동매매 및 AI 기반 매매 전략 수립
- **핵심 타겟:** 미국 주식 (NASDAQ, S&P 500 등) 우선 개발 후 국내 주식 확장
- **주요 기술:** Python (FastAPI, yfinance), Kafka (Optional), Docker, Gemini AI (Gems)

## 2. 단계별 진행 계획 (Phases)

### Phase 1: 환경 설정 및 기획 (Environment & Setup)
| 상태 | 작업명 | 상세 내용 | 비고 |
| :---: | :--- | :--- | :--- |
| ✅ | **Repo 구성** | FastAPI(Backend) 및 yfinance 연동 기본 구조 완료 | |
| ⬜ | **Gems 구성** | 'Expert Quant Developer' 페르소나 Gems 생성 및 프롬프트 튜닝 | 전략 수립 파트너 |
| ⬜ | **DB 설계** | 사용자 정보, 매매 이력, 전략 파라미터 테이블 설계 | PostgreSQL |
| ⬜ | **API 키 관리** | Telegram Bot, Gemini API, 주식 API(KIS/Polygon 등) 설정 | `.env` 보안 |

### Phase 2: 코어 백엔드 및 DB 구축 (Core Backend & DB)
| 상태 | 작업명 | 상세 내용 | 기술 스택 |
| :---: | :--- | :--- | :--- |
| ✅ | **시세 조회** | yfinance 기반 실시간/과거 시세 조회 로직 구현 | core/stock_service.py |
| ✅ | **API 서버** | FastAPI 기반 주식 정보 제공 엔드포인트 구축 | main_api.py |
| ⬜ | **DB 연동** | SQLAlchemy/SQLModel을 이용한 PostgreSQL 연동 | Python |
| ⬜ | **주문 모듈** | 미국 주식 소수점 매매 및 지정가/시장가 주문 로직 | KIS / Alpaca |
| ⬜ | **인증 시스템** | 웹/앱 사용자를 위한 JWT 기반 로그인 및 토큰 관리 | OAuth2 |

### Phase 3: 데이터 분석 및 전략 엔진 (Analysis Engine)
| 상태 | 작업명 | 상세 내용 | 기술 스택 |
| :---: | :--- | :--- | :--- |
| ⬜ | **기술적 지표** | RSI, MACD, 이동평균선 등 주요 지표 자동 계산 모듈 | Pandas, TA-Lib |
| ⬜ | **백테스팅** | Gems가 제안한 전략(Momentum, Mean Reversion 등) 검증 | Backtrader / VectorBT |
| ⬜ | **AI 감성 분석** | Reddit, Yahoo Finance 뉴스 등 미국 시장 센티먼트 분석 | Gemini API |
| ⬜ | **시그널 생성** | 매수/매도 시그널 생성 및 알림(Push/Telegram) 연동 | |

### Phase 4: 웹/앱 프론트엔드 개발 (UI/UX)
| 상태 | 작업명 | 상세 내용 | 기술 스택 |
| :---: | :--- | :--- | :--- |
| ⬜ | **앱 아키텍처** | 크로스 플랫폼(Web/App) 대응을 위한 UI 설계 | Flutter |
| ⬜ | **대시보드** | 자산 현황, 보유 종목, 실시간 수익률 모니터링 화면 | UI |
| ⬜ | **차트 시각화** | 실시간 캔들 차트 및 전략적 타점 표시 | Lightweight Charts |
| ⬜ | **매매 인터페이스** | 앱에서 직접 주문을 넣고 취소할 수 있는 트레이딩 뷰 | UI |

### Phase 5: 인프라 및 배포 (Infra & Deployment)
| 상태 | 작업명 | 상세 내용 | 기술 스택 |
| :---: | :--- | :--- | :--- |
| ⬜ | **도커라이징** | FastAPI, DB, Redis 등 서비스 컨테이너화 | Docker Compose |
| ⬜ | **배포** | 클라우드 인스턴스(AWS/GCP) 배포 및 CI/CD 구축 | GitHub Actions |
| ⬜ | **보안 강화** | SSL 설정 및 API Rate Limiting 적용 | Nginx / Cloudflare |

---

## 3. Backlog (아이디어 저장소)
- [ ] Reddit 'WallStreetBets' 실시간 트렌드 티커 추출
- [ ] 고배당 미국 주식 자동 재투자 로직 추가
- [ ] 국내 주식 (한국투자증권 API) 연동 및 통합 관리 기능
- [ ] AI 기반 포트폴리오 최적화 제안 기능

