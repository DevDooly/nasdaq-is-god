# 🚀 Nasdaq is God - Coolify 배포 & DB 초기화 및 상세 로깅 가이드

이 문서는 `nasdaq-is-god` 프로젝트를 Coolify(Mini PC) 상에서 원클릭으로 켜고 끄며, DB 초기화 및 시스템의 상세 실시간 동작 로그를 확인하는 방법을 안내합니다.

---

## 1. 🔍 상세 실시간 라이브 로그 확인 방법 (Logging & Diagnostics)

서비스 내부의 동작 원인 분석, 예외 발생 원인, HTTP 요청/응답 경로를 확인하려면 아래 3가지 방법 중 편하신 방법으로 로그를 실시간 조회하실 수 있습니다.

### 방법 A: 웹 API를 통한 라이브 로그 조회 (가장 간편함)
브라우저에서 아래 주소로 접속하시면 백엔드의 최근 라이브 동작 및 HTTP 요청/응답 로그 100줄을 JSON으로 즉시 확인하실 수 있습니다:
```text
http://<MINI_PC_IP>:9095/system/logs
```

### 방법 B: Coolify 웹 대시보드 `Logs` 탭 활용
1. Coolify 웹 대시보드 (`http://192.168.0.2:8000`) 접속
2. `Projects` -> `nasdaqisgod` 선택
3. `backend` (또는 `frontend`, `db`, `bot`) 컨테이너 선택
4. 상단 **`Logs`** 탭 클릭 시 실시간 콘솔 로그 스트림 확인 가능

---

## 2. DB 초기화 방법 (처음부터 다시 시작하기)

### 방법 A: Coolify 환경변수로 1회성 자동 초기화
Coolify의 프로젝트 **Environment Variables** 탭에 아래 환경변수를 추가하고 **Deploy**합니다:
```env
RESET_DB=true
```
- 백엔드 컨테이너가 시작될 때 기존 데이터베이스의 모든 테이블을 삭제(`DROP TABLE`)하고 새로 깨끗하게 생성합니다.
- 초기화 후에는 `RESET_DB=false`로 다시 변경하시면 데이터가 지속해서 저장됩니다.

### 방법 B: 로컬에서 1회성 스크립트 실행
로컬 터미널에서 아래 스크립트를 실행하여 데이터베이스를 즉시 리셋할 수 있습니다:
```bash
python reset_db.py
```

---

## 3. Coolify에서 프로젝트 등록 및 On/Off 제어 방법

### 1단계: Coolify에 Docker Compose 스택 추가
1. Coolify 웹 대시보드 접속
2. **Projects** -> **Default** -> **Production**
3. **`+ Add Resource`** 클릭 -> **`Docker Compose`** 선택
4. GitHub 연동 후 `nasdaq-is-god` 레포지토리 선택
5. **Docker Compose Location**: `docker-compose.coolify.yml` 입력 후 Save

### 2단계: 포트 노출 설정 (Ports Expose)
* **`frontend`** 컨테이너 -> `Ports Expose`: `8081:80` 입력
* **`backend`** 컨테이너 -> `Ports Expose`: `9095:9000` 입력

---

## 4. 접속 포트 안내

- **Backend API (FastAPI)**: `http://<MINI_PC_IP>:9095`
- **라이브 로그 API**: `http://<MINI_PC_IP>:9095/system/logs`
- **Swagger API Docs**: `http://<MINI_PC_IP>:9095/docs`
- **Frontend Web**: `http://<MINI_PC_IP>:8081`


