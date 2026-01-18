import httpx
from bs4 import BeautifulSoup
import re

url = "https://gotopage.xyz/?ref=2026"
print(f"Fetching {url}")
resp = httpx.get(url, follow_redirects=True)
print(f"Final URL: {resp.url}")
print(f"Status: {resp.status_code}")

soup = BeautifulSoup(resp.text, 'html.parser')
meta = soup.find('meta', attrs={'http-equiv': re.compile("refresh", re.I)})
if meta:
    print(f"Meta Refresh Found: {meta}")
    content = meta.get('content', '')
    if 'url=' in content.lower():
        next_url = content.split('url=')[-1].strip()
        print(f"Target URL: {next_url}")
else:
    print("No Meta Refresh found.")
