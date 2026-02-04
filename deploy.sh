#!/bin/bash

# GanongPLP 배포 스크립트
# 이 스크립트는 GitHub Actions에서 자동으로 실행됩니다
# 또는 수동으로 실행 가능: bash deploy.sh

set -e  # 에러 발생 시 스크립트 중단

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 프로젝트 경로 (필요에 따라 수정)
PROJECT_PATH="/home/ubuntu/GanongPLP"

echo -e "${YELLOW}=== GanongPLP 자동 배포 시작 ===${NC}"
echo "시간: $(date)"
echo ""

# 1. 프로젝트 디렉토리 확인
if [ ! -d "$PROJECT_PATH" ]; then
    echo -e "${RED}❌ 프로젝트 디렉토리를 찾을 수 없습니다: $PROJECT_PATH${NC}"
    exit 1
fi

echo -e "${GREEN}✓ 프로젝트 경로 확인${NC}: $PROJECT_PATH"

# 2. 프로젝트 디렉토리로 이동
cd "$PROJECT_PATH"
echo -e "${GREEN}✓ 디렉토리 이동 완료${NC}"

# 3. 최신 코드 가져오기
echo ""
echo -e "${YELLOW}>> Git에서 최신 코드 가져오는 중...${NC}"
git fetch origin
git reset --hard origin/main
echo -e "${GREEN}✓ 최신 코드 가져오기 완료${NC}"

# 4. 현재 실행 중인 Python 프로세스 확인 및 종료
echo ""
echo -e "${YELLOW}>> 기존 프로세스 종료...${NC}"

# uvicorn 프로세스 찾기
UVICORN_PID=$(pgrep -f "uvicorn.*backend.main" || true)

if [ -n "$UVICORN_PID" ]; then
    echo "기존 프로세스 ID: $UVICORN_PID"
    kill -15 "$UVICORN_PID" 2>/dev/null || true

    # 프로세스 종료 대기 (최대 10초)
    for i in {1..10}; do
        if ! kill -0 "$UVICORN_PID" 2>/dev/null; then
            echo -e "${GREEN}✓ 프로세스 정상 종료${NC}"
            break
        fi
        if [ $i -eq 10 ]; then
            echo "강제 종료 중..."
            kill -9 "$UVICORN_PID" 2>/dev/null || true
        fi
        sleep 1
    done
else
    echo -e "${YELLOW}! 실행 중인 프로세스가 없습니다${NC}"
fi

# 5. Python 의존성 설치
echo ""
echo -e "${YELLOW}>> Python 의존성 설치...${NC}"
cd backend
pip install -q -r requirements.txt --upgrade 2>&1 || {
    echo -e "${RED}❌ 의존성 설치 실패${NC}"
    exit 1
}
cd ..
echo -e "${GREEN}✓ 의존성 설치 완료${NC}"

# 6. 데이터베이스 체크 및 초기화
echo ""
echo -e "${YELLOW}>> 데이터베이스 확인...${NC}"
if [ ! -f "data/poultry.db" ]; then
    echo "데이터베이스 생성 중..."
    python backend/main.py --init-db 2>/dev/null || true
    echo -e "${GREEN}✓ 데이터베이스 생성 완료${NC}"
else
    echo -e "${GREEN}✓ 데이터베이스 존재${NC}"
fi

# 7. 새 프로세스 시작
echo ""
echo -e "${YELLOW}>> 새 프로세스 시작...${NC}"

# nohup으로 백그라운드 실행
nohup python -m uvicorn backend.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 2 \
    > logs/app.log 2>&1 &

sleep 2

# 프로세스 확인
NEW_PID=$(pgrep -f "uvicorn.*backend.main" || true)
if [ -n "$NEW_PID" ]; then
    echo -e "${GREEN}✓ 새 프로세스 시작 성공${NC}"
    echo "프로세스 ID: $NEW_PID"
else
    echo -e "${RED}❌ 프로세스 시작 실패${NC}"
    echo "로그 확인:"
    tail -20 logs/app.log
    exit 1
fi

# 8. 서비스 헬스 체크
echo ""
echo -e "${YELLOW}>> 서비스 헬스 체크...${NC}"
sleep 2

for i in {1..10}; do
    if curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ 서비스 정상 작동${NC}"
        break
    fi
    if [ $i -eq 10 ]; then
        echo -e "${RED}❌ 서비스 헬스 체크 실패${NC}"
        tail -20 logs/app.log
        exit 1
    fi
    echo "대기 중... ($i/10)"
    sleep 1
done

# 9. 배포 완료
echo ""
echo -e "${GREEN}=== 배포가 완료되었습니다! ===${NC}"
echo "시간: $(date)"
echo "서비스 URL: http://13.236.3.48:8000"
echo ""
echo "로그 확인: tail -f logs/app.log"
