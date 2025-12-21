import csv
import os
import requests
import time
import google.generativeai as genai
from datetime import datetime
from email.utils import parsedate_to_datetime

CSV_FILE = "news_history.csv"

# 환경 변수 로드
NAVER_ID = os.environ.get('NAVER_CLIENT_ID')
NAVER_SECRET = os.environ.get('NAVER_CLIENT_SECRET')
TG_TOKEN = os.environ.get('TELEGRAM_TOKEN')
TG_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

# Gemini AI 설정
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

KEYWORD = '"국민연금" "김성주"'
FILE_PATH = "last_link.txt"

def analyze_with_gemini(title, description):
    """더 정교해진 AI 분석 및 데이터 추출"""
    # AI에게 답변 형식을 더 엄격하게 요구합니다.
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
    try:
        response = model.generate_content(prompt)
        content = response.text
        
        # 감성 판별 로직 강화 (단어 포함 여부 확인)
        sentiment = "중립"
        if "우호" in content:
            sentiment = "우호"
        elif "부정" in content:
            sentiment = "부정"
            
        return content, sentiment
    except Exception as e:
        # 에러 발생 시 어떤 에러인지 로그에 남깁니다.
        print(f"⚠️ Gemini API 호출 중 상세 에러 발생: {e}")
        return f"AI 분석 실패 (사유: {e})", "중립"

def save_to_csv(data):
    """기사 정보를 CSV에 누적 저장"""
    file_exists = os.path.isfile(CSV_FILE)
    with open(CSV_FILE, mode='a', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['Date', 'Title', 'URL', 'Sentiment']) # 헤더
        writer.writerow(data)

def clean_html(text):
    """HTML 태그 제거 및 특수문자 변환"""
    if not text: return ""
    return text.replace('<b>', '').replace('</b>', '').replace('&quot;', '"').replace('&apos;', "'").replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')

def format_date(date_str):
    """날짜 형식 변환"""
    try:
        dt = parsedate_to_datetime(date_str)
        return dt.strftime('%Y-%m-%d %H:%M')
    except:
        return date_str

def main():
    url = f"https://openapi.naver.com/v1/search/news.json?query={KEYWORD}&display=30&sort=date"
    headers = {"X-Naver-Client-Id": NAVER_ID, "X-Naver-Client-Secret": NAVER_SECRET}
    
    res = requests.get(url, headers=headers).json()
    items = res.get('items', [])
    if not items: return

    if not os.path.exists(FILE_PATH):
        last_link = ""
    else:
        with open(FILE_PATH, "r") as f:
            last_link = f.read().strip()

    new_articles = []
    for item in items:
        if item['link'] == last_link: break
        new_articles.append(item)
    
    new_articles.reverse()

    for article in new_articles:
        title = clean_html(article['title'])
        pub_date = format_date(article['pubDate'])
        description = clean_html(article['description'])
        
        # Gemini 분석 결과와 감성 태그를 받음
        ai_briefing, sentiment = analyze_with_gemini(title, description)
        
        # Gemini AI 분석 호출
        ai_briefing = analyze_with_gemini(title, description)
        
        message = (
            f"🚨 **NPS CEO AI 브리핑**\n\n"
            f"📌 **제목:** {title}\n"
            f"{ai_briefing}\n\n"
            f"⏰ **시간:** {pub_date}\n"
            f"🔗 **링크:** {article['link']}"
        )
        
        send_url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
        requests.get(send_url, params={"chat_id": TG_CHAT_ID, "text": message, "parse_mode": "Markdown"})
        save_to_csv([pub_date, title, article['link'], sentiment])
        time.sleep(1)

    if items:
        with open(FILE_PATH, "w") as f:
            f.write(items[0]['link'])

if __name__ == "__main__":
    main()
