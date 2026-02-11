# 🚀 Nasdaq is God 실행 가이드 및 상태 확인

이 문서는 프로젝트의 전체 시스템(DB, Backend API, Frontend Web, Bot)을 구동하고 관리하는 방법을 설명합니다.

## 1. 전제 조건 (Prerequisites)
- **Docker & Docker Compose V2**: 데이터베이스 실행용
- **Python 3.10+**: 백엔드 및 봇 실행용
- **Flutter SDK**: 프론트엔드 실행용
- **.env 파일**: 모든 API 키 및 설정 포함 (이미 생성됨)

## 2. 시스템 구동 순서

### Step 1: 데이터베이스 실행 (Docker)
백엔드 서버가 DB에 연결되어야 하므로 가장 먼저 실행합니다.
```bash
docker compose up -d
```

### Step 2: 백엔드 API 서버 실행 (FastAPI)
```bash
# 의존성 설치 (최초 1회)
pip install -r requirements.txt

# 서버 실행
python3 main_api.py
```
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs) 접속 가능

### Step 3: 프론트엔드 웹 실행 (Flutter)
```bash
cd frontend
flutter run -d chrome
```

### Step 4: 텔레그램 봇 실행 (Optional)
```bash
python3 main.py
```

## 3. 상태 확인 명령어 (Status Check)

### DB 상태 확인
```bash
docker compose ps
```

### 프로세스 구동 확인 (Linux/Mac)
```bash
# 백엔드 서버 확인
ps aux | grep main_api.py | grep -v grep

# 텔레그램 봇 확인
ps aux | grep main.py | grep -v grep
```

### 포트 점유 확인
```bash
# 8000 포트 (FastAPI)
netstat -tulpn | grep 8000
```

## 4. 트러블슈팅
- **DB 연결 실패**: `.env`의 `DATABASE_URL`이 `localhost:5432`인지 확인하세요.
- **포트 충돌**: 8000 포트가 이미 사용 중이라면 `main_api.py`의 `uvicorn.run(port=8000)`을 변경하세요.
- **Flutter 실행 불가**: `flutter doctor`를 실행하여 환경 설정을 점검하세요.