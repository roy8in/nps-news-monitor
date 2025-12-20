import os
import requests
import time

NAVER_ID = os.environ.get('NAVER_CLIENT_ID')
NAVER_SECRET = os.environ.get('NAVER_CLIENT_SECRET')
TG_TOKEN = os.environ.get('TELEGRAM_TOKEN')
TG_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

# 검색어 최적화: 반드시 '국민연금'과 '김성주'가 포함된 결과만
KEYWORD = '"국민연금" "김성주"' 
FILE_PATH = "last_link.txt"

def get_news_list():
    # 최근 10개의 기사를 가져옴 (누락 방지)
    url = f"https://openapi.naver.com/v1/search/news.json?query={KEYWORD}&display=10&sort=date"
    headers = {"X-Naver-Client-Id": NAVER_ID, "X-Naver-Client-Secret": NAVER_SECRET}
    try:
        res = requests.get(url, headers=headers).json()
        return res.get('items', [])
    except Exception as e:
        print(f"Error: {e}")
        return []

def main():
    items = get_news_list()
    if not items:
        return

    # 저장된 마지막 기사 링크 읽기
    if os.path.exists(FILE_PATH):
        with open(FILE_PATH, "r") as f:
            last_link = f.read().strip()
    else:
        last_link = ""

    new_articles = []
    for item in items:
        if item['link'] == last_link:
            break  # 저장된 링크를 만나면 그 이후는 이미 본 기사임
        new_articles.append(item)

    # 기사가 거꾸로(최신순) 나열되어 있으므로, 오래된 것부터 알림 보내기 위해 뒤집음
    new_articles.reverse()

    for article in new_articles:
        title = article['title'].replace('<b>', '').replace('</b>', '').replace('&quot;', '"')
        msg = f"📢 NPS CEO 기사 알림\n\n제목: {title}\n링크: {article['link']}"
        
        send_url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
        requests.get(send_url, params={"chat_id": TG_CHAT_ID, "text": msg})
        time.sleep(1) # 텔레그램 도배 방지 짧은 대기

    # 가장 최신 기사의 링크를 파일에 저장
    if new_articles:
        with open(FILE_PATH, "w") as f:
            f.write(items[0]['link'])
        print(f"{len(new_articles)}개의 새로운 기사 발견!")
    else:
        print("새로운 기사 없음.")

if __name__ == "__main__":
    main()
