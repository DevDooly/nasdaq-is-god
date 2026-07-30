# 🛡️ Nasdaq is God - 개발 & Coolify 안전 배포 파이프라인 규칙 (Rulebook)

본 문서는 무분별한 배포 실패와 포트 충돌을 방지하고, Mini PC에서의 직접 검증 후 안전하게 운영 환경(Coolify)에 배포하기 위한 **표준 파이프라인 규칙 (Standard Operating Procedure)** 입니다.

---

## 📌 핵심 원칙: 브랜치 분리 및 배포 통제

```text
[개발자 / AI Assistant]
       │
       ▼ (1. 소스 수정 & SSH 수동 검증)
  [dev 브랜치] ───(Mini PC 수동 테스트 / 버그 수정 완료)───┐
                                                            ▼ (2. 검증 완료 후 Merge)
                                                       [main 브랜치]
                                                            │
                                                            ▼ (3. 100% 안전 자동 배포)
                                                      [Coolify (PaaS)]
```

1. **`dev` 브랜치 (개발 & 수동 테스트 전용)**:
   - 모든 코드 수정, 신규 기능 추가, Mini PC SSH 접속 수동 테스트는 `dev` 브랜치에서 진행합니다.
   - `dev` 브랜치에 Push 하더라도 **Coolify는 무분별하게 자동 배포되지 않습니다.**

2. **`main` 브랜치 (Coolify 운영 배포 전용)**:
   - Mini PC에서 `dev` 브랜치 테스트가 100% 성공하고 검증이 완료된 코드만 `main` 브랜치로 Merge / Push 됩니다.
   - Coolify는 오직 `main` 브랜치만 바라보며 100% 오류 없는 안전한 코드를 배포합니다.

---

## 🚀 단계별 작업 표준 절차 (Workflow Rule)

### 1단계: `dev` 브랜치에서 소스 수정 및 Mini PC SSH 수동 검증
1. 소스 수정 전 항상 `dev` 브랜치인지 확인합니다:
   ```bash
   git checkout dev
   ```
2. Mini PC에 SSH 접속하여 소스를 수정하거나 테스트를 진행합니다:
   ```bash
   git pull origin dev
   docker compose -f docker-compose.coolify.yml up -d --build
   ```
3. `curl`, 로그 확인 및 웹 화면 접속으로 버그/포트 에러가 없는지 100% 검증합니다.

---

### 2단계: 수동 테스트 포트 및 컨테이너 정리
Mini PC에서 검증이 끝나면 수동 테스트 컨테이너를 종료하여 포트(8081, 9095 등)를 깨끗하게 비워둡니다:
```bash
docker compose -f docker-compose.coolify.yml down
```

---

### 3단계: `main` 브랜치로 운영 반영 (Coolify 자동 배포)
수동 테스트와 포트 정리가 완료되면 `main` 브랜치에 커밋/Merge 하여 Push 합니다:
```bash
git checkout main
git merge dev
git push origin main
```
👉 **결과**: Coolify가 100% 검증된 `main` 브랜치 코드를 감지하여 단 1초의 포트 충돌이나 빌드 에러 없이 깔끔하게 한 방 배포를 완료합니다!

---

## ⚙️ Coolify 대시보드 설정 규칙

* **Coolify Project**: `nasdaqisgod`
* **Branch**: **`main`** (고정)
* **Ports Expose**:
  * `frontend`: `8081:80`
  * `backend`: `9095:9000`
