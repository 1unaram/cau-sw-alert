import datetime
import json
import os

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv("api_keys.env")

NOTION_API_KEY = os.getenv("NOTION_API_KEY")
DATABASE_ID = os.getenv("DATABASE_ID")

existing_uids = set()
new_uids = set()


def add_new_uids():
    global new_uids

    try:
        with open("data.json", "r+", encoding='utf-8') as data_file:
            existing_data = data_file.read()
            if existing_data:
                data = json.loads(existing_data)
            else:
                data = {}
            for uid in new_uids:
                data[uid] = True
            data_file.seek(0)
            json.dump(data, data_file)
            data_file.truncate()
    except Exception as e:
        with open("error.log", "a", encoding='utf-8') as error_log:
            error_log.write(f"[{datetime.datetime.now()}] Error updating data.json: {str(e)}\n")


def fetch_previous_data():
    global existing_uids

    try:
        with open("data.json", "r", encoding='utf-8') as data_file:
            existing_data = data_file.read()
            if existing_data:
                data = json.loads(existing_data)
                existing_uids = set(data.keys())
            else:
                existing_uids = set()
    except FileNotFoundError:
        print("data.json not found. Starting with an empty set of existing UIDs.")
        existing_uids = set()
    except Exception as e:
        with open("error.log", "a", encoding='utf-8') as error_log:
            error_log.write(f"[{datetime.datetime.now()}] Error reading data.json: {str(e)}\n")
        existing_uids = set()


def create_page_to_database(item, type):
    payload = {
        "parent": {
            "database_id": DATABASE_ID
        },
        "properties": {
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
                    "start": datetime.datetime.strptime(item['date'], '%Y.%m.%d').date().isoformat()
                }
            },
            "Type": {
                "select": {
                    "name": type
                }
            }
        }
    }
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        'Authorization': f'Bearer {NOTION_API_KEY}',
        'Notion-Version': '2022-06-28'
    }

    try:
        response = requests.post(f"https://api.notion.com/v1/pages", json=payload, headers=headers)
    except Exception as e:
        with open("error.log", "a", encoding='utf-8') as error_log:
            error_log.write(f"[{datetime.datetime.now()}] Error occurred while creating page: {str(e)}\n")


def fetch_posts(type):
    global existing_uids, new_uids

    url = ''
    if type == 'Notice':
        url = 'https://cse.cau.ac.kr/sub05/sub0501.php'
    elif type == 'Employment':
        url = 'https://cse.cau.ac.kr/sub05/sub0502.php'

    response = requests.get(url)
    response.encoding = 'utf-8'

    if response.status_code != 200:
        try:
            with open("log", "a", encoding='utf-8') as log_file:
                log_file.write(f"[{datetime.datetime.now()}] {response.status_code} - {response.text}\n")
        except Exception as e:
            with open("error.log", "a", encoding='utf-8') as error_log:
                error_log.write(f"[{datetime.datetime.now()}] Error occurred: {str(e)}\n")
    else:
        html = response.text
        soup = BeautifulSoup(html, 'html.parser')
        table = soup.find('table', class_='table-basic')
        rows = table.find_all('tr')[1:]

        data = {}
        for row in rows:
            col = row.find('td', class_='aleft')
            uid = type[0] + col.find('a')['href'].split('uid=')[1].split('&')[0]

            if uid in existing_uids:
                continue

            title = col.get_text(strip=True).replace('NEW', '').strip()
            post_url = url + col.find('a')['href']
            date = row.find_all('td', class_='pc-only')[2].get_text(strip=True)

            data[uid] = {
                'title': title,
                'url': post_url,
                'date': date
            }
            new_uids.add(uid)

        if data:
            for item in data.keys():
                create_page_to_database(data[item], type)


if __name__ == "__main__":
    fetch_previous_data()
    fetch_posts('Notice')
    fetch_posts('Employment')
    add_new_uids()
