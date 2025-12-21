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
    """라이브러리 없이 직접 Gemini API를 호출하는 가장 확실한 방법"""
    # v1beta 주소를 사용하여 모델 인식 오류를 원천 차단합니다.
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    headers = {'Content-Type': 'application/json'}
    
    prompt = f"""
    당신은 홍보실 뉴스 분석 전문가입니다. 아래 뉴스를 분석해 감성과 3줄 요약을 작성하세요.
    반드시 아래 형식을 엄격히 지켜주세요.
    
    [감성]: 우호, 중립, 부정 중 하나를 선택
    [요약]:
    1. 핵심내용
    2. 핵심내용
    3. 핵심내용

    뉴스 제목: {title}
    뉴스 내용: {description}
    """
    
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        res_json = response.json()
        
        # API 응답에서 텍스트만 추출
        content = res_json['candidates'][0]['content']['parts'][0]['text']
        
        sentiment = "중립"
        if "우호" in content or "긍정" in content: sentiment = "우호"
        elif "부정" in content or "비판" in content: sentiment = "부정"
            
        return content, sentiment
    except Exception as e:
        # 에러 발생 시 서버 응답 전문을 출력하여 디버깅을 돕습니다.
        print(f"⚠️ Gemini API 호출 에러 상세: {response.text if 'response' in locals() else e}")
        return "AI 분석 실패 (API 응답 오류)", "중립"

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
