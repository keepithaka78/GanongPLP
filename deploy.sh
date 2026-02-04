#!/bin/bash

# GanongPLP 배포 스크립트
# 이 스크립트는 GitHub Actions에서 자동으로 실행됩니다
# 또는 수동으로 실행 가능: bash deploy.sh

set -e  # 에러 발생 시 스크립트 중단

echo "=== GanongPLP 자동 배포 시작 ==="
echo "시간: $(date)"
echo ""

# 프로젝트 경로 찾기 (여러 가능성 확인)
PROJECT_PATH=""

if [ -d "/home/ubuntu/GanongPLP" ]; then
    PROJECT_PATH="/home/ubuntu/GanongPLP"
elif [ -d "$HOME/GanongPLP" ]; then
    PROJECT_PATH="$HOME/GanongPLP"
elif [ -d "$(pwd)/GanongPLP" ]; then
    PROJECT_PATH="$(pwd)/GanongPLP"
else
    # 현재 디렉토리가 GanongPLP인 경우
    if [ -f "backend/main.py" ] && [ -f "deploy.sh" ]; then
        PROJECT_PATH="$(pwd)"
    fi
fi

if [ -z "$PROJECT_PATH" ] || [ ! -d "$PROJECT_PATH" ]; then
    echo "❌ 프로젝트 디렉토리를 찾을 수 없습니다"
    exit 1
fi

echo "✓ 프로젝트 경로: $PROJECT_PATH"
cd "$PROJECT_PATH"

# 1. 최신 코드 가져오기
echo ""
echo ">> Git에서 최신 코드 가져오는 중..."
git fetch origin
git reset --hard origin/main
echo "✓ 최신 코드 가져오기 완료"

# 2. 기존 프로세스 종료
echo ""
echo ">> 기존 프로세스 종료..."
pkill -f "python -m uvicorn" || true
sleep 1
echo "✓ 프로세스 종료 완료"

# 3. logs 디렉토리 생성
if [ ! -d "logs" ]; then
    mkdir -p logs
fi

# 4. Python 의존성 설치
echo ""
echo ">> Python 의존성 설치..."
pip install -q -r backend/requirements.txt --upgrade --break-system-packages
echo "✓ 의존성 설치 완료"

# 5. 새 프로세스 시작
echo ""
echo ">> 새 프로세스 시작..."
cd backend
nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 > ../logs/app.log 2>&1 &
cd ..

sleep 3

# 6. 프로세스 확인
if pgrep -f "python -m uvicorn" > /dev/null; then
    echo "✓ 프로세스 시작 성공"
else
    echo "❌ 프로세스 시작 실패"
    tail -20 logs/app.log
    exit 1
fi

# 7. 배포 완료
echo ""
echo "=== 배포가 완료되었습니다! ==="
echo "시간: $(date)"
echo "서비스 URL: http://13.236.3.48:8000"
