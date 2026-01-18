import asyncio
import os
import sys
from .scraper import MoviesdaScraper
from typing import List, Dict, Optional
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Force UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = "moviesda_db"
COLLECTION_NAME = "movies"

class MovieIndexer:
    def __init__(self):
        self.scraper = MoviesdaScraper()
        self.client = None
        self.db = None
        self.collection = None
        self.is_indexing = False
        
        if MONGO_URI:
            try:
                self.client = AsyncIOMotorClient(MONGO_URI)
                self.db = self.client[DB_NAME]
                self.collection = self.db[COLLECTION_NAME]
                print("Indexer: Connected to MongoDB.")
            except Exception as e:
                print(f"Indexer: Failed to connect to MongoDB: {e}")
        else:
            print("Indexer: WARNING - MONGO_URI not found. Indexing will not be persisted.")

    async def start_indexing(self):
        """Main indexing loop."""
        if self.is_indexing:
            print("Indexer: Already running.")
            return

        if not self.collection:
            print("Indexer: No MongoDB connection. Skipping indexing.")
            return

        self.is_indexing = True
        print("Indexer: Starting background indexing...")
        
        try:
            # 1. Get Years
            years = await self.scraper.get_years()
            print(f"Indexer: Found {len(years)} year categories.")

            for year in years:
                print(f"Indexer: Scanning {year['name']}...")
                base_url = year['link']
                
                page = 1
                while True:
                    if page == 1:
                        url = base_url
                    else:
                        separator = "?" if base_url.endswith('/') else "/?"
                        url = f"{base_url}{separator}page={page}"
                    
                    try:
                        movies = await self.scraper.get_movies_in_year(url)
                    except Exception as e:
                        print(f"Indexer: Error scanning {url}: {e}")
                        break

                    if not movies:
                        break

                    # Check for "Sidebar Loop" trap via "look-ahead" existence check?
                    # Simply upserting is safer for now.
                    
                    # Optional: Check if page seems to be duplicate (heuristic)
                    # We skip this for robustness, just re-scan/update.

                    for m in movies:
                        m['year_category'] = year['name']
                        
                        # Deep Indexing
                        try:
                            # Check if we already have detailed info to avoid re-fetching
                            existing = await self.collection.find_one({"link": m['link']})
                            if existing and existing.get('poster'):
                                print(f"   > Skipping deep index for {m['title']} (Already indexed)")
                            else:
                                details = await self.scraper.get_qualities(m['link'])
                                meta = details.get('meta', {})
                                m['poster'] = meta.get('poster')
                                m['desc'] = meta.get('desc')
                                print(f"   > Deep indexed: {m['title']}")
                        except Exception as e:
                            print(f"   > Failed deep index for {m['title']}: {e}")

                        # UPSERT into MongoDB
                        await self.collection.update_one(
                            {'link': m['link']}, 
                            {'$set': m}, 
                            upsert=True
                        )
                    
                    # Polite delay
                    await asyncio.sleep(0.2) 
                    page += 1
            
            print("Indexer: Indexing complete.")

        except Exception as e:
            print(f"Indexer: Critical failure: {e}")
        finally:
            self.is_indexing = False

    async def search(self, query: str) -> List[Dict]:
        """Search via MongoDB regex"""
        if not query or self.collection is None:
            return []
        
        # Simple regex search for title
        cursor = self.collection.find(
            {"title": {"$regex": query, "$options": "i"}}
        ).limit(50)
        
        return await cursor.to_list(length=50)

    async def enrich_metadata(self, movies: List[Dict]) -> List[Dict]:
        """
        Enrich a list of live-scraped movies with metadata from MongoDB
        """
        if self.collection is None:
            return movies
            
        links = [m['link'] for m in movies]
        # Fetch all matching docs
        cursor = self.collection.find({"link": {"$in": links}})
        cached_docs = await cursor.to_list(length=len(links))
        
        cached_map = {d['link']: d for d in cached_docs}
        
        for movie in movies:
            cached = cached_map.get(movie['link'])
            if cached:
                if not movie.get('poster') and cached.get('poster'):
                    movie['poster'] = cached['poster']
                if not movie.get('desc') and cached.get('desc'):
                    movie['desc'] = cached['desc']
        
        return movies
