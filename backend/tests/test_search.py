from scraper import MoviesdaScraper
import sys

def test_search(query):
    scraper = MoviesdaScraper()
    # Resolve base URL first
    scraper.get_years() 
    print(f"Base URL: {scraper.resolved_base}")
    
    # Try pattern 1: /?s=
    search_url = f"{scraper.resolved_base}/?s={query}"
    print(f"Testing: {search_url}")
    try:
        soup = scraper._get_soup(search_url)
        # Check if we get results. 
        # Usually results are in similar divs as movies
        blocks = soup.find_all('div', class_='f')
        if not blocks:
            blocks = soup.find_all('a')
            
        found = False
        for b in blocks[:10]:
            a = b if b.name == 'a' else b.find('a')
            if a:
                print(f"Result: {a.get_text(strip=True)} -> {a['href']}")
                found = True
        
        if found:
            print("Search Pattern 1 seems successful")
            return
            
    except Exception as e:
        print(f"Error: {e}")

    # Try pattern 2: /search?q=
    search_url = f"{scraper.resolved_base}/index.php?s={query}"
    print(f"Testing: {search_url}")
    try:
        soup = scraper._get_soup(search_url)
        found = False
        for a in soup.find_all('a')[:10]:
             print(f"Result: {a.get_text(strip=True)}")
             if query.lower() in a.get_text(strip=True).lower():
                 found = True
        if found: print("index.php?s= worked")
    except:
        pass

if __name__ == "__main__":
    test_search("Amararan") # Using likely keyword
