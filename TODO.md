# 📋 Nasdaq is God 작업 리스트

## 🚀 High Priority (프론트엔드 시각화 및 자동매매)
- [ ] **대시보드 UI 구현**: 앱에서 실시간 잔고, 보유 자산, 총 수익률 표시
- [ ] **지표 차트 시각화**: `fl_chart`를 이용하여 RSI, MACD 등을 앱에서 그래프로 표시
- [ ] **자동매매 스케줄러**: 정해진 주기에 따라 지표를 체크하고 `KISBroker`를 통해 자동 주문 실행
- [ ] **실시간 데이터 스트리밍**: WebSocket을 통한 실시간 시세 및 체결 알림

## ✅ Completed (실전 매매 및 백엔드 엔진)
- [x] **실제 브로커 연동**: 한국투자증권(KIS) API 연동 (`core/kis_broker.py`) 완료
- [x] **브로커 스위칭**: Mock <-> Real 브로커 간 전환 기능 추가
- [x] **기술적 지표 모듈**: `core/indicator_service.py` (RSI, MACD, BB) 완료
- [x] **분석 API 추가**: `/stock/{symbol}/indicators` 엔드포인트 완료
- [x] **인증 및 DB 구축**: JWT 로그인 시스템 및 PostgreSQL 연동 완료

## 📈 Analysis & Strategy
- [ ] **백테스팅 파이프라인**: 과거 데이터를 이용한 전략 검증 로직 기초 설계
- [ ] **Gemini 연동**: 시장 데이터 요약 및 전략 제안을 위한 AI 핸들러 개발
- [ ] **거래소별 세부 처리**: 프리마켓/애프터마켓 주문 처리 로직 고도화
