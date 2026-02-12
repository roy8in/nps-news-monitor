import os
import requests
import time
import csv
import difflib
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime

# 환경 변수 로드
NAVER_ID = os.environ.get('NAVER_CLIENT_ID')
NAVER_SECRET = os.environ.get('NAVER_CLIENT_SECRET')
TG_TOKEN = os.environ.get('TELEGRAM_TOKEN')
TG_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

KEYWORD = '"국민연금" "김성주"'
CSV_FILE = "news_history.csv" 

def get_processed_data():
    """
    CSV에서:
    1. 모든 URL (중복 수집 방지용)
    2. 최근 24시간 이내의 기사 제목 (유사도 검사용)
    을 읽어옵니다.
    """
    links = set()
    recent_titles = []
    now = datetime.now()
    
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, mode='r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            next(reader, None) # 헤더 건너뛰기
            for row in reader:
                if len(row) > 2:
                    date_str = row[0]
                    title = row[1]
                    url = row[2]
                    
                    links.add(url)
                    
                    # 24시간 이내 제목만 추출
                    try:
                        # CSV 날짜 포맷: YYYY-MM-DD HH:MM
                        dt = datetime.strptime(date_str, '%Y-%m-%d %H:%M')
                        if (now - dt) <= timedelta(hours=24):
                            recent_titles.append(title)
                    except ValueError:
                        pass # 날짜 파싱 실패 시 무시

    return links, recent_titles

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

def is_similar(new_title, existing_titles, threshold=0.7):
    """새 제목이 기존(최근 24시간) 제목들과 유사한지 검사합니다."""
    for title in existing_titles:
        if difflib.SequenceMatcher(None, new_title, title).ratio() >= threshold:
            return True
    return False

def main():
    # 1. 이미 처리한 기사 목록(URL)과 최근 제목들 불러오기
    processed_links, recent_titles = get_processed_data()

    # 2. 네이버 API 호출
    url = f"https://openapi.naver.com/v1/search/news.json?query={KEYWORD}&display=100&sort=date"
    headers = {"X-Naver-Client-Id": NAVER_ID, "X-Naver-Client-Secret": NAVER_SECRET}
    
    try:
        res = requests.get(url, headers=headers).json()
        items = res.get('items', [])
    except Exception as e:
        print(f"네이버 API 호출 실패: {e}")
        return

    # 3. 새로운 기사만 필터링 (CSV에 없는 URL만 추출)
    new_articles = []
    for item in items:
        if item['link'] not in processed_links:
            new_articles.append(item)
    
    # 오래된 기사부터 알림이 오도록 순서 뒤집기
    new_articles.reverse()

    # 4. 새 기사 처리
    for article in new_articles:
        title = clean_html(article['title'])
        pub_date = format_date(article['pubDate'])
        link = article['link']
        
        # 4-1. 유사도 검사 (최근 24시간 내 기사와 비교)
        if is_similar(title, recent_titles):
            print(f"🚫 유사 기사 저장 (전송 생략): {title}")
            # 전송은 안 하지만, 기록은 남김 (URL 중복 방지 + 히스토리)
            save_to_csv([pub_date, title, link])
            processed_links.add(link)
            # 현재 배치 내 중복 방지를 위해 리스트에도 추가
            recent_titles.append(title)
            continue

        # 4-2. 텔레그램 전송
        message = (
            f"<b>📢 NPS 새 기사 알림</b>\n\n"
            f"📌 <b>제목:</b> {title}\n"
            f"⏰ <b>발표:</b> {pub_date}\n"
            f"🔗 <b>링크:</b> <a href='{link}'>기사 바로가기</a>"
        )
        
        send_url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
        params = {
            "chat_id": TG_CHAT_ID,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": False
        }
        
        try:
            response = requests.get(send_url, params=params)
            if response.status_code == 200:
                # 전송 성공 시 저장
                save_to_csv([pub_date, title, link])
                recent_titles.append(title)
                processed_links.add(link)
            else:
                print(f"전송 실패: {response.text}")
        except Exception as e:
            print(f"전송 중 에러 발생: {e}")

        time.sleep(1)

    print(f"처리 완료: 새 기사 {len(new_articles)}건 발견 (유사 기사 포함)")

if __name__ == "__main__":
    main()