import asyncio
from scraper import MoviesdaScraper
import re

async def debug_2026():
    scraper = MoviesdaScraper()
    print("Fetching 2026 Page...")
    # Get the 2026 link first
    years = await scraper.get_years()
    year_2026 = next((y for y in years if "2026" in y['name']), None)
    
    if not year_2026:
        print("Scraper could NOT find 2026 year entry.")
        return

    print(f"Found 2026 Year: {year_2026['name']} -> {year_2026['link']}")
    
    # Now inspect movies on that page
    print("\nfetching page content...")
    soup = await scraper._get_soup(year_2026['link'])
    
    print("\n--- Inspecting Blocks ---")
    blocks = soup.find_all('div', class_='f')
    if not blocks:
         print("No div.f found, falling back to all links")
         blocks = soup.find_all('a')

    for i, block in enumerate(blocks):
        a_tag = block if block.name == 'a' else block.find('a')
        if not a_tag: continue
        
        text = a_tag.get_text(strip=True)
        href = a_tag.get('href')
        safe_text = text.encode('ascii', 'replace').decode('ascii')
        print(f"[{i}] Text: '{safe_text}' | Href: '{href}'")
        
        # Simulate filter logic
        should_exclude = False
        if not href: should_exclude = True
        elif "page" in href.lower(): should_exclude = True
        elif len(text) <= 1: should_exclude = True
        elif "telegram" in text.lower(): should_exclude = True
        elif "group" in text.lower(): should_exclude = True
        elif "movies" in text.lower() and re.search(r'\d{4}', text):
             if text.lower().startswith("tamil") and text.lower().endswith("movies"):
                  should_exclude = True
                  print("   -> Filtered by Tamil...Movies rule")
             if text.lower().startswith("20") and text.lower().endswith("movies"):
                  should_exclude = True
        
        if should_exclude:
             print("   [EXCLUDED]")
        else:
             print("   [KEPT]")
             
    # Actual scraped result
    print("\n--- Actual Scraper Result ---")
    movies = await scraper.get_movies_in_year(year_2026['link'])
    print(f"Count: {len(movies)}")
    for m in movies:
        print(m)

if __name__ == "__main__":
    asyncio.run(debug_2026())
