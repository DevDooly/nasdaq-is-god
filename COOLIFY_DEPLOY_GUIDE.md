# 🚀 Nasdaq is God - Coolify 배포 & DB 초기화 가이드

이 문서는 `nasdaq-is-god` 프로젝트를 Coolify(Mini PC) 상에서 원클릭으로 켜고 끄며, 필요 시 DB를 처음부터 새로 초기화하는 방법을 안내합니다.

---

## 1. DB 초기화 방법 (새로 시작하기)

### 방법 A: Coolify 환경변수로 최초 1회 자동 초기화 (추천)
Coolify의 프로젝트 **Environment Variables** 탭에 아래 환경변수를 추가하고 **Deploy**합니다.
```env
RESET_DB=true
```
- 백엔드 컨테이너가 시작될 때 기존 데이터베이스의 모든 테이블을 삭제(`DROP TABLE`)하고 새로 깨끗하게 생성합니다.
- 초기화 후에는 `RESET_DB=false`로 다시 변경하시면 데이터가 지속해서 저장됩니다.

### 방법 B: 로컬에서 1회성 스크립트 실행
로컬 터미널에서 아래 스크립트를 실행하여 데이터베이스를 즉시 리셋할 수 있습니다.
```bash
python reset_db.py
```

---

## 2. Coolify에서 프로젝트 등록 및 On/Off 제어 방법

### 1단계: Coolify에 Docker Compose 스택 추가
1. Coolify 웹 대시보드 (`http://1.231.114.132:8000`) 접속
2. **Projects** -> **Default** (또는 새 프로젝트 생성) -> **Production**
3. **`+ New`** 또는 **`+ Add Resource`** 클릭 -> **`Docker Compose`** 선택
4. GitHub 연동 후 `nasdaq-is-god` 레포지토리 선택
5. **Docker Compose Location**: `docker-compose.coolify.yml` 입력 후 Save

### 2단계: 필수 환경변수 설정
Coolify 프로젝트 설정의 **Environment Variables**에 입력:
```env
DB_USER=postgres
DB_PASSWORD=password
DB_NAME=nasdaq_god
RESET_DB=false
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
GEMINI_API_KEY=your_gemini_api_key_here
```

### 3단계: 원클릭 On / Off (켜고 끄기)
- **Start / Deploy**: 대시보드 상단의 **`Deploy`** 또는 **`Start`** 버튼을 누르면 `PostgreSQL DB + Backend API + Frontend Web + Telegram Bot`이 한꺼번에 온(On) 기동됩니다.
- **Stop**: **`Stop`** 버튼 클릭 시 전 서비스가 깔끔하게 종료됩니다.
- **Restart**: **`Restart`** 버튼 하나로 모든 컨테이너가 재부팅됩니다.

---

## 3. 포트 안내

- **Backend API (FastAPI)**: `http://<MINI_PC_IP>:9000` (Swagger UI: `http://<MINI_PC_IP>:9000/docs`)
- **Frontend Web**: `http://<MINI_PC_IP>:8080`
