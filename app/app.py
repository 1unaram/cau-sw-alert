import datetime
import json
import os
import re
import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from notion import create_page_to_notion_database, create_error_page
from dotenv import load_dotenv

# 스크립트 위치 기준 절대 경로
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, 'keys.env'))
DATA_FILE = os.path.join(BASE_DIR, 'data.json')

existing_uids = set()
new_uids = set()


def request_with_retry(func, *args, retries=3, delay=5, **kwargs):
    """
    일시적인 연결 오류(Connection refused, timeout 등)로 인한 실패를 흡수하기 위해
    지정한 요청 함수를 최대 retries회까지 재시도한다. 모두 실패하면 마지막 예외를 그대로 던진다.
    """
    last_exc = None
    for attempt in range(1, retries + 1):
        try:
            return func(*args, **kwargs)
        except requests.exceptions.RequestException as e:
            last_exc = e
            print(f"⚠️  [{datetime.datetime.now()}] Request failed (attempt {attempt}/{retries}): {e}")
            if attempt < retries:
                time.sleep(delay)
    raise last_exc


def add_new_uids():
    global new_uids

    if not new_uids:
        print("ℹ️  No new UIDs to add")
        return

    try:
        with open(DATA_FILE, "r+", encoding='utf-8') as data_file:
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
        kofia_new = [uid for uid in new_uids if uid.startswith('KOFIA')]
        print(f"✅ Added {len(new_uids)} new UIDs to {DATA_FILE}")
    except Exception as e:
        print(f"❌ [{datetime.datetime.now()}] Error updating data.json: {str(e)}")


def load_previous_data():
    global existing_uids

    try:
        with open(DATA_FILE, "r", encoding='utf-8') as data_file:
            existing_data = data_file.read()
            if existing_data:
                data = json.loads(existing_data)
                existing_uids = set(data.keys())
            else:
                existing_uids = set()
        print(f"✅ Loaded {len(existing_uids)} existing UIDs from {DATA_FILE}")
    except FileNotFoundError:
        print(f"data.json not found at {DATA_FILE}. Starting with an empty set of existing UIDs.")
        existing_uids = set()
    except Exception as e:
        print(f"❌ [{datetime.datetime.now()}] Error reading data.json: {str(e)}")
        existing_uids = set()


def fetch_kofia_posts():
    global existing_uids, new_uids

    base_url = 'https://www.kofia.or.kr/brd/m_96/list.do'
    urls = [
        'https://www.kofia.or.kr/brd/m_96/list.do?page=3',
        'https://www.kofia.or.kr/brd/m_96/list.do?page=2',
        'https://www.kofia.or.kr/brd/m_96/list.do?page=1',
        ]

    data = {}

    for url in urls:
        response = request_with_retry(requests.get, url)
        response.encoding = 'utf-8'

        if response.status_code != 200:
            print(f"❌ [{datetime.datetime.now()}] KOFIA fetch failed: {response.status_code}")
        else:
            html = response.text
            soup = BeautifulSoup(html, 'html.parser')
            table = soup.find('table', class_='common2 mgb25')
            rows = table.find_all('tr')[1:]

            for row in rows:
                cols = row.find_all('td')

                # [2] 회사명
                company = cols[1].text.strip()

                # [3] 제목
                title = cols[2].text.strip()
                if not any(keyword in title for keyword in ['정보보호', '보안', '보호', '해킹', '취약점', '사이버', '네트워크', 'IT', '정보보안']):
                    continue

                # [3] URL 및 고유 ID 추출
                href = cols[2].find('a')['href']
                post_url = 'https://www.kofia.or.kr/brd/m_96' + href[1:]

                # URL에서 seq 파라미터 추출하여 고유 ID로 사용
                seq_match = re.search(r'seq=(\d+)', href)
                if not seq_match:
                    continue
                uid = 'KOFIA' + seq_match.group(1)

                if uid in existing_uids or uid in new_uids:
                    continue

                # [4] 날짜
                date = cols[4].get_text(strip=True)

                data[uid] = {
                    'title': title,
                    'url': post_url,
                    'date': datetime.datetime.strptime(date, '%Y-%m-%d').date().isoformat(),
                    'uid': uid
                }

    if data:
        for item in data.keys():
            create_page_to_notion_database(data[item], 'KOFIA', new_uids)


def fetch_is_posts(type):
    global existing_uids, new_uids

    url = 'https://security.cau.ac.kr/board.htm?bbsid=notice'

    response = request_with_retry(requests.get, url)
    response.encoding = 'euc-kr'

    if response.status_code != 200:
        print(f"❌ [{datetime.datetime.now()}] ISNotice fetch failed: {response.status_code}")
    else:
        html = response.text
        soup = BeautifulSoup(html, 'html.parser')
        table = soup.find('table', class_='listTable')
        tbody = table.find('tbody')
        rows = tbody.find_all('tr')

        data = {}
        for row in rows:
            cols = row.find_all('td')

            # 공지는 건너뛰기
            if cols[0].find('img'):
                continue

            # [1] 번호
            uid = 'ISN' + cols[0].text.strip()
            if uid in existing_uids:
                continue

            # [2] 제목
            title = cols[1].find('a').get_text(strip=True).strip()

            # [3] URL
            post_url = 'https://security.cau.ac.kr/board.htm' + cols[1].find('a')['href']

            # [4] 날짜
            date = cols[3].get_text(strip=True)

            data[uid] = {
                'title': title,
                'url': post_url,
                'date': datetime.datetime.strptime(date, '%Y.%m.%d').date().isoformat(),
                'uid': uid
            }

        if data:
            for item in data.keys():
                create_page_to_notion_database(data[item], type, new_uids)


def fetch_posts(type):
    global existing_uids, new_uids

    url = ''
    if type == 'Notice':
        url = 'https://cse.cau.ac.kr/sub05/sub0501.php'
    elif type == 'Employment':
        url = 'https://cse.cau.ac.kr/sub05/sub0502.php'
    elif type == 'Contest':
        url = 'https://cse.cau.ac.kr/sub05/sub0506.php'

    response = request_with_retry(requests.get, url)
    response.encoding = 'utf-8'

    if response.status_code != 200:
        print(f"❌ [{datetime.datetime.now()}] {type} fetch failed: {response.status_code}")
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
                'date': datetime.datetime.strptime(date, '%Y.%m.%d').date().isoformat(),
                'uid': uid
            }

        if data:
            for item in data.keys():
                create_page_to_notion_database(data[item], type, new_uids)

# (4) SW교육원 공지사항
def fetch_swedu(type):
    global existing_uids, new_uids

    base_url = 'https://swedu.cau.ac.kr/board'
    url = base_url + '/list?boardtypeid=7&menuid=001005005'

    response = request_with_retry(requests.get, url)
    response.encoding = 'utf-8'

    if response.status_code != 200:
        print(f"❌ [{datetime.datetime.now()}] SWedu fetch failed: {response.status_code}")
    else:
        html = response.text
        soup = BeautifulSoup(html, 'html.parser')
        table = soup.find('table')
        rows = table.find_all('tr')[1:]

        data = {}
        for row in rows:
            col = row.find('td', class_='tl').find('a')
            uid = type[0] + col['href'].split('boardid=')[1].split('&')[0]

            if uid in existing_uids:
                continue

            title = col.get_text(strip=True)
            post_url = base_url  + col['href'][1:]
            date = row.find_all('td')[2].get_text(strip=True)

            data[uid] = {
                'title': title,
                'url': post_url,
                'date': datetime.datetime.strptime(date, '%Y-%m-%d').date().isoformat(),
                'uid': uid
            }

        if data:
            for item in data.keys():
                create_page_to_notion_database(data[item], type, new_uids)


# (7) 캠퍼스리쿠르팅
def fetch_campus_recruitment():
    global existing_uids, new_uids

    login_url = 'https://rainbow.cau.ac.kr/site/member/logonnew'
    base_url = 'https://rainbow.cau.ac.kr/site/program/recruit/listCampusRecruit'

    session = requests.Session()
    user_id = os.getenv('C_ID')
    user_pw = os.getenv('C_PW')
    if user_id and user_pw:
        request_with_retry(
            session.post,
            login_url,
            data={
                'prevurl': '/site/program/recruit/listCampusRecruit',
                'mobileyn': 'N',
                'userid': user_id,
                'userpw': user_pw
            }
        )

    response = request_with_retry(session.get, base_url)
    response.encoding = 'utf-8'

    if response.status_code != 200:
        print(f"❌ [{datetime.datetime.now()}] Campus Recruitment fetch failed: {response.status_code}")
    elif 'autherror' in response.url or '로그인 해주세요' in response.text:
        print("❌ Campus Recruitment requires login")
        print("   Set C_ID and C_PW in environment (or keys.env) and run again.")
        raise RuntimeError("Campus Recruitment requires login")
    else:
        html = response.text
        soup = BeautifulSoup(html, 'html.parser')
        table = (
            soup.select_one('div.table_style1 table')
            or soup.find('table', class_='table_style1')
        )

        if not table:
            print("❌ Campus Recruitment table not found")
            raise RuntimeError("Campus Recruitment table not found")

        rows = table.find_all('tr')[1:]

        data = {}
        for row in rows:
            cols = row.find_all('td')
            if len(cols) < 5:
                continue

            link = cols[2].find('a')
            if not link or 'href' not in link.attrs:
                continue

            uid_match = re.search(r'campusrecruitno=(\d+)', link['href'])
            if not uid_match:
                continue

            uid = 'CR' + uid_match.group(1)

            if uid in existing_uids or uid in new_uids:
                continue

            organization = cols[1].get_text(' ', strip=True)
            title = link.get_text(strip=True)
            period = re.sub(r'\s+', ' ', cols[4].get_text(' ', strip=True)).strip()
            post_url = urljoin(base_url, link['href'])

            data[uid] = {
                'title': f'[{organization}] {title} ({period})',
                'url': post_url,
                'date': datetime.datetime.now().date().isoformat(),
                'uid': uid
            }

        if data:
            for item in data.keys():
                create_page_to_notion_database(data[item], 'CampusRecruit', new_uids)


def run_step(label, func, *args, **kwargs):
    """
    fetch 함수 하나를 실행하고, 실패해도 다른 fetch에 영향이 없도록 예외를 격리한다.
    실패 시 같은 Notion DB에 알림용 페이지를 생성해 원인을 확인할 수 있게 한다.
    """
    try:
        func(*args, **kwargs)
    except Exception as e:
        print(f"❌ [{datetime.datetime.now()}] {label} step failed: {type(e).__name__}: {e}")
        create_error_page(label, f"{type(e).__name__}: {e}")


if __name__ == "__main__":

    # --- 기존 데이터 불러오기 ---
    load_previous_data()

    # 1) 소프트웨어학부 공지사항
    run_step('Notice', fetch_posts, 'Notice')

    # 2) 소프트웨어학부 취업정보
    run_step('Employment', fetch_posts, 'Employment')

    # 3) 소프트웨어학부 공모전 소식
    run_step('Contest', fetch_posts, 'Contest')

    # 4) SW교육원 공지사항
    run_step('SWedu', fetch_swedu, 'SWedu')

    # 5) 산업보안학과 공지사항
    run_step('ISNotice', fetch_is_posts, 'ISNotice')

    # 6) 금융투자협회 채용 공고
    run_step('KOFIA', fetch_kofia_posts)

    # 7) 캠퍼스리쿠르팅
    run_step('CampusRecruitment', fetch_campus_recruitment)

    # --- 새로운 UID를 data.json에 추가 ---
    add_new_uids()
