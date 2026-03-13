import urllib.request
import re
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

url = 'https://artnuri.or.kr/crawler/info/search.do?docid=&source=&pageSetting=1&sc_seNo=&key=2301170002&sc_orderBy=endDt&recordCountPerPage=5&pageIndex=1&sc_hash=&sc_list=&seNo=&sw=&sc_genre=%EC%8B%9C%EA%B0%81%EC%98%88%EC%88%A0&sc_genre=%EB%8B%A4%EC%9B%90%EC%98%88%EC%88%A0&sc_target=&sc_local=%EC%84%9C%EC%9A%B8&sc_local=%EA%B2%BD%EA%B8%B0&sc_field=&sc_isDo=I&sc_isDo=T&sc_isDo=U'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})

try:
    res = urllib.request.urlopen(req, context=ctx, timeout=5)
    html = res.read().decode('utf-8')
    
    # Save HTML to file to inspect it
    with open('artnuri_debug.html', 'w', encoding='utf-8') as f:
        f.write(html)
        
    titles = re.findall(r'<div class="box_text">.*?<strong class="tit">(.*?)</strong>', html, re.DOTALL)
    if not titles:
        titles = re.findall(r'<p class="tit">(.*?)</p>', html, re.DOTALL)
    if not titles:
        titles = re.findall(r'<p class="board_tit.*?>(.*?)</p>', html, re.DOTALL)
    if not titles:
        titles = re.findall(r'<div class="title.*?>(.*?)</div>', html, re.DOTALL)
    if not titles:
        titles = re.findall(r'<strong class="tit.*?>(.*?)</strong>', html, re.DOTALL)
    if not titles:
        titles = re.findall(r'<a[^>]*class="title"[^>]*>(.*?)</a>', html, re.DOTALL)
        
    print(f"Found {len(titles)} items.")
    for t in titles[:5]:
        clean_t = re.sub(r'<[^>]+>', '', t).strip()
        print('-', clean_t.replace('\n', '').replace('\t', '').replace('\r', ''))
except Exception as e:
    print('Error:', e)
