import os
import requests
import time
from datetime import datetime
from email.utils import parsedate_to_datetime

# 환경 변수 로드
NAVER_ID = os.environ.get('NAVER_CLIENT_ID')
NAVER_SECRET = os.environ.get('NAVER_CLIENT_SECRET')
TG_TOKEN = os.environ.get('TELEGRAM_TOKEN')
TG_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

KEYWORD = '"국민연금" "김성주"'
FILE_PATH = "last_link.txt"

def format_date(date_str):
    """네이버의 RFC 822 날짜 형식을 '2025-12-21 14:30' 형태로 변환"""
    try:
        dt = parsedate_to_datetime(date_str)
        return dt.strftime('%Y-%m-%d %H:%M')
    except:
        return date_str

def clean_html(text):
    """HTML 태그 및 특수문자 제거"""
    if not text: return ""
    return text.replace('<b>', '').replace('</b>', '').replace('&quot;', '"').replace('&apos;', "'").replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')

def main():
    url = f"https://openapi.naver.com/v1/search/news.json?query={KEYWORD}&display=10&sort=date"
    headers = {"X-Naver-Client-Id": NAVER_ID, "X-Naver-Client-Secret": NAVER_SECRET}
    
    try:
        res = requests.get(url, headers=headers).json()
        items = res.get('items', [])
    except Exception as e:
        print(f"API 요청 에러: {e}")
        return

    if not items:
        return

    # 마지막 링크 읽기
    if not os.path.exists(FILE_PATH):
        last_link = ""
    else:
        with open(FILE_PATH, "r") as f:
            last_link = f.read().strip()

    new_articles = []
    for item in items:
        if item['link'] == last_link:
            break
        new_articles.append(item)
    
    new_articles.reverse()

    for article in new_articles:
        title = clean_html(article['title'])
        pub_date = format_date(article['pubDate'])
        description = clean_html(article['description']) # 요약 내용 (기자/언론사 정보 포함 가능성 높음)
        link = article['link']
        
        # 메시지 구성
        message = (
            f"🚨 **NPS CEO 새 기사 알림**\n\n"
            f"📌 **제목:** {title}\n"
            f"⏰ **시간:** {pub_date}\n"
            f"📝 **요약:** {description}...\n"
            f"🔗 **링크:** {link}"
        )
        
        send_url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
        requests.get(send_url, params={"chat_id": TG_CHAT_ID, "text": message, "parse_mode": "Markdown"})
        time.sleep(1)

    if items:
        with open(FILE_PATH, "w") as f:
            f.write(items[0]['link'])

if __name__ == "__main__":
    main()
