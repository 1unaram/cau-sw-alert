#!/bin/bash

# crontab에서 이 프로젝트의 작업을 제거하는 스크립트
cd "$(dirname "$0")"

SCRIPT_DIR="$(pwd)"

echo "$(date): Removing crontab entry for this project..."

# 현재 crontab을 가져와서 이 프로젝트 관련 항목만 제거
crontab -l 2>/dev/null | grep -v "$SCRIPT_DIR/run_app.sh" | crontab -

echo "$(date): Crontab entry removed successfully!"
echo ""
echo "Current crontab entries:"
crontab -l 2>/dev/null || echo "No crontab entries found."
