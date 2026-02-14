# 📡 Real-time Guru Watch & Execution Plan (Draft)

이 문서는 시장 영향력 있는 인물의 소셜 발언을 실시간으로 포착하고, AI 분석을 거쳐 즉각적인 매매로 연결하는 'Zero-Latency' 시스템 구축을 위한 설계도입니다. 사장님(User)의 피드백에 따라 지속적으로 업데이트됩니다.

---

## 1. 시스템 목표 (Goal)
- **목표 지연 시간**: 발언 발생 후 분석 완료까지 **10초 이내**.
- **자동화 수준**: AI 점수가 극단적(Bullish 90+ 또는 Bearish 10-)일 경우 즉시 자동 매매 실행.
- **아카이브**: 모든 실시간 이벤트와 그에 따른 주가 변동을 DB화하여 백테스팅 데이터로 활용.

---

## 2. 실시간 데이터 수집 전략 (Data Ingestion)

### Option A: X(Twitter) 공식 Webhook (Account Activity API)
- **방식**: X 서버가 새 트윗 발생 시 우리 서버의 엔드포인트를 직접 호출.
- **장점**: 가장 빠르고 정확함.
- **단점**: 고가의 유료 플랜($100/mo~) 필요.

### Option B: 자동화 브릿지 활용 (추천 ⭐)
- **도구**: **Pipedream**, **Make.com**, 또는 **IFTTT**.
- **흐름**: 
    1. Third-party 서비스가 구루의 새 트윗을 모니터링.
    2. 트윗 발생 즉시 우리 서버의 `POST /gurus/webhook` 호출.
- **장점**: 개발 공수가 적고, 공식 API보다 저렴하거나 무료 범위 내 사용 가능.

### Option C: 전용 모니터링 봇 (Self-hosted)
- **도구**: `twint` (작동 여부 확인 필요) 또는 맞춤형 스크래퍼.
- **방식**: 10초 단위로 초고속 Polling 수행.
- **단점**: X의 차단(IP Ban) 위험이 높음.

---

## 3. 백엔드 처리 파이프라인 (Processing Pipeline)

1. **Webhook Listener**: 외부에서 들어오는 트윗 데이터를 수신.
2. **Fast-Filter**: 텍스트 길이가 너무 짧거나 단순 인사말 등 무의미한 내용은 AI로 보내기 전 필터링.
3. **Concurrent AI Analysis**: 
    - Gemini 2.0 Flash를 사용하여 분석 속도 극대화.
    - `impact_score`와 함께 `confidence_level` (확신도) 추출.
4. **Execution Decision**:
    - `IF (impact_score > 90 AND confidence > 0.8) THEN EXECUTE_BUY`
    - `IF (impact_score < 10 AND confidence > 0.8) THEN EXECUTE_SELL`

---

## 4. 프론트엔드 실시간 알림 (UI/UX)
- **Push Notification**: 웹/앱이 꺼져 있어도 브라우저 알림으로 즉시 분석 결과 팝업.
- **Live Impact Meter**: 발언 직후 1분/5분/10분 단위의 주가 변화를 실시간 그래프로 오버레이 표시.

---

## 5. 향후 과제 및 논의 사항 (To-do)
- [ ] 어떤 인물의 발언에 '완전 자동 매매' 권한을 줄 것인가? (예: 파월 100%, 머스크 50% 등)
- [ ] 오보(Fake News)나 해킹된 계정의 발언에 대한 방어 로직 (Cross-check 로직).
- [ ] 실시간 연동 테스트를 위한 테스트용 X 계정 생성.

---

**마지막 업데이트**: 2026-02-14
**작성자**: Senior Quant Developer (Nasdaq is God)
