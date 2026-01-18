import asyncio
from scraper import MoviesdaScraper
import json

async def inspect_2023():
    scraper = MoviesdaScraper()
    print("Fetching 2023 movies...")
    # 1. Get 2023 Page
    years = await scraper.get_years()
    year_2023 = next((y for y in years if "2023" in y['name']), None)
    
    if not year_2023:
        print("Could not find 2023 year page.")
        return

    print(f"Found 2023 Page: {year_2023['link']}")
    
    # 2. Get Movies from 2023
    movies = await scraper.get_movies_in_year(year_2023['link'])
    if not movies:
        print("No movies found in 2023.")
        return
        
    target_movie = movies[0] # Pick first one
    print(f"Inspecting Movie: {target_movie['title']} -> {target_movie['link']}")
    
    # 3. Get Qualities
    qualities = await scraper.get_qualities(target_movie['link'])
    print("\nQualities found:")
    for q in qualities:
        print(f" - {q['name']} -> {q['link']}")
        
    if not qualities:
        return

    # 4. Inspect Files (which are actually sub-qualities/folders)
    for q in qualities:
        print(f"\nSub-folders/Files for quality: {q['name']}")
        sub_items = await scraper.get_files(q['link'])
        for item in sub_items:
            print(f"   Name: '{item['name']}' | Link: ...{item['link'][-30:]}")
            
            # Drill down into one of them (e.g. 720p)
            if "720" in item['name']:
                 print(f"   DRILLING DOWN into: {item['name']}")
                 # These should be the actual files
                 potential_files = await scraper.get_servers(item['link'])
                 for pf in potential_files:
                      print(f"      [Potential File/Server]: {pf.get('server')} -> ...{pf.get('link')[-30:]}")
                      if "sample" in pf.get('server', '').lower():
                           print("      [DETECTED SAMPLE]")

if __name__ == "__main__":
    asyncio.run(inspect_2023())
