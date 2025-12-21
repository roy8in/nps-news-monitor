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
FILE_PATH = "last_link.txt"
CSV_FILE = "news_history.csv"

def save_to_csv(data):
    """기사 정보를 CSV에 누적 저장"""
    file_exists = os.path.isfile(CSV_FILE)
    with open(CSV_FILE, mode='a', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['Date', 'Title', 'URL']) # 감성 항목 제외
        writer.writerow(data)

def clean_html(text):
    """HTML 태그 제거"""
    if not text: return ""
    return text.replace('<b>', '').replace('</b>', '').replace('&quot;', '"').replace('&apos;', "'").replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')

def format_date(date_str):
    """날짜 형식 변환"""
    try:
        dt = parsedate_to_datetime(date_str)
        return dt.strftime('%Y-%m-%d %H:%M')
    except: return date_str

def main():
    url = f"https://openapi.naver.com/v1/search/news.json?query={KEYWORD}&display=50&sort=date"
    headers = {"X-Naver-Client-Id": NAVER_ID, "X-Naver-Client-Secret": NAVER_SECRET}
    
    try:
        res = requests.get(url, headers=headers).json()
        items = res.get('items', [])
    except Exception as e:
        print(f"네이버 API 호출 실패: {e}")
        return

    if not items: return

    # 마지막 기사 링크 확인
    last_link = ""
    if os.path.exists(FILE_PATH):
        with open(FILE_PATH, "r") as f: last_link = f.read().strip()

    new_articles = []
    for item in items:
        if item['link'] == last_link: break
        new_articles.append(item)
    
    new_articles.reverse()

    for article in new_articles:
        title = clean_html(article['title'])
        pub_date = format_date(article['pubDate'])
        
        # 텔레그램 메시지 구성 (심플 버전)
        message = (
            f"📢 **NPS 새 기사 알림**\n\n"
            f"📌 **제목:** {title}\n"
            f"⏰ **발표:** {pub_date}\n"
            f"🔗 **링크:** {article['link']}"
        )
        
        # 텔레그램 전송
        send_url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
        requests.get(send_url, params={"chat_id": TG_CHAT_ID, "text": message, "parse_mode": "Markdown"})
        
        # CSV 데이터 저장
        save_to_csv([pub_date, title, article['link']])
        time.sleep(1)

    # 마지막 기사 업데이트
    if items:
        with open(FILE_PATH, "w") as f: f.write(items[0]['link'])

if __name__ == "__main__":
    main()
