import asyncio
from scraper import MoviesdaScraper

async def debug_api_logic():
    scraper = MoviesdaScraper()
    print("Fetching years...")
    years = await scraper.get_years()
    year_2026 = next((y for y in years if "2026" in y['name']), None)
    
    if not year_2026:
        print("2026 not found in years")
        return
        
    print(f"Testing API logic for: {year_2026['name']} ({year_2026['link']})")
    
    # Replicate api.py get_movies logic EXACTLY
    pages = 3
    year_url = year_2026['link']
    
    try:
        all_movies = []
        base_url = year_url.rstrip('/')
        
        for page_num in range(1, pages + 1):
            if page_num == 1:
                current_url = base_url
            else:
                current_url = f"{base_url}/?page={page_num}"
            
            print(f"Processing API Page {page_num}: {current_url}")
            try:
                movies = await scraper.get_movies_in_year(current_url)
                print(f"   - Scraper returned {len(movies)} raw items")
                
                # Filter out navigation links (contain "Movies" in title usually)
                # print sample raw titles
                for m in movies[:3]:
                    print(f"     Raw: {m['title'].encode('ascii', 'replace')}")
                    
                filtered_movies = [m for m in movies if not m['title'].startswith('Tamil') and 'Movies' not in m['title']]
                print(f"   - After API Filter: {len(filtered_movies)} items")
                
                all_movies.extend(filtered_movies)
            except Exception as e:
                print(f"   - EXCEPTION in page loop: {e}")
                break  # Stop if page doesn't exist
        
        print(f"Final Movie Count: {len(all_movies)}")
        
    except Exception as e:
        print(f"Top Level Exception: {e}")

if __name__ == "__main__":
    asyncio.run(debug_api_logic())
