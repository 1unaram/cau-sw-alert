#!/bin/bash

# crontab에서 실행할 app.py 스크립트
# 스크립트 실행 디렉토리로 이동
cd "$(dirname "$0")"

# app.py 실행
python3 app.py

echo "$(date): Execution completed" >> cron.log
echo "---" >> cron.log
