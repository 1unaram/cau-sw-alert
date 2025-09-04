# CAU SW Notice - 자동 실행 설정

## 자동 설정 (권장)

```bash
chmod +x setup.sh
./setup.sh
```

이 명령으로 모든 설정이 자동 완료됩니다:

-   필요한 Python 패키지 설치
-   초기화 실행 (init.py)
-   **api_keys.env 파일 생성** (API 키 설정 필요)
-   crontab에 3시간마다 실행하는 작업 자동 등록

## ⚠️ API 키 설정 (필수)

설정 완료 후 `api_keys.env` 파일을 편집하여 실제 API 키를 입력하세요:

```bash
vim api_keys.env
```

필요한 값:

-   **NOTION_API_KEY**: https://www.notion.so/my-integrations 에서 생성
-   **DATABASE_ID**: Notion 데이터베이스 URL에서 복사

## 수동 crontab 관리

### crontab 제거

```bash
chmod +x remove_cron.sh
./remove_cron.sh
```

### 현재 crontab 확인

```bash
crontab -l
```

## 로그 확인

-   `cron.log`: crontab 실행 로그 (표준 출력)
-   `app_cron.log`: run_app.sh 실행 로그
-   `log.log`: 애플리케이션 로그
-   `error.log`: 에러 로그

## 실행 주기 변경

crontab 항목을 수정하려면:

1. `./remove_cron.sh`로 기존 항목 제거
2. `setup.sh`에서 CRON_JOB 변수 수정
3. `./setup.sh` 재실행

### 시간 설정 예시

-   `0 */3 * * *`: 3시간마다 (현재 설정)
-   `0 */6 * * *`: 6시간마다
-   `0 9,15,21 * * *`: 매일 9시, 15시, 21시에만
-   `0 0 * * *`: 매일 자정에
