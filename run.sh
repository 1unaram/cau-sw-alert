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

# API 키 파일 확인 및 생성
if [ ! -f "api_keys.env" ]; then
    echo "$(date): Creating api_keys.env file..."
    cat > api_keys.env << 'EOF'
# API Keys Configuration
# Please fill in your actual API keys below

# Notion API Key - Get it from https://www.notion.so/my-integrations
NOTION_API_KEY=your_notion_api_key_here

# Notion Database ID - Copy from your Notion database URL
DATABASE_ID=your_database_id_here
EOF
    echo ""
    echo "⚠️  IMPORTANT: API keys file created!"
    echo "📝 Please edit 'api_keys.env' file and add your actual API keys:"
    echo "   - NOTION_API_KEY: Get from https://www.notion.so/my-integrations"
    echo "   - DATABASE_ID: Copy from your Notion database URL"
    echo ""
else
    echo "$(date): api_keys.env file already exists"
fi

# run_app.sh에 실행 권한 부여
chmod +x run_app.sh

echo "$(date): Setup complete!"
echo ""

# 현재 절대 경로 가져오기
SCRIPT_DIR="$(pwd)"
CRON_JOB="0 6,9,12,15,18,21 * * * $SCRIPT_DIR/run_app.sh >> $SCRIPT_DIR/cron.log 2>&1"

# 기존 crontab에 같은 작업이 있는지 확인
if crontab -l 2>/dev/null | grep -q "$SCRIPT_DIR/run_app.sh"; then
    echo "Crontab entry already exists for this project."
else
    # 새로운 cron job 추가
    echo "$(date): Adding crontab entry..."
    (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
    echo "Crontab entry added successfully!"
    echo "App will run at 6, 9, 12, 15, 18, and 21 o'clock."
fi

echo ""
echo "Current crontab entries:"
crontab -l
