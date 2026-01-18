from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from .scraper import MoviesdaScraper
from .indexer import MovieIndexer
from typing import List, Optional
import asyncio

app = FastAPI(title="MoviesDA Streaming API")

# Enable CORS for frontend (Vite defaults to localhost:5173)
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
    # Start background indexing task
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
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/details")
async def get_movie_details(movie_url: str):
    """Get quality variants/files for a movie"""
    try:
        data = await scraper.get_qualities(movie_url)
        # Return just the qualities list for compatibility, 
        # or return the whole object if frontend updates. 
        # For now, let's return the list to be safe.
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
        # Enable recursive depth for deep traversal
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
    """
    try:
        # 1. Get qualities
        data = await scraper.get_qualities(movie_url)
        qualities = data.get('qualities', [])
        
        if not qualities:
            raise HTTPException(status_code=404, detail="No qualities found")
        
        # 2. Sort by quality preference (Explicit Hierarchy)
        # We want to find the BEST quality.
        # Priority: 1080p > 720p > 640 > 480 > Original (Original can be anything, sometimes low quality cam)
        quality_priority = ['1080', '720', '640', '480', 'original', 'hd']
        
        selected_quality = None
        
        # Try to find the highest priority match
        for priority in quality_priority:
            for q in qualities:
                if priority in q['name'].lower():
                    selected_quality = q
                    break
            if selected_quality:
                break
        
        # Fallback if no specific quality found in names, take the LAST one (often highest quality in these lists)
        # or the first if list is short. Actually, typically bottom one is best in sorted lists, but let's stick to first if no match.
        if not selected_quality:
             selected_quality = qualities[0]

        print(f"Selected Quality: {selected_quality['name']}")
        
        # 3. Get files
        files = await scraper.get_files(selected_quality['link'])
        if not files:
            raise HTTPException(status_code=404, detail="No files found")
        
        # Pick non-sample file AND sort by quality (Level 4 Resolution Check)
        # Often Level 4 contains ["Movie 360p", "Movie 1080p"] etc. We must pick the best one.
        non_sample_files = [f for f in files if "sample" not in f['name'].lower()]
        
        if not non_sample_files:
             # Fallback if only samples exist
             selected_file = files[0] # Just take the first one
        else:
             # Apply Priority Sorting to Level 4 items
             # We reuse the same priority list but apply it to the file list
             # 1080p > 720p > 640 > 480 > Original > HD > 360
             
             # Note: 'Original' usually appears at Level 3. At Level 4 we see explicit resolutions.
             l4_quality_priority = ['1080', '720', '640', '480', 'original', 'hd'] 
             
             best_file = None
             for priority in l4_quality_priority:
                 for f in non_sample_files:
                     if priority in f['name'].lower():
                         best_file = f
                         break
                 if best_file:
                     break
             
             if best_file:
                 selected_file = best_file
             else:
                 # If no priority keyword matched, just take the first one (or maybe the last one? typically list is desc or asc)
                 # Let's take the first non-sample one.
                 selected_file = non_sample_files[0]
        
        print(f"Selected File (Level 4): {selected_file['name']}")
        
        # 4. Get Servers (which might actually be the file list in deeper hierarchies)
        servers = await scraper.get_servers(selected_file['link'])
        if not servers:
            raise HTTPException(status_code=404, detail="No servers found")

        # Filter out samples from SERVERS/FILES list too
        # In deep hierarchies, 'files' were folders, and 'servers' are the actual files (e.g. "Movie.mp4", "Movie Sample.mp4")
        non_sample_servers = [s for s in servers if "sample" not in s['server'].lower()]
        
        if not non_sample_servers:
             # Fallback if only samples exist
             target_server = servers[0]
        else:
             target_server = non_sample_servers[0]
        
        print(f"Selected Server/File: {target_server['server']}")

        # 5. Get Stream Link
        final_link = await scraper.resolve_final_link(target_server['link'], depth=0)
        
        if not final_link:
            raise HTTPException(status_code=404, detail="Could not resolve final link")
        
        return {
            "stream_url": final_link,
            "quality": selected_quality['name'],
            "filename": selected_file['name'],
            "poster": data.get('meta', {}).get('poster'),
            "desc": data.get('meta', {}).get('desc')
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
