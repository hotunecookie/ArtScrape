import json
import re
import urllib.request
import ssl
from datetime import datetime

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# 관심 없는 공고 키워드 (대관, 공실 등)
EXCLUSION_KEYWORDS = ["대관", "공실", "세미나실", "교육실", "연습실", "갤러리카페", "카페대관"]

def fetch_html(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache',
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        res = urllib.request.urlopen(req, context=ctx, timeout=15)
        return res.read().decode('utf-8')
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return ""

def strip_tags(text):
    # Just remove tags, keep all content
    return re.sub(r'<[^>]+>', ' ', text)

def clean_text(text):
    # Remove status spans like <span class="status-진">진</span> or <span class="state-st2 ...">...</span>
    # These often contain "진", "예", "미" etc.
    text = re.sub(r'<span[^>]*class="[^"]*(status|state)[^"]*"[^>]*>.*?</span>', '', text, flags=re.IGNORECASE)
    # Remove remaining HTML tags
    text = re.sub(r'<[^>]+>', ' ', text)
    # Replace whitespace/newlines
    text = text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Remove starting prefixes like "진 ", "예 ", "미 ", "2026년 "
    text = re.sub(r'^(진|예|미|진행중|예정|마감)\s+', '', text)
    text = re.sub(r'^\d{4}년?\s*', '', text) 
    # Remove common repetitive words
    text = text.replace("수시대관", "").replace("정기대관", "").strip()
    return text.strip()

def should_exclude(title):
    return any(keyword in title for keyword in EXCLUSION_KEYWORDS)

def parse_date(text):
    if not text: return "9999-12-31"
    # Just remove tags
    text = strip_tags(text)
    
    # YYYY-MM-DD or YYYY.MM.DD
    match = re.search(r'(\d{4})[-.](\d{1,2})[-.](\d{1,2})', text)
    if match:
        return f"{match.group(1)}-{int(match.group(2)):02d}-{int(match.group(3)):02d}"
    
    # YYYY년 MM월 DD일
    match = re.search(r'(\d{4})\s*년\s*(\d{1,2})\s*월\s*(\d{1,2})\s*일', text)
    if match:
        return f"{match.group(1)}-{int(match.group(2)):02d}-{int(match.group(3)):02d}"
        
    return "9999-12-31"

def extract_titles_arko():
    url = "https://www.arko.or.kr/board/list/4013?bid=463"
    html = fetch_html(url)
    results = []
    
    # <li> 안에 <a> 가 있고 제목은 <span class="tit">
    items = re.findall(r'<li>\s*<a[^>]*>(.*?)</a>\s*</li>', html, re.DOTALL)
    for content in items:
        title_match = re.search(r'<span[^>]*class="tit"[^>]*>(.*?)</span>', content, re.DOTALL)
        if title_match:
            title = clean_text(title_match.group(1))
            if not title or len(title) < 5 or any(x in title for x in ["결과", "기록물", "선정"]):
                continue
            if should_exclude(title):
                continue
            
            # 날짜 추출: .con 에 기간 정보가 있는 경우가 많음
            deadline = "9999-12-31"
            date_matches = re.findall(r'(\d{4}[-.]\d{1,2}[-.]\d{1,2})|(\d{4}\s*년\s*\d{1,2}\s*월\s*\d{1,2}\s*일)', content)
            if date_matches:
                all_found = []
                for m1, m2 in date_matches:
                    dm = m1 if m1 else m2
                    all_found.append(parse_date(dm))
                deadline = max(all_found) if all_found else "9999-12-31"
            
            results.append({"source": "한국문화예술위원회", "title": title, "deadline": deadline})
    return results

def extract_titles_sfac():
    url = "https://www.sfac.or.kr/participation/participation/artspace_project.do?searchSttusCd=1"
    html = fetch_html(url)
    results = []
    
    items = re.findall(r'<li>(.*?)</li>', html, re.DOTALL)
    for item in items:
        title_match = re.search(r'<p[^>]*class="[^"]*tit[^"]*"[^>]*>(.*?)</p>', item, re.DOTALL)
        if not title_match:
             title_match = re.search(r'<p[^>]*class="[^"]*program-title[^"]*"[^>]*>(.*?)</p>', item, re.DOTALL)
        
        if title_match:
            title = clean_text(title_match.group(1))
            if "결과" in title or len(title) < 5 or should_exclude(title):
                continue
            # SFAC list doesn't show deadline, using far future for sorting if not found
            results.append({"source": "서울문화재단", "title": title, "deadline": "9999-12-31"})
    return results

def extract_titles_ggcf():
    url = "https://www.ggcf.kr/boards/businessNotices/articles"
    html = fetch_html(url)
    results = []
    
    items = re.findall(r'<div[^>]*class="list__left[^>]*>(.*?)</div>', html, re.DOTALL)
    for item in items:
        if "ing" in item or "진행" in item:
            title_match = re.search(r'<p[^>]*class="[^"]*tit[^"]*"[^>]*>(.*?)</p>', item, re.DOTALL)
            if title_match:
                title = clean_text(title_match.group(1))
                if not any(x in title for x in ["결과", "선정", "종료", "안내"]) and not should_exclude(title):
                    date_match = re.search(r'(\d{4}\.\d{2}\.\d.2})', item)
                    deadline = date_match.group(1) if date_match else "9999-12-31"
                    results.append({"source": "경기문화재단", "title": title, "deadline": parse_date(deadline)})
    return results

def extract_titles_artnuri():
    url = "https://artnuri.or.kr/crawler/info/search.do?docid=&source=&pageSetting=1&sc_seNo=&key=2301170002&sc_orderBy=endDt&recordCountPerPage=100&pageIndex=1&sc_hash=&sc_list=&seNo=&sw=&sc_genre=%EC%8B%9C%EA%B0%81%EC%98%88%EC%88%A0&sc_genre=%EB%8B%A4%EC%9B%90%EC%98%88%EC%88%A0&sc_target=&sc_local=%EC%84%9C%EC%9A%B8&sc_local=%EA%B2%BD%EA%B8%B0&sc_field=&sc_isDo=I&sc_isDo=T&sc_isDo=U"
    html = fetch_html(url)
    results = []
    
    seen_titles = set()
    for match in re.finditer(r'<a[^>]*class="title"[^>]*>(.*?)</a>', html, re.DOTALL):
        title_raw = match.group(1)
        title = clean_text(title_raw)
        if not title or len(title) < 3 or title in seen_titles or should_exclude(title): continue
        seen_titles.add(title)
        
        # 타이틀 주변 (뒤쪽 1000자)에서 마감일 검색
        context = html[match.end():match.end()+1000]
        date_match = re.search(r'마감일.*?<em>(.*?)</em>', context, re.DOTALL)
        deadline = date_match.group(1) if date_match else "9999-12-31"
        
        results.append({"source": "아트누리", "title": title, "deadline": parse_date(deadline)})
    return results

def main():
    print("Scraping started...")
    all_items = []
    
    all_items.extend(extract_titles_arko())
    all_items.extend(extract_titles_sfac())
    all_items.extend(extract_titles_ggcf())
    all_items.extend(extract_titles_artnuri())
    
    # Sort by deadline (closest first)
    # 9999-12-31 will be at the end
    sorted_items = sorted(all_items, key=lambda x: x['deadline'])
    
    if not sorted_items:
        combined_text = "현재 수집된 진행중/예정 지원사업이 없습니다."
    else:
        formatted = []
        for idx, item in enumerate(sorted_items):
            date_str = f" [마감: {item['deadline']}]" if item['deadline'] != "9999-12-31" else " [마감: 미정]"
            formatted.append(f"{idx+1}. [{item['source']}] {item['title']}{date_str}")
        combined_text = "\n".join(formatted)

    print(combined_text)
    
    data = {"text": combined_text}
    with open("news.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("Saved to news.json")

if __name__ == "__main__":
    main()
