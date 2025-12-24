#!/bin/bash

# 스크립트 실행 디렉토리로 이동
cd "$(dirname "$0")"
echo "$(date): Starting setup process..."


# ============ [1] 필요한 라이브러리 설치 (전역 환경에) ============
echo "$(date): Installing required packages..."
pip3 install requests beautifulsoup4 python-dotenv
echo ""


# ============ [2] Notion Key 파일 확인 ============
if [ ! -f notion_keys.env ]; then
    echo "$(date): notion_keys.env not found. Creating from template..."
    exit 1
else
    echo "$(date): notion_keys.env found."
fi


# ============ [3] 노션 데이터베이스 자동 생성 ============
echo ""
echo "$(date): Checking if Notion database needs to be created..."
if grep -q "^DATABASE_ID=$" notion_keys.env || ! grep -q "^DATABASE_ID=" notion_keys.env; then
    echo "$(date): DATABASE_ID is empty. Creating Notion database automatically..."
    echo ""
    python3 app/notion.py

    if [ $? -ne 0 ]; then
        echo ""
        echo "❌ ERROR: Failed to create Notion database."
        echo "   Please check your NOTION_API_KEY in notion_keys.env"
        exit 1
    fi
else
    echo "$(date): DATABASE_ID already exists. Skipping database creation."
fi


# ============ [4] data.json 파일 초기화 ============
echo "$(date): Creating fresh data.json..."
cat > data.json << 'EOF'
{}
EOF
echo "$(date): data.json created successfully."


# ============ [5] run_app.sh에 실행 권한 부여 ============
chmod +x run_app.sh

echo "$(date): Setup complete!"
echo ""


# ============ [6] crontab에 작업 추가 ============
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
