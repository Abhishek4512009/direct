from scraper import MoviesdaScraper
from bs4 import BeautifulSoup
import urllib.parse
import re

def test_extract_and_search(query):
    scraper = MoviesdaScraper()
    soup = scraper._get_soup(scraper.base_url)
    
    # 1. Extract Content Domain
    content_domain = None
    for a in soup.find_all('a'):
        href = a.get('href', '')
        if 'moviesda' in href or 'isaimini' in href:
            parsed = urllib.parse.urlparse(href)
            if parsed.netloc and parsed.netloc != "gotopage.xyz":
                 content_domain = f"{parsed.scheme}://{parsed.netloc}"
                 print(f"Discovered content domain: {content_domain}")
                 break
    
    if not content_domain:
        print("Could not discover content domain")
        return

    # 2. Try Search on Content Domain
    # Pattern: /index.php?s={query} is most common for these WP-like sites
    search_url = f"{content_domain}/index.php?s={query}"
    print(f"Testing Search: {search_url}")
    
    try:
        resp = scraper.client.get(search_url)
        print(f"Status: {resp.status_code}")
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        found = False
        for a in soup.find_all('a'):
            if query.lower() in a.get_text(strip=True).lower():
                print(f"Found: {a.get_text(strip=True)} -> {a['href']}")
                found = True
        
        if found: 
            print("Search SUCCESS")
        else:
            print("Search FAILED (No results found in links)")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_extract_and_search("Amaran")
