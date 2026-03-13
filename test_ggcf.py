import urllib.request
import ssl
import re

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def fetch_html(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        res = urllib.request.urlopen(req, context=ctx, timeout=15)
        return res.read().decode('utf-8')
    except Exception as e:
        print(f"Error: {e}")
        return ""

url = "https://www.ggcf.kr/boards/businessNotices/articles"
html = fetch_html(url)
print(f"HTML Length: {len(html)}")

# Test 1: Generic 'tit' class
titles = re.findall(r'<p[^>]*class="tit[^>]*>(.*?)</p>', html, re.DOTALL)
print(f"Test 1 (Generic 'tit' class) found: {len(titles)}")
for t in titles[:5]:
    print(f" - {t[:50]}")

# Test 2: 'list__left' container
items = re.findall(r'<div[^>]*class="list__left[^>]*>(.*?)</div>', html, re.DOTALL)
print(f"Test 2 ('list__left' container) found: {len(items)}")

# Save HTML for inspection
with open("ggcf_debug_test.html", "w", encoding="utf-8") as f:
    f.write(html)
print("Saved HTML to ggcf_debug_test.html")
