# 수동 배포 가이드

GitHub Actions 자동 배포가 작동할 때까지, 이 방법으로 서버에 배포할 수 있습니다.

## 🔧 수동 배포 방법

### Step 1: SSH로 서버 접속

```bash
ssh -i "C:\Users\yimmj\OneDrive\Desktop\산란기록부 Renewal\PLP가농바이오\GanongPLP.pem" ubuntu@13.236.3.48
```

### Step 2: 프로젝트 디렉토리 찾기

서버에 접속 후:

```bash
# 현재 디렉토리 확인
pwd

# GanongPLP 디렉토리 찾기
find ~ -name "GanongPLP" -type d
```

예상 경로:
- `/home/ubuntu/GanongPLP`
- 또는 다른 경로

### Step 3: 배포 실행

```bash
# 1. 프로젝트 디렉토리로 이동
cd /path/to/GanongPLP  # 위에서 찾은 경로로 수정

# 2. 최신 코드 가져오기
git pull origin main

# 3. 기존 프로세스 종료
pkill -f "python -m uvicorn" || true
sleep 1

# 4. 의존성 설치
pip install -q -r backend/requirements.txt --upgrade

# 5. logs 디렉토리 생성
mkdir -p logs

# 6. 새 프로세스 시작
cd backend
nohup python -m uvicorn main:app --host 0.0.0.0 --port 8000 > ../logs/app.log 2>&1 &
cd ..

# 7. 프로세스 확인
sleep 3
ps aux | grep "python -m uvicorn"

# 8. 로그 확인
tail -20 logs/app.log
```

### Step 4: 배포 확인

```
http://13.236.3.48:8000
```

에 접속해서 최신 기능이 보이는지 확인!

---

## 🐛 문제 해결

### Q: "GanongPLP 디렉토리를 찾을 수 없습니다"

```bash
# 모든 디렉토리 확인
ls -la ~
ls -la /opt
```

### Q: "프로세스 시작 실패"

```bash
# 로그 상세 확인
tail -100 logs/app.log

# 포트 확인
netstat -tlnp | grep 8000
# 또는
lsof -i :8000
```

### Q: "의존성 설치 실패"

```bash
# Python 버전 확인
python --version
python3 --version

# pip 업그레이드
pip install --upgrade pip
pip3 install --upgrade pip

# 직접 설치
pip3 install -r backend/requirements.txt
```

---

## 📊 배포 후 로그 확인

```bash
# 실시간 로그 보기
tail -f /path/to/GanongPLP/logs/app.log

# 마지막 50줄 보기
tail -50 /path/to/GanongPLP/logs/app.log

# 프로세스 확인
ps aux | grep uvicorn
```

---

## 🔄 간단한 배포 스크립트 (한 번에)

위의 Step 3를 한 번에 실행하려면:

```bash
cd /path/to/GanongPLP && \
git pull origin main && \
pkill -f "python -m uvicorn" || true && \
sleep 1 && \
pip install -q -r backend/requirements.txt --upgrade && \
mkdir -p logs && \
cd backend && \
nohup python -m uvicorn main:app --host 0.0.0.0 --port 8000 > ../logs/app.log 2>&1 & \
cd .. && \
sleep 3 && \
echo "배포 완료!" && \
tail -10 logs/app.log
```

---

## 💡 자동 배포 설정

자동 배포를 활성화하려면 GitHub Secrets을 설정하세요:

### GitHub Secrets 설정

1. GitHub 저장소: https://github.com/keepithaka78/GanongPLP
2. Settings → Secrets and variables → Actions
3. "New repository secret" 클릭

**Secret 1: EC2_PRIVATE_KEY**
- Name: `EC2_PRIVATE_KEY`
- Value: GanongPLP.pem 파일의 전체 내용

**Secret 2: EC2_HOST**
- Name: `EC2_HOST`
- Value: `13.236.3.48`

**Secret 3: EC2_USER**
- Name: `EC2_USER`
- Value: `ubuntu`

설정 후 `git push origin main` 실행하면 자동 배포 시작!
