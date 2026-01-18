import sys
import codecs
import asyncio
from scraper import MoviesdaScraper

# Force UTF-8 for Windows console
if sys.platform == "win32":
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

async def inspect():
    scraper = MoviesdaScraper()
    # We need a sample movie URL. Let's get one from 2026 list.
    print("Fetching 2026 list...")
    movies = await scraper.get_movies_in_year("https://gotopage.xyz/?ref=2026")
    
    
    # Filter for the specific movie user showed: "Central"
    valid_movies = [m for m in movies if 'central' in m['title'].lower()]
    
    if not valid_movies:
        print("Movie 'Central' not found in 2026/2025 list. Inspecting first valid movie instead.")
        valid_movies = [m for m in movies if '(' in m['title'] or '202' in m['title']]

    if not valid_movies:
        return

    target_movie = valid_movies[0]
    print(f"Inspecting: {target_movie['title']} -> {target_movie['link']}")
    
    soup = await scraper._get_soup(target_movie['link'])
    
    # Dump relevant parts
    print("\n--- Searching for Images ---")
    for img in soup.find_all('img'):
        print(f"IMG: {img.get('src', '')} | Alt: {img.get('alt', '')} | Class: {img.get('class', '')}")
        
    print("\n--- Searching for Description/Synopsis ---")
    # Dump all text to find where the description is hiding
    body = soup.find('body')
    if body:
        text = body.get_text(separator='|', strip=True)
        # Print first 2000 chars to see structure
        print(f"BODY TEXT DUMP: {text[:2000]}")
        
    for div in soup.find_all('div'):
        t = div.get_text(strip=True)
        if len(t) > 50 and len(t) < 500:
            print(f"Candidate DIV: {t}")

if __name__ == "__main__":
    asyncio.run(inspect())
