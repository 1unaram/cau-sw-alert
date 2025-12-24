#!/bin/bash

# crontab에서 이 프로젝트의 작업을 제거하는 스크립트

# 스크립트 실행 디렉토리로 이동
cd "$(dirname "$0")"

SCRIPT_DIR="$(pwd)"

echo "Removing crontab entries for: $SCRIPT_DIR/run_app.sh"
echo ""

# 현재 crontab 확인
if ! crontab -l 2>/dev/null | grep -q "$SCRIPT_DIR/run_app.sh"; then
    echo "No crontab entry found for this project."
    exit 0
fi

# 해당 프로젝트의 cron job 제거
crontab -l 2>/dev/null | grep -v "$SCRIPT_DIR/run_app.sh" | crontab -

echo "✅ Crontab entry removed successfully!"
echo ""
echo "Current crontab entries:"
crontab -l
