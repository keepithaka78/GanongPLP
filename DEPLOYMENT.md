# 배포 가이드

이 문서는 가농바이오 양계 대시보드를 다양한 환경에 배포하는 방법을 설명합니다.

## 배포 옵션

### 1. 로컬 개발 환경 (현재 상태)

현재 로컬에서 개발 중이며, `http://localhost:8000`에서 실행됩니다.

**장점:**
- 무료
- 빠른 개발 및 테스트
- 완전한 제어

**단점:**
- 인터넷을 통한 원격 접속 불가
- 컴퓨터가 켜져 있어야 함

---

### 2. 로컬 네트워크 배포

같은 Wi-Fi/네트워크의 다른 기기에서 접속 가능하도록 설정

#### 설정 방법

1. **방화벽 설정**
   - Windows 방화벽에서 포트 8000 허용
   - 제어판 → Windows Defender 방화벽 → 고급 설정
   - 인바운드 규칙 → 새 규칙 → 포트 → TCP 8000

2. **서버 IP 확인**
   ```bash
   ipconfig
   # IPv4 주소 확인 (예: 192.168.0.100)
   ```

3. **다른 기기에서 접속**
   ```
   http://192.168.0.100:8000
   ```

**장점:**
- 무료
- 사무실/농장 내 여러 기기에서 접속 가능
- 데이터가 로컬에 안전하게 보관

**단점:**
- 같은 네트워크에서만 접속 가능
- 컴퓨터가 항상 켜져 있어야 함

---

### 3. 클라우드 배포 (인터넷 접속)

인터넷 어디서나 접속 가능한 웹 서비스로 배포

#### 옵션 A: Render.com (권장)

**무료 티어 제공**, Python 직접 지원

##### 배포 단계

1. **GitHub 계정 생성** (없는 경우)
   - https://github.com 방문
   - Sign up

2. **코드를 GitHub에 업로드**
   ```bash
   cd poultry-dashboard
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/your-username/poultry-dashboard.git
   git push -u origin main
   ```

3. **Render.com 계정 생성**
   - https://render.com 방문
   - GitHub 계정으로 로그인

4. **새 Web Service 생성**
   - Dashboard → "New +" → "Web Service"
   - GitHub 리포지토리 연결
   - `poultry-dashboard` 선택

5. **설정**
   ```
   Name: poultry-dashboard
   Region: Singapore (또는 가까운 지역)
   Branch: main
   Root Directory: (비워둠)
   Environment: Python 3
   Build Command: cd backend && pip install -r requirements.txt
   Start Command: cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT
   ```

6. **환경 변수 추가**
   - Advanced → Environment Variables
   - `EXCEL_DIR`: 엑셀 파일 경로 (클라우드에서는 데이터베이스 파일 사용)

7. **배포**
   - "Create Web Service" 클릭
   - 5-10분 대기
   - URL 확인: `https://poultry-dashboard.onrender.com`

**무료 티어 제한:**
- 15분 미사용 시 슬립 모드 (재접속 시 30초 소요)
- 750시간/월 무료 (매달 리셋)

**유료 티어 ($7/월):**
- 슬립 모드 없음
- 더 빠른 성능
- 커스텀 도메인 지원

##### 데이터 파일 처리

클라우드 배포 시 엑셀 파일을 직접 업로드할 수 없으므로:

**옵션 1: 초기 데이터만 사용**
- 로컬에서 데이터를 로드하여 `poultry.db` 생성
- `poultry.db` 파일을 GitHub에 커밋 (`.gitignore`에서 제외)
- 이후 수동 업데이트는 불가능

**옵션 2: 클라우드 스토리지 연동** (고급)
- Google Drive API 연동
- OneDrive API 연동
- S3 등 클라우드 스토리지 사용

---

#### 옵션 B: Railway.app

Render와 유사, 무료 티어 제공

1. https://railway.app 방문
2. GitHub 로그인
3. "New Project" → "Deploy from GitHub repo"
4. 설정:
   ```
   Build Command: cd backend && pip install -r requirements.txt
   Start Command: cd backend && python main.py
   ```

**무료 티어:**
- $5 크레딧/월 제공
- 약 500시간 사용 가능

---

#### 옵션 C: Heroku

유료 전환 (최소 $5/월)

---

### 4. 추천 배포 전략

#### 단계 1: 로컬 네트워크 배포 (즉시)
- 비용: $0
- 사무실/농장 내 사용
- 안정성 검증

#### 단계 2: 클라우드 배포 (필요 시)
- Render.com 무료 티어로 시작
- 외부 접속이 필요한 경우
- 안정성 확인 후 유료 전환 고려

---

## 배포 후 체크리스트

### 필수 확인 사항
- [ ] 서버가 정상적으로 시작되는가?
- [ ] API Health Check 성공: `/api/health`
- [ ] 대시보드 로딩 정상
- [ ] 데이터가 올바르게 표시되는가?
- [ ] 모든 페이지 접속 가능 (비교, 추이, 검색, 예측)
- [ ] 알림 기능 작동
- [ ] 필터링 기능 작동

### 성능 확인
- [ ] 페이지 로딩 속도 (< 3초)
- [ ] API 응답 속도 (< 1초)
- [ ] 그래프 렌더링 정상

### 보안
- [ ] 환경 변수 설정 (민감한 정보 노출 방지)
- [ ] HTTPS 사용 (Render는 자동 제공)
- [ ] 필요 시 인증 추가 고려

---

## 업데이트 배포

### 로컬 배포
```bash
# 코드 수정 후
# 서버 재시작 (Ctrl+C 후 다시 실행)
python main.py
```

### 클라우드 배포
```bash
# 코드 수정 후
git add .
git commit -m "업데이트 내용"
git push

# Render/Railway가 자동으로 재배포
```

---

## 문제 해결

### Render 배포 실패
1. 로그 확인: Dashboard → Service → Logs
2. Build Command 확인
3. Python 버전 확인 (3.11 필요)
4. requirements.txt 경로 확인

### 데이터가 표시되지 않음
1. 데이터베이스 파일 존재 확인
2. EXCEL_DIR 환경 변수 확인
3. 로그에서 에러 확인

### 성능 저하
1. 무료 티어 슬립 모드 확인
2. 데이터베이스 크기 확인
3. 불필요한 데이터 정리

---

## 비용 요약

| 옵션 | 월 비용 | 장점 | 단점 |
|------|---------|------|------|
| 로컬 | $0 | 완전 제어, 안전 | 원격 접속 불가 |
| 로컬 네트워크 | $0 | 무료, 내부 접속 | 외부 접속 불가 |
| Render 무료 | $0 | 인터넷 접속 | 슬립 모드 |
| Render 유료 | $7 | 항상 온, 빠름 | 월 비용 |
| Railway | ~$5 | 유연함 | 크레딧 소진 |

---

## 추가 고려사항

### 커스텀 도메인
- Render 유료: 자체 도메인 연결 가능
- 예: `dashboard.ganongbio.com`
- 도메인 비용: 연 $10-15

### 데이터 백업
- 정기적인 데이터베이스 백업 설정
- 클라우드 스토리지 활용 (Google Drive, OneDrive)

### 모니터링
- Render 대시보드에서 서버 상태 확인
- 이메일 알림 설정

### 확장성
- 사용자 증가 시 유료 플랜으로 업그레이드
- PostgreSQL 등 프로덕션 데이터베이스 고려

---

## 지원

배포 관련 문제가 있으면:
1. 로그 확인
2. README.md의 문제 해결 섹션 참조
3. GitHub Issues에 문의
