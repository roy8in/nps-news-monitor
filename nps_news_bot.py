import os
import requests
import time
import google.generativeai as genai
from datetime import datetime
from email.utils import parsedate_to_datetime

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
    """Gemini를 이용한 기사 감성 분석 및 3줄 요약"""
    prompt = f"""
    당신은 홍보실의 전문 뉴스 분석관입니다. 
    아래 뉴스 정보를 바탕으로 이사장님(김성주)에 대한 기사의 우호도를 판별하고 3줄 요약을 작성하세요.
    
    기사 제목: {title}
    네이버 요약: {description}

    형식:
    📊 감성: [우호 / 중립 / 부정 중 택1] (적절한 이모지 포함)
    📝 AI 3줄 브리핑:
    1. (핵심 내용 한 줄)
    2. (핵심 내용 한 줄)
    3. (핵심 내용 한 줄)
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"AI 분석 중 오류가 발생했습니다: {e}"

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
    url = f"https://openapi.naver.com/v1/search/news.json?query={KEYWORD}&display=10&sort=date"
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
        time.sleep(1)

    if items:
        with open(FILE_PATH, "w") as f:
            f.write(items[0]['link'])

if __name__ == "__main__":
    main()
