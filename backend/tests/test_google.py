import httpx
from bs4 import BeautifulSoup
import urllib.parse
import time

def test_google(query):
    domain = "moviesda15.com"
    # q=site:domain+query
    url = f"https://www.google.com/search?q=site:{domain}+{query}&hl=en"
    print(f"Fetching: {url}")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
    }
    
    try:
        resp = httpx.get(url, headers=headers)
        print(f"Status: {resp.status_code}")
        
        if resp.status_code == 429:
             print("Too Many Requests (CAPTCHA)")
             return
             
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Google search results are usually in div.g > div > div > a
        # Or h3 for titles
        
        found_any = False
        for a in soup.find_all('a'):
            href = a.get('href', '')
            # Extract real URL if it's a google redirect? 
            # Modern google search results often contain direct links in href for main results
            
            if domain in href and "google" not in href:
                 title_tag = a.find('h3')
                 if title_tag:
                     print(f"Result: {title_tag.get_text()} -> {href}")
                     found_any = True
        
        if not found_any:
            print("No results found parsing standard selectors.")
            # debug dump
            # with open("google_debug.html", "w", encoding="utf-8") as f: f.write(resp.text)

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_google("Amaran")
