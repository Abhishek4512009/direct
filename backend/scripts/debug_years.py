import asyncio
from scraper import MoviesdaScraper
import re

async def debug_years():
    scraper = MoviesdaScraper()
    print("Fetching home page...")
    soup = await scraper._get_soup(scraper.base_url)
    
    print("\n--- All Links on Home Page ---")
    found_years = []
    for a in soup.find_all('a'):
        text = a.get_text(strip=True)
        href = a.get('href')
        print(f"Text: '{text}' | Href: '{href}'")
        
        if re.search(r'\d{4}\s+Movies', text, re.IGNORECASE):
             print("   [MATCHED REGEX]")
             found_years.append(text)
        else:
             pass
             
    print(f"\nTotal Years Matched: {len(found_years)}")
    print(f"List: {found_years}")

if __name__ == "__main__":
    asyncio.run(debug_years())
