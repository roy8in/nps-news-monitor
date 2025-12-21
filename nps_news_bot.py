import os
import requests
import time
import csv
import json
from datetime import datetime
from email.utils import parsedate_to_datetime

# 환경 변수 로드
NAVER_ID = os.environ.get('NAVER_CLIENT_ID')
NAVER_SECRET = os.environ.get('NAVER_CLIENT_SECRET')
TG_TOKEN = os.environ.get('TELEGRAM_TOKEN')
TG_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

KEYWORD = '"국민연금" "김성주"'
FILE_PATH = "last_link.txt"
CSV_FILE = "news_history.csv"

def analyze_with_gemini(title, description):
    """
    모든 경로 문제를 우회하기 위해 가장 안정적인 v1 주소를 사용하며, 
    실패 시 대체 모델을 시도하는 강인한 로직입니다.
    """
    # 1. 가장 표준적인 v1 API 주소를 사용합니다.
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    headers = {'Content-Type': 'application/json'}
    prompt = f"뉴스 제목: {title}\n내용: {description}\n위 기사를 이사장 관점에서 우호/중립/부정 중 하나로 판별하고 3줄 요약해줘."
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }

    try:
        # 첫 번째 시도: gemini-1.5-flash
        response = requests.post(url, headers=headers, json=payload)
        
        # 만약 404가 뜬다면, 모델명을 'gemini-pro'로 바꿔서 한 번 더 시도합니다.
        if response.status_code == 404:
            print("⚠️ Flash 모델을 찾을 수 없어 Pro 모델로 재시도합니다.")
            alt_url = url.replace("gemini-1.5-flash", "gemini-pro")
            response = requests.post(alt_url, headers=headers, json=payload)

        res_json = response.json()
        
        # 정상 응답 시 텍스트 추출
        if 'candidates' in res_json:
            content = res_json['candidates'][0]['content']['parts'][0]['text']
            sentiment = "중립"
            if any(x in content for x in ["우호", "긍정", "좋음"]): sentiment = "우호"
            elif any(x in content for x in ["부정", "비판", "나쁨"]): sentiment = "부정"
            return content, sentiment
        else:
            print(f"❌ API 응답 오류: {res_json}")
            return "AI 분석 실패 (형식 오류)", "중립"

    except Exception as e:
        print(f"❌ 네트워크 에러: {e}")
        return "AI 분석 실패 (연결 오류)", "중립"
        
# --- 아래는 기존과 동일하지만 데이터 저장을 위해 최적화됨 ---

def save_to_csv(data):
    file_exists = os.path.isfile(CSV_FILE)
    with open(CSV_FILE, mode='a', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['Date', 'Title', 'URL', 'Sentiment'])
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
    search_url = f"https://openapi.naver.com/v1/search/news.json?query={KEYWORD}&display=10&sort=date"
    headers = {"X-Naver-Client-Id": NAVER_ID, "X-Naver-Client-Secret": NAVER_SECRET}
    
    res = requests.get(search_url, headers=headers).json()
    items = res.get('items', [])
    if not items: return

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
        description = clean_html(article['description'])
        
        ai_briefing, sentiment = analyze_with_gemini(title, description)
        
        message = f"🚨 **NPS CEO AI 브리핑**\n\n📌 **제목:** {title}\n{ai_briefing}\n\n⏰ **발표:** {pub_date}\n🔗 **링크:** {article['link']}"
        
        send_url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
        requests.get(send_url, params={"chat_id": TG_CHAT_ID, "text": message, "parse_mode": "Markdown"})
        
        save_to_csv([pub_date, title, article['link'], sentiment])
        time.sleep(1)

    if items:
        with open(FILE_PATH, "w") as f: f.write(items[0]['link'])

if __name__ == "__main__":
    main()
