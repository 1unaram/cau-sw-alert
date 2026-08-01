import datetime
import os
import sys

import requests
from dotenv import load_dotenv

load_dotenv("keys.env")

NOTION_API_KEY = os.getenv("NOTION_API_KEY")
DATABASE_ID = os.getenv("DATABASE_ID")
PERSON_ID = os.getenv("PERSON_ID")
PARENT_PAGE_ID = os.getenv("PARENT_PAGE_ID")


def create_notion_database():
    """
    노션에 새 데이터베이스를 생성합니다.
    필요한 속성: Title, URL, Date, Type, Read, Noti
    """
    if not NOTION_API_KEY:
        print("❌ ERROR: NOTION_API_KEY가 keys.env에 설정되지 않았습니다.")
        print("   https://www.notion.so/my-integrations 에서 API 키를 생성하세요.")
        sys.exit(1)

    if not PARENT_PAGE_ID:
        print("❌ ERROR: PARENT_PAGE_ID가 keys.env에 설정되지 않았습니다.")
        print("   노션에서 데이터베이스를 생성할 부모 페이지 ID를 입력하세요.")
        print("   1. 노션 페이지를 열기")
        print("   2. URL에서 페이지 ID 복사 (예: https://notion.so/PAGE_ID)")
        print("   3. Integration 연결 확인 (페이지 우측 상단 '...' > Add connections)")
        sys.exit(1)

    if not PERSON_ID:
        print("⚠️  WARNING: PERSON_ID가 설정되지 않았습니다. Noti 필드는 비활성화됩니다.")

    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": "2025-09-03"
    }

    print(f"✅ 부모 페이지 ID 사용: {PARENT_PAGE_ID}")

    # 데이터베이스 생성
    properties = {
        "Title": {
            "title": {}
        },
        "URL": {
            "url": {}
        },
        "Date": {
            "date": {}
        },
        "Type": {
            "select": {
                "options": [
                    {"name": "Notice", "color": "yellow"},
                    {"name": "SWedu", "color": "yellow"},
                    {"name": "ISNotice", "color": "yellow"},
                    {"name": "Contest", "color": "blue"},
                    {"name": "Employment", "color": "blue"},
                    {"name": "KOFIA", "color": "blue"},
                    {"name": "CampusRecruit", "color": "blue"},
                ]
            }
        },
        "Read": {
            "checkbox": {}
        }
    }

    # PERSON_ID가 있으면 Noti 필드 추가
    if PERSON_ID:
        properties["Noti"] = {
            "people": {}
        }

    database_payload = {
        "parent": {
            "type": "page_id",
            "page_id": PARENT_PAGE_ID
        },
        "title": [
            {
                "type": "text",
                "text": {
                    "content": "CAU SW Notice"
                }
            }
        ],
        "initial_data_source": {
            "properties": properties
        }
    }

    try:
        create_response = requests.post(
            "https://api.notion.com/v1/databases",
            headers=headers,
            json=database_payload
        )

        if create_response.status_code != 200:
            print(f"❌ ERROR: 데이터베이스 생성 실패 (Status {create_response.status_code})")
            print(f"   응답: {create_response.text}")
            sys.exit(1)

        database_data = create_response.json()
        database_id = database_data["id"]
        database_url = database_data.get("url", "N/A")

        print(f"✅ 데이터베이스 생성 완료!")
        print(f"   URL: {database_url}")
        print(f"   ID: {database_id}")

        return database_id

    except Exception as e:
        print(f"❌ ERROR: 데이터베이스 생성 중 오류 발생: {str(e)}")
        sys.exit(1)


def update_env_file(database_id):
    """
    keys.env 파일에 DATABASE_ID를 업데이트합니다.
    """
    try:
        # 기존 파일 읽기
        with open("keys.env", "r", encoding="utf-8") as f:
            lines = f.readlines()

        # DATABASE_ID 업데이트
        updated = False
        for i, line in enumerate(lines):
            if line.startswith("DATABASE_ID="):
                lines[i] = f"DATABASE_ID={database_id}\n"
                updated = True
                break

        # DATABASE_ID가 없으면 추가
        if not updated:
            lines.append(f"\nDATABASE_ID={database_id}\n")

        # 파일 쓰기
        with open("keys.env", "w", encoding="utf-8") as f:
            f.writelines(lines)

        print(f"✅ keys.env 파일에 DATABASE_ID 저장 완료!")

    except Exception as e:
        print(f"❌ ERROR: keys.env 업데이트 중 오류: {str(e)}")
        sys.exit(1)


# fetch한 데이터를 노션 데이터베이스에 페이지로 생성
def create_page_to_notion_database(item, type, new_uids):
    properties = {
        "Read": {
            "checkbox": False
        },
        "Title": {
            "title": [
                {
                    "text": {
                        "content": item['title']
                    }
                }
            ]
        },
        "URL": {
            "url": item['url']
        },
        "Date": {
            "date": {
                "start": item['date']
            }
        },
        "Type": {
            "select": {
                "name": type
            }
        }
    }

    # PERSON_ID가 설정된 경우에만 Noti 필드 추가
    if PERSON_ID:
        properties["Noti"] = {
            "people": [
                {
                    "object": "user",
                    "id": PERSON_ID
                }
            ]
        }

    payload = {
        "parent": {
            "database_id": DATABASE_ID
        },
        "properties": properties
    }
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        'Authorization': f'Bearer {NOTION_API_KEY}',
        'Notion-Version': '2025-09-03'
    }

    try:
        response = requests.post(f"https://api.notion.com/v1/pages", json=payload, headers=headers)

        if response.status_code != 200:
            print(f"❌ [{datetime.datetime.now()}] Failed to create Notion page: {response.status_code} - {response.text[:200]}")
            return

        new_uids.add(item['uid'])
    except Exception as e:
        print(f"❌ [{datetime.datetime.now()}] Error creating Notion page: {str(e)}")


if __name__ == "__main__":
    print("=" * 60)
    print("CAU SW Notice - 노션 데이터베이스 자동 생성")
    print("=" * 60)
    print()

    database_id = create_notion_database()
    update_env_file(database_id)

    print()
    print("=" * 60)
    print("🎉 설정 완료! 이제 app.py를 실행할 수 있습니다.")
    print("=" * 60)
