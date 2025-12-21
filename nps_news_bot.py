import os
import requests
import time
import csv
from datetime import datetime
from email.utils import parsedate_to_datetime

# 환경 변수 로드
NAVER_ID = os.environ.get('NAVER_CLIENT_ID')
NAVER_SECRET = os.environ.get('NAVER_CLIENT_SECRET')
TG_TOKEN = os.environ.get('TELEGRAM_TOKEN')
TG_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

KEYWORD = '"국민연금" "김성주"'
CSV_FILE = "news_history.csv" # 이제 이 파일이 중복 여부의 기준이 됩니다

def get_processed_links():
    """기존에 처리된 기사 링크들을 CSV에서 읽어옵니다."""
    links = set()
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, mode='r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            next(reader, None) # 헤더 건너뛰기
            for row in reader:
                if len(row) > 2: # URL 컬럼 추출
                    links.add(row[2])
    return links

def save_to_csv(data):
    """기사 정보를 CSV에 누적 저장"""
    file_exists = os.path.isfile(CSV_FILE)
    with open(CSV_FILE, mode='a', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['Date', 'Title', 'URL'])
        writer.writerow(data)

def clean_html(text):
    if not text: return ""
    return text.replace('<b>', '').replace('</b>', '').replace('&quot;', '"').replace('&apos;', "'").replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')

def format_date(date_str):
    try:
        dt = parsedate_to_datetime(date_str)
        return dt.strftime('%Y-%m-%d %H:%M')
    except: return date_str

def main():
    # 1. 이미 처리한 기사 목록 불러오기
    processed_links = get_processed_links()

    # 2. 네이버 API 호출 (최대 100개로 범위 확장)
    url = f"https://openapi.naver.com/v1/search/news.json?query={KEYWORD}&display=100&sort=date"
    headers = {"X-Naver-Client-Id": NAVER_ID, "X-Naver-Client-Secret": NAVER_SECRET}
    
    try:
        res = requests.get(url, headers=headers).json()
        items = res.get('items', [])
    except Exception as e:
        print(f"네이버 API 호출 실패: {e}")
        return

    # 3. 새로운 기사만 필터링 (CSV에 없는 링크만 추출)
    new_articles = []
    for item in items:
        if item['link'] not in processed_links:
            new_articles.append(item)
    
    # 오래된 기사부터 알림이 오도록 순서 뒤집기
    new_articles.reverse()

    # 4. 새 기사 알림 및 저장
    for article in new_articles:
        title = clean_html(article['title'])
        pub_date = format_date(article['pubDate'])
        
        message = (
            f"📢 **NPS 새 기사 알림**\n\n"
            f"📌 **제목:** {title}\n"
            f"⏰ **발표:** {pub_date}\n"
            f"🔗 **링크:** {article['link']}"
        )
        
        # 텔레그램 전송
        send_url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
        requests.get(send_url, params={"chat_id": TG_CHAT_ID, "text": message, "parse_mode": "Markdown"})
        
        # CSV에 즉시 저장하여 다음 실행 때 중복 안 되게 함
        save_to_csv([pub_date, title, article['link']])
        time.sleep(1) # 전송 간격 조절

    print(f"처리 완료: 새 기사 {len(new_articles)}건 발견")

if __name__ == "__main__":
    main()
