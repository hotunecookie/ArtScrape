import urllib.request
import re
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

url = 'https://www.arko.or.kr/board/list/3148'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})

try:
    res = urllib.request.urlopen(req, context=ctx, timeout=10)
    html = res.read().decode('utf-8')
    with open('arko_debug.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"Downloaded ARKO HTML, length: {len(html)}")
except Exception as e:
    print('Error:', e)
