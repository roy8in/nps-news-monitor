import os
import requests
import time
import csv
from google import genai  # 최신 SDK 임포트 방식
from datetime import datetime
from email.utils import parsedate_to_datetime

# 환경 변수 로드
NAVER_ID = os.environ.get('NAVER_CLIENT_ID')
NAVER_SECRET = os.environ.get('NAVER_CLIENT_SECRET')
TG_TOKEN = os.environ.get('TELEGRAM_TOKEN')
TG_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

# Gemini 클라이언트 설정
client = genai.Client(
    api_key=GEMINI_API_KEY,
    http_options={'api_version': 'v1'}
)

KEYWORD = '"국민연금" "김성주"'
FILE_PATH = "last_link.txt"
CSV_FILE = "news_history.csv"

def analyze_with_gemini(title, description):
    """Gemini 1.5 Flash 분석 (최적화 버전)"""
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
        # 모델 이름 앞에 'models/'를 붙여 경로를 더 확실히 합니다.
        response = client.models.generate_content(
            model='gemini-1.5-flash', 
            contents=prompt
        )
        
        # 답변이 비어있을 경우를 대비한 안전장치
        if not response or not response.text:
            return "분석 결과 없음", "중립"
            
        content = response.text
        
        sentiment = "중립"
        if "우호" in content or "긍정" in content: sentiment = "우호"
        elif "부정" in content or "비판" in content: sentiment = "부정"
            
        return content, sentiment
    except Exception as e:
        print(f"⚠️ Gemini API 호출 에러 상세: {e}")
        return f"AI 분석 실패 (사유: {e})", "중립"

def save_to_csv(data):
    """기사 정보를 CSV에 누적 저장"""
    file_exists = os.path.isfile(CSV_FILE)
    with open(CSV_FILE, mode='a', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['Date', 'Title', 'URL', 'Sentiment'])
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
    url = f"https://openapi.naver.com/v1/search/news.json?query={KEYWORD}&display=10&sort=date"
    headers = {"X-Naver-Client-Id": NAVER_ID, "X-Naver-Client-Secret": NAVER_SECRET}
    
    res = requests.get(url, headers=headers).json()
    items = res.get('items', [])
    if not items: return

    # 마지막 기사 링크 확인
    last_link = ""
    if os.path.exists(FILE_PATH):
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
        
        # AI 분석 실행
        ai_briefing, sentiment = analyze_with_gemini(title, description)
        
        # 텔레그램 메시지 구성
        message = (
            f"🚨 **NPS CEO AI 브리핑**\n\n"
            f"📌 **제목:** {title}\n"
            f"{ai_briefing}\n\n"
            f"⏰ **발표:** {pub_date}\n"
            f"🔗 **링크:** {article['link']}"
        )
        
        # 텔레그램 전송
        send_url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
        requests.get(send_url, params={"chat_id": TG_CHAT_ID, "text": message, "parse_mode": "Markdown"})
        
        # CSV 데이터 저장
        save_to_csv([pub_date, title, article['link'], sentiment])
        time.sleep(1)

    # 마지막 기사 업데이트
    if items:
        with open(FILE_PATH, "w") as f:
            f.write(items[0]['link'])

if __name__ == "__main__":
    main()
