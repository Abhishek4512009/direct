import httpx
from bs4 import BeautifulSoup
import urllib.parse

def test_ddg(query):
    # Dork: site:moviesda15.com Amaran
    # We need to dynamically get the domain from scraper, but for test hardcode it or reuse logic
    domain = "moviesda15.com" 
    
    url = f"https://html.duckduckgo.com/html/?q=site:{domain}+{query}"
    print(f"Fetching: {url}")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Referer": "https://html.duckduckgo.com/"
    }
    
    try:
        resp = httpx.get(url, headers=headers)
        print(f"Status: {resp.status_code}")
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # DDG results are in a.result__a
        for a in soup.find_all('a', class_='result__a'):
            title = a.get_text(strip=True)
            link = a['href']
            # DDG wraps links in /l/?kh=-1&uddg=...
            # We need to unwrap or just look at the text
            if "uddg=" in link:
                # Extract real link
                pass
                
            print(f"Found: {title} -> {link}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_ddg("Amaran")
