from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from .scraper import MoviesdaScraper
from .indexer import MovieIndexer
from typing import List, Optional
from app.english import router as english_router
import asyncio
import re

app = FastAPI(title="MoviesDA Streaming API")
app.include_router(english_router)
# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development, allow all. In prod, lock this down.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize scraper and indexer
scraper = MoviesdaScraper()
indexer = MovieIndexer()

@app.on_event("startup")
async def startup_event():
    # Start background indexing task only
    asyncio.create_task(indexer.start_indexing())

@app.get("/")
async def health_check():
    return {"status": "ok", "message": "MoviesDA API is running"}

@app.get("/api/search")
async def search_movies(q: str):
    """Search for movies across all indexed categories"""
    return await indexer.search(q)

@app.get("/api/years")
async def get_years():
    """Get list of year categories"""
    try:
        return await scraper.get_years()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/movies")
async def get_movies(year_url: str, pages: int = 3):
    """Get movies for a specific year category URL, aggregating multiple pages"""
    try:
        all_movies = []
        base_url = year_url
        if not base_url.endswith('/'):
            base_url += '/'
        
        for page_num in range(1, pages + 1):
            if page_num == 1:
                current_url = base_url
            else:
                separator = "?" if base_url.endswith('/') else "/?"
                current_url = f"{base_url}{separator}page={page_num}"
            
            try:
                movies = await scraper.get_movies_in_year(current_url)
                # Filter out navigation links (contain "Movies" in title usually)
                movies = [m for m in movies if not m['title'].startswith('Tamil') and 'Movies' not in m['title']]
                all_movies.extend(movies)
            except Exception:
                break  # Stop if page doesn't exist
        
        # Enrich with local metadata (Posters/Desc) if available
        all_movies = await indexer.enrich_metadata(all_movies)
        
        return all_movies
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"CRITICAL ERROR in get_movies: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/details")
async def get_movie_details(movie_url: str):
    """Get quality variants/files for a movie"""
    try:
        data = await scraper.get_qualities(movie_url)
        return data.get('qualities', [])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/files")
async def get_files(quality_url: str):
    try:
        return await scraper.get_files(quality_url)
    except Exception as e:
         raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stream")
async def get_stream_link(file_url: str):
    """
    Get the final direct download link for a file page.
    This performs the server traversal (Level 6 & 7).
    """
    try:
        # 1. Get servers
        servers = await scraper.get_servers(file_url)
        if not servers:
             raise HTTPException(status_code=404, detail="No download servers found")
        
        # 2. Pick the first server (usually best)
        target_server = servers[0]
        
        # 3. Resolve
        final_link = await scraper.resolve_final_link(target_server['link'], depth=0)
        
        if not final_link:
             raise HTTPException(status_code=404, detail="Could not resolve final link")
             
        return {"stream_url": final_link}
    except Exception as e:
         raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/auto-stream")
async def get_auto_stream(movie_url: str):
    """
    Automatically resolve the best quality stream for a movie.
    Prefers 1080p > 720p > other qualities.
    Refined to pick the LARGEST file size at the final level (Size-Optimized).
    """
    try:
        # 1. Get qualities (Level 3)
        data = await scraper.get_qualities(movie_url)
        qualities = data.get('qualities', [])
        
        if not qualities:
            raise HTTPException(status_code=404, detail="No qualities found")
        
        # 2. Sort by quality preference (Level 3 Priority)
        quality_priority = ['1080', '720', '640', '480', 'original', 'hd']
        selected_quality = None
        
        for priority in quality_priority:
            for q in qualities:
                if priority in q['name'].lower():
                    selected_quality = q
                    break
            if selected_quality:
                break
        
        if not selected_quality:
             selected_quality = qualities[0]

        print(f"Selected Quality: {selected_quality['name']}")
        
        # 3. Get files (Level 4)
        files = await scraper.get_files(selected_quality['link'])
        if not files:
            raise HTTPException(status_code=404, detail="No files found")
        
        # Filter samples and Sort Level 4 items
        non_sample_files = [f for f in files if "sample" not in f['name'].lower()]
        candidates_l4 = non_sample_files if non_sample_files else files
             
        # Apply Priority Sorting to Level 4 items
        l4_quality_priority = ['1080', '720', '640', '480', 'original', 'hd'] 
        selected_file = None
        
        for priority in l4_quality_priority:
            for f in candidates_l4:
                if priority in f['name'].lower():
                    selected_file = f
                    break
            if selected_file:
                break
        
        if not selected_file:
            selected_file = candidates_l4[0]
        
        print(f"Selected File (Level 4): {selected_file['name']}")
        
        # 4. Get Servers (Level 5) - SIZE BASED SORTING
        servers = await scraper.get_servers(selected_file['link'])
        if not servers:
            raise HTTPException(status_code=404, detail="No servers found")

        non_sample_servers = [s for s in servers if "sample" not in s['server'].lower()]
        candidates_l5 = non_sample_servers if non_sample_servers else servers
        
        # --- SIZE SORTER HELPER ---
        def parse_size_mb(text):
            """Extracts size (e.g. '2.4 GB') and converts to MB for comparison."""
            match = re.search(r'(\d+(?:\.\d+)?)\s*(GB|MB)', text, re.IGNORECASE)
            if not match:
                return 0.0 
            
            val = float(match.group(1))
            unit = match.group(2).upper()
            
            if unit == 'GB':
                return val * 1024 
            return val 
        # --------------------------

        target_server = max(candidates_l5, key=lambda s: parse_size_mb(s['server']))
        
        print(f"Selected Server/File: {target_server['server']} (Size-Optimized)")

        # 5. Get Stream Link
        final_link = await scraper.resolve_final_link(target_server['link'], depth=0)
        
        if not final_link:
            raise HTTPException(status_code=404, detail="Could not resolve final link")
        
        return {
            "stream_url": final_link,
            "quality": selected_quality['name'],
            "filename": selected_file['name'],
            "server_label": target_server['server'],
            "poster": data.get('meta', {}).get('poster'),
            "desc": data.get('meta', {}).get('desc')
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in auto-stream: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
    
