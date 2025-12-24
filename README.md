# CAU SW Notice

중앙대학교 소프트웨어학부 공지사항 자동 수집 → Notion 데이터베이스 업로드

## 📋 수집 대상

-   소프트웨어학부: 공지사항, 취업정보, 공모전
-   SW교육원: 공지사항
-   산업보안학과: 공지사항

## 🚀 빠른 시작

### 1. 초기 설정

```bash
chmod +x setup.sh
./setup.sh
```

### 2. API 키 설정

`notion_keys.env` 파일 편집:

```bash
NOTION_API_KEY=your_notion_api_key      # https://www.notion.so/my-integrations
PARENT_PAGE_ID=your_parent_page_id      # 데이터베이스를 생성할 페이지 ID
PERSON_ID=your_person_id                # (선택) 알림받을 사용자 ID
DATABASE_ID=                            # 자동 생성됨
```

### 3. 완료

-   데이터베이스가 자동 생성되고 `DATABASE_ID`가 저장됩니다
-   crontab에 자동 등록되어 6, 9, 12, 15, 18, 21시에 실행됩니다

## 📁 프로젝트 구조

```
cau-sw-notice/
├── app/
│   ├── app.py          # 메인 크롤링 스크립트
│   └── notion.py       # Notion API (DB 생성 + 페이지 추가)
├── setup.sh            # 초기 설정 스크립트
├── run_app.sh          # 앱 실행 스크립트 (cron용)
├── remove_cron.sh      # crontab 제거 스크립트
├── data.json           # 수집된 게시물 ID 저장
└── notion_keys.env     # API 키 설정 파일
```

## 🔧 관리 명령어

### 수동 실행

```bash
python3 app/app.py
```

### crontab 제거

```bash
./remove_cron.sh
```

### crontab 확인

```bash
crontab -l
```

### 실행 주기 변경

`setup.sh`의 `CRON_JOB` 변수 수정 후 재실행

```bash
# 예시
0 */3 * * *        # 3시간마다
0 9,15,21 * * *    # 9시, 15시, 21시
```

## 📝 로그

-   `cron.log`: 전체 실행 로그
