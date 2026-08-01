import datetime
import os
import re
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# === Test Start ===

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, 'keys.env'))

login_url = 'https://rainbow.cau.ac.kr/site/member/logonnew'
base_url = 'https://rainbow.cau.ac.kr/site/program/recruit/listCampusRecruit'

session = requests.Session()
user_id = os.getenv('C_ID')
user_pw = os.getenv('C_PW')
if user_id and user_pw:
    session.post(
        login_url,
        data={
            'prevurl': '/site/program/recruit/listCampusRecruit',
            'mobileyn': 'N',
            'userid': user_id,
            'userpw': user_pw
        }
    )

response = session.get(base_url)
response.encoding = 'utf-8'

if response.status_code != 200:
    print(f"❌ [{datetime.datetime.now()}] Campus Recruitment fetch failed: {response.status_code}")
elif 'autherror' in response.url or '로그인 해주세요' in response.text:
    print("❌ Campus Recruitment requires login")
    print("   Set C_ID and C_PW in environment (or keys.env) and run again.")
    raise SystemExit(1)
else:
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')
    table = (
        soup.select_one('div.table_style1 table')
        or soup.find('table', class_='table_style1')
    )

    if not table:
        print("❌ Campus Recruitment table not found")
        raise SystemExit(1)

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

    print(f"✅ Parsed {len(data)} campus recruitment rows")
    for item in list(data.values())[:5]:
        print(item)
