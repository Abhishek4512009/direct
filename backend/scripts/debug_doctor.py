
import asyncio
from scraper import MoviesdaScraper
import json

async def debug_doctor():
    scraper = MoviesdaScraper()
    
    # 1. Level 3: Qualities
    # URL found from logs or expected URL for Doctor movie
    # Log said: Fetching: https://moviesda15.com/doctor-2021-movie/
    movie_url = "https://moviesda15.com/doctor-2021-movie/" 
    print(f"--- Level 3: Qualities ({movie_url}) ---")
    qualities = await scraper.get_qualities(movie_url)
    print(json.dumps(qualities, indent=2))
    
    if not qualities.get('qualities'):
        print("No qualities found.")
        return

    # 2. Level 4: Files (for 'Original')
    # Typically first quality
    q_link = qualities['qualities'][0]['link']
    print(f"\n--- Level 4: Files ({q_link}) ---")
    files = await scraper.get_files(q_link)
    print(json.dumps(files, indent=2))
    
    if not files:
        print("No files found.")
        return

    # 3. Level 5: Servers (or Sub-files?)
    # Pick the first file
    f_link = files[0]['link']
    print(f"\n--- Level 5: Servers? ({f_link}) ---")
    servers = await scraper.get_servers(f_link)
    print(json.dumps(servers, indent=2))
    
    if not servers:
        print("No servers found. Checking if it's a sub-directory...")
        soup = await scraper._get_soup(f_link)
        # Dump links to see what's actually there
        print("Links on page:")
        for a in soup.find_all('a'):
            print(f" - {a.get_text(strip=True)} -> {a.get('href')}")


if __name__ == "__main__":
    asyncio.run(debug_doctor())
