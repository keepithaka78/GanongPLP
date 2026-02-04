# GitHub Actions를 이용한 자동 배포 가이드

이 문서는 GitHub에 push할 때 AWS EC2 서버에 자동으로 배포되도록 설정하는 방법을 설명합니다.

## 📋 준비 사항

### 1. AWS EC2 인스턴스 정보
- **IP 주소**: 13.236.3.48
- **사용자**: ubuntu
- **SSH 키**: GanongPLP.pem
- **프로젝트 경로**: /home/ubuntu/GanongPLP (또는 실제 경로)

### 2. GitHub 저장소
- 이미 생성됨: https://github.com/keepithaka78/GanongPLP.git

## 🔧 설정 단계

### Step 1: GitHub Actions Secrets 설정

GitHub 저장소의 Secrets에 AWS 접근 정보를 추가해야 합니다.

#### 1-1. GitHub에 로그인
```
https://github.com/keepithaka78/GanongPLP
Settings → Secrets and variables → Actions
```

#### 1-2. 새 Secret 추가 (3개)

**Secret 1: EC2_PRIVATE_KEY**
- Name: `EC2_PRIVATE_KEY`
- Value: `GanongPLP.pem` 파일의 내용 전체 (-----BEGIN PRIVATE KEY-----부터 끝까지)
- 저장

**Secret 2: EC2_HOST**
- Name: `EC2_HOST`
- Value: `13.236.3.48`
- 저장

**Secret 3: EC2_USER**
- Name: `EC2_USER`
- Value: `ubuntu`
- 저장

### Step 2: 배포 파일 확인

다음 파일들이 이미 생성되어 있는지 확인하세요:

```
GanongPLP/
├── .github/
│   └── workflows/
│       └── deploy.yml          ✓ 워크플로우 설정
├── deploy.sh                   ✓ 배포 스크립트
└── logs/                        ✓ 로그 디렉토리
```

### Step 3: 로컬 Git 설정 확인

```bash
cd C:\Users\yimmj\OneDrive\Desktop\산란기록부\ Renewal\PLP가농바이오\현재\ 계군\GanongPLP

# 원격 저장소 확인
git remote -v
# origin  https://github.com/keepithaka78/GanongPLP.git (fetch)
# origin  https://github.com/keepithaka78/GanongPLP.git (push)
```

## 🚀 자동 배포 사용법

### 배포 트리거

코드를 GitHub main 브랜치에 push하면 자동으로 배포됩니다:

```bash
# 파일 수정 후
git add .
git commit -m "설명"
git push origin main
```

### 배포 진행 상황 확인

1. GitHub 저장소 접속
2. **Actions** 탭 클릭
3. 최신 워크플로우 클릭
4. 진행 상황 모니터링

## 📊 배포 워크플로우 상세

### 자동 배포 과정:

1. **코드 푸시** → GitHub에 코드 업로드
2. **Actions 트리거** → 자동으로 배포 작업 시작
3. **SSH 연결** → AWS EC2 서버에 접속
4. **Git Pull** → 최신 코드 다운로드
5. **의존성 설치** → Python 패키지 설치
6. **프로세스 재시작** → uvicorn 서버 재시작
7. **헬스 체크** → 서비스 정상 작동 확인
8. **배포 완료** → 자동 알림

## 🔍 문제 해결

### 배포 실패 시 확인할 것:

#### 1. GitHub Actions 로그 확인
- GitHub → Actions → 실패한 워크플로우 클릭
- 로그에서 에러 메시지 확인

#### 2. AWS 서버 직접 확인
```bash
# SSH 접속
ssh -i "GanongPLP.pem" ubuntu@13.236.3.48

# 프로세스 상태 확인
ps aux | grep uvicorn

# 로그 확인
tail -f /home/ubuntu/GanongPLP/logs/app.log

# 서비스 테스트
curl http://localhost:8000/api/health
```

#### 3. 일반적인 에러

**에러: Permission denied (publickey)**
- GitHub Secrets에 SSH 키가 올바르게 설정되었는지 확인
- SSH 키의 형식 확인 (-----BEGIN PRIVATE KEY-----로 시작)

**에러: No such file or directory**
- AWS 서버의 프로젝트 경로 확인
- deploy.sh의 PROJECT_PATH 수정 필요

**에러: Port 8000 already in use**
- 기존 프로세스 확인: `ps aux | grep uvicorn`
- 수동으로 종료: `kill -9 [PID]`

## 📝 수동 배포 (선택사항)

GitHub Actions 없이 수동으로 배포하려면:

```bash
# 1. SSH 접속
ssh -i "GanongPLP.pem" ubuntu@13.236.3.48

# 2. 배포 스크립트 실행
cd /home/ubuntu/GanongPLP
bash deploy.sh
```

## 🔐 보안 주의사항

⚠️ **중요**: SSH 개인 키 관리

- SSH 키는 절대 GitHub에 직접 커밋하지 마세요
- GitHub Secrets에만 저장하세요
- SSH 키 파일의 권한: `chmod 600 GanongPLP.pem`
- 필요시 새로운 SSH 키 쌍 생성 권장

## 📊 배포 상태 모니터링

### 자동 배포 후 확인:

1. **서비스 접속**: http://13.236.3.48:8000
2. **API 헬스 체크**: http://13.236.3.48:8000/api/health
3. **최신 기능 확인**:
   - 주간 산란율 탭
   - 계군 상세 분석 탭
   - 모든 네비게이션 링크

## 💡 팁

### 배포 속도 향상
- AWS 서버 용량 확인
- 불필요한 데이터 정리
- 데이터베이스 인덱싱 추가

### 롤백 (이전 버전으로 되돌리기)
```bash
# SSH 접속 후
cd /home/ubuntu/GanongPLP
git log --oneline | head -10  # 커밋 확인
git reset --hard [커밋ID]      # 해당 버전으로 복원
bash deploy.sh                # 배포 재실행
```

### 배포 로그 확인
```bash
# SSH 접속 후
cd /home/ubuntu/GanongPLP
tail -f logs/app.log          # 실시간 로그 보기
tail -n 100 logs/app.log      # 마지막 100줄 보기
```

## 🔄 다음 단계

1. ✅ GitHub Secrets 설정 완료
2. ✅ 배포 파일 생성 완료
3. 📍 **첫 배포**: `git push origin main` 실행
4. 🔍 GitHub Actions 페이지에서 진행 상황 확인
5. ✔️ 서버 접속 후 배포 성공 확인

## 📞 지원

배포 관련 문제:
1. GitHub Actions 로그 확인
2. AWS 서버 로그 확인: `tail -f /home/ubuntu/GanongPLP/logs/app.log`
3. 필요시 SSH로 직접 접속하여 문제 진단

## 📚 참고

- [GitHub Actions 문서](https://docs.github.com/en/actions)
- [AWS EC2 SSH 연결](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/AccessingInstancesLinux.html)
- [uvicorn 문서](https://www.uvicorn.org/)
