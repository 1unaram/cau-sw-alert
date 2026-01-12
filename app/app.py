import datetime
import json
from turtle import title

import requests
from bs4 import BeautifulSoup
from notion import create_page_to_database

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
        print(f"❌ [{datetime.datetime.now()}] Error updating data.json: {str(e)}")


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
        print(f"❌ [{datetime.datetime.now()}] Error reading data.json: {str(e)}")
        existing_uids = set()



def fetch_kofia_posts():
    global existing_uids, new_uids

    base_url = 'https://www.kofia.or.kr/brd/m_96/list.do'

    response = requests.get(base_url)
    response.encoding = 'utf-8'

    if response.status_code != 200:
        print(f"❌ [{datetime.datetime.now()}] KOFIA fetch failed: {response.status_code}")
    else:
        html = response.text
        soup = BeautifulSoup(html, 'html.parser')
        table = soup.find('table', class_='common2 mgb25')
        rows = table.find_all('tr')[1:]

        data = {}
        for row in rows:
            cols = row.find_all('td')

            # [1] 번호
            uid = 'KOFIA' + cols[0].text.strip()
            if uid in existing_uids:
                continue

            # [2] 회사명
            company = cols[1].text.strip()

            # [3] 제목
            title = cols[2].text.strip()

            # [3] URL
            post_url = base_url + cols[2].find('a')['href']

            # [4] 날짜
            date = cols[4].get_text(strip=True)

            data[uid] = {
                'title': title,
                'url': post_url,
                'date': datetime.datetime.strptime(date, '%Y-%m-%d').date().isoformat()
            }
            new_uids.add(uid)

        if data:
            for item in data.keys():
                create_page_to_database(data[item], 'KOFIA')


def fetch_is_posts(type):
    global existing_uids, new_uids

    url = 'https://security.cau.ac.kr/board.htm?bbsid=notice'

    response = requests.get(url)
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
                'date': datetime.datetime.strptime(date, '%Y.%m.%d').date().isoformat()
            }
            new_uids.add(uid)

        if data:
            for item in data.keys():
                create_page_to_database(data[item], type)


def fetch_posts(type):
    global existing_uids, new_uids

    url = ''
    if type == 'Notice':
        url = 'https://cse.cau.ac.kr/sub05/sub0501.php'
    elif type == 'Employment':
        url = 'https://cse.cau.ac.kr/sub05/sub0502.php'
    elif type == 'Contest':
        url = 'https://cse.cau.ac.kr/sub05/sub0506.php'

    response = requests.get(url)
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
                'date': datetime.datetime.strptime(date, '%Y.%m.%d').date().isoformat()
            }
            new_uids.add(uid)

        if data:
            for item in data.keys():
                create_page_to_database(data[item], type)


def fetch_swedu(type):
    global existing_uids, new_uids

    base_url = 'https://swedu.cau.ac.kr/board'
    url = base_url + '/list?boardtypeid=7&menuid=001005005'

    response = requests.get(url)
    response.encoding = 'utf-8'

    if response.status_code != 200:
        print(f"❌ [{datetime.datetime.now()}] SWEdu fetch failed: {response.status_code}")
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
                'date': datetime.datetime.strptime(date, '%Y-%m-%d').date().isoformat()
            }
            new_uids.add(uid)

        if data:
            for item in data.keys():
                create_page_to_database(data[item], type)


if __name__ == "__main__":

    fetch_previous_data()

    # 소프트웨어학부 공지사항
    fetch_posts('Notice')

    # 소프트웨어학부 취업정보
    fetch_posts('Employment')

    # 소프트웨어학부 공모전 소식
    fetch_posts('Contest')

    # SW교육원 공지사항
    fetch_swedu('SWEdu')

    # 산업보안학과 공지사항
    fetch_is_posts('ISNotice')

    # 금융투자협회 채용 공고
    fetch_kofia_posts()

    add_new_uids()
