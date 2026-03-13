import json
import re
import urllib.request
import ssl
from datetime import datetime

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

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

def clean_text(text):
    text = re.sub(r'<[^>]+>', '', text)
    text = text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
    return re.sub(r'\s+', ' ', text).strip()

def parse_date(text):
    match = re.search(r'(\d{4})[-.](\d{1,2})[-.](\d{1,2})', text)
    if match:
        return f"{match.group(1)}-{int(match.group(2)):02d}-{int(match.group(3)):02d}"
    return "9999-12-31"

def extract_titles_arko():
    url = "https://www.arko.or.kr/board/list/4013?bid=463"
    html = fetch_html(url)
    results = []
    
    items = re.findall(r'<li>\s*<a href="(/board/view/[^"]+)">(.*?)</a>\s*</li>', html, re.DOTALL)
    for link, content in items:
        title_match = re.search(r'<span[^>]*class="tit"[^>]*>(.*?)</span>', content, re.DOTALL)
        if title_match:
            title = clean_text(title_match.group(1))
            if "결과" in title or "상세보기" in title or len(title) < 5:
                continue
            
            # Extract date from con/text if available, otherwise fallback
            date_text = re.search(r'(\d{4}[-.]\d{1,2}[-.]\d{1,2})', content)
            deadline = date_text.group(1) if date_text else "9999-12-31"
            results.append({"source": "한국문화예술위원회", "title": title, "deadline": parse_date(deadline)})
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
            if "결과" in title or len(title) < 5:
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
                if not any(x in title for x in ["결과", "선정", "종료", "안내"]):
                    date_match = re.search(r'(\d{4}\.\d{2}\.\d{2})', item)
                    deadline = date_match.group(1) if date_match else "9999-12-31"
                    results.append({"source": "경기문화재단", "title": title, "deadline": parse_date(deadline)})
    return results

def extract_titles_artnuri():
    url = "https://artnuri.or.kr/crawler/info/search.do?docid=&source=&pageSetting=1&sc_seNo=&key=2301170002&sc_orderBy=endDt&recordCountPerPage=100&pageIndex=1&sc_hash=&sc_list=&seNo=&sw=&sc_genre=%EC%8B%9C%EA%B0%81%EC%98%88%EC%88%A0&sc_genre=%EB%8B%A4%EC%9B%90%EC%98%88%EC%88%A0&sc_target=&sc_local=%EC%84%9C%EC%9A%B8&sc_local=%EA%B2%BD%EA%B8%B0&sc_field=&sc_isDo=I&sc_isDo=T&sc_isDo=U"
    html = fetch_html(url)
    results = []
    
    # Artnuri items usually in <li> or similar inside a list container
    items = re.findall(r'<li>(.*?)</li>', html, re.DOTALL)
    for item in items:
        title_match = re.search(r'<a[^>]*class="title"[^>]*>(.*?)</a>', item, re.DOTALL)
        if title_match:
            title = clean_text(title_match.group(1))
            date_match = re.search(r'마감일.*?<dd>(.*?)</dd>', item, re.DOTALL)
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
