
import asyncio
from scraper import MoviesdaScraper
import json
import re

async def debug_2026():
    scraper = MoviesdaScraper()
    # Test WITHOUT trailing slash to simulate frontend behavior
    url = "https://moviesda15.com/tamil-2026-movies" 
    print(f"--- Fetched URL: {url} ---")
    
    # 1. Raw scrape
    movies = await scraper.get_movies_in_year(url)
    print(f"Found {len(movies)} items RAW.")
    for m in movies:
        try:
            print(f" - {m['title']} ({m['link']})")
        except UnicodeEncodeError:
            print(f" - {m['title'].encode('utf-8')} ({m['link']})")
        
    # 2. Replicate API filtering
    filtered = [m for m in movies if not m['title'].startswith('Tamil') and 'Movies' not in m['title']]
    print(f"\n--- Filtered items (as per API) ---")
    print(f"Found {len(filtered)} items.")
    for m in filtered:
        try:
            print(f" - {m['title']}")
        except UnicodeEncodeError:
            print(f" - {m['title'].encode('utf-8')}")

if __name__ == "__main__":
    asyncio.run(debug_2026())
