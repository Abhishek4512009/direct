import asyncio
from scraper import MoviesdaScraper
import json

async def inspect_level4():
    scraper = MoviesdaScraper()
    print("Fetching movie data...")
    
    # Let's try to get a specific movie we know has multiple qualities
    # We'll search for one or just traverse to one.
    # Let's use the 2023 list again as it was successfully found before.
    
    years = await scraper.get_years()
    year_2023 = next((y for y in years if "2023" in y['name']), None)
    movies = await scraper.get_movies_in_year(year_2023['link'])
    
    # Pick the first movie
    target_movie = movies[0] 
    print(f"Target Movie: {target_movie['title']}")
    
    # Level 3: Qualities
    qualities = await scraper.get_qualities(target_movie['link'])
    print(f"Level 3 (Qualities): {[q['name'] for q in qualities]}")
    
    selected_quality = qualities[0] # Usually 'Original'
    print(f"Selected Level 3: {selected_quality['name']}")
    
    # Level 4: "Files" (Actually Resolution Folders)
    level4_items = await scraper.get_files(selected_quality['link'])
    
    print("\n--- Level 4 Items (Order preserved) ---")
    for i, item in enumerate(level4_items):
        print(f"[{i}] {item['name']}")
        
    # Check if my current logic (index 0) would pick the wrong one
    print(f"\nCurrent Logic would pick: {level4_items[0]['name']}")

if __name__ == "__main__":
    asyncio.run(inspect_level4())
