#!/bin/bash

# 스크립트 실행 디렉토리로 이동
cd "$(dirname "$0")"

echo "$(date): Starting setup process..."

# 필요한 라이브러리 설치 (전역 환경에)
echo "$(date): Installing required packages..."
pip3 install requests beautifulsoup4 python-dotenv

# init.py 실행
echo "$(date): Running initialization..."
python3 init.py

# run_app.sh에 실행 권한 부여
chmod +x run_app.sh

echo "$(date): Setup complete!"
echo ""

# 현재 절대 경로 가져오기
SCRIPT_DIR="$(pwd)"
CRON_JOB="0 */3 * * * $SCRIPT_DIR/run_app.sh >> $SCRIPT_DIR/cron.log 2>&1"

# 기존 crontab에 같은 작업이 있는지 확인
if crontab -l 2>/dev/null | grep -q "$SCRIPT_DIR/run_app.sh"; then
    echo "Crontab entry already exists for this project."
else
    # 새로운 cron job 추가
    echo "$(date): Adding crontab entry..."
    (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
    echo "Crontab entry added successfully!"
    echo "App will run every 3 hours starting from the next hour mark."
fi

echo ""
echo "Current crontab entries:"
crontab -l
