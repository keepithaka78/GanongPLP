#!/bin/bash

# 배포 스크립트 테스트용 (로컬에서 실행)
# 이 스크립트는 실제 서버 경로를 테스트합니다

echo "=== 배포 스크립트 테스트 ==="
echo ""

# SSH 접속 테스트
echo ">> SSH 접속 테스트..."
ssh -i "C:\Users\yimmj\OneDrive\Desktop\산란기록부 Renewal\PLP가농바이오\GanongPLP.pem" \
    ubuntu@13.236.3.48 \
    'echo "✓ SSH 접속 성공" && pwd && ls -la | head -5'

