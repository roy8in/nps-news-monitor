import re
import html

def clean_html(text):
    if not text: return ""
    text = html.unescape(text) # &quot;, &amp; 등 HTML 엔티티 일괄 처리
    text = re.sub(r'<[^>]+>', '', text) # 남아있는 HTML 태그 전부 제거
    return text.strip()

print(clean_html("&#39;국민연금 이사장 김성주&#39;"))
