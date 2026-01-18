from scraper import MoviesdaScraper
import sys

def test_search_direct(query):
    scraper = MoviesdaScraper()
    # Force resolve first
    scraper.get_years()
    print(f"Resolved Base: {scraper.resolved_base}")
    
    # Try multiple common search patterns on the resolved domain
    patterns = [
        f"{scraper.resolved_base}/index.php?s={query}",
        f"{scraper.resolved_base}/?s={query}",
        f"{scraper.resolved_base}/search?q={query}",
        f"https://www.google.com/search?q=site:{scraper.resolved_base}+{query}" 
    ]
    
    for url in patterns:
        print(f"\nTesting: {url}")
        try:
            # We use scraper.client to keep headers
            resp = scraper.client.get(url)
            print(f"Status: {resp.status_code}")
            if "Amaran" in resp.text:
                print("SUCCESS: Found query in response text")
                # write to file to inspect
                with open("search_result.html", "w", encoding="utf-8") as f:
                    f.write(resp.text)
                return
            else:
                 print("Query not found in response")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    test_search_direct("Amaran")
