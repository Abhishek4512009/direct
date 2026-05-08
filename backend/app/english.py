import httpx
from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/api/english", tags=["English Movies & Series"])

CINEMETA_BASE = "https://v3-cinemeta.strem.io"

async def fetch_cinemeta(path: str) -> dict:
    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            response = await client.get(f"{CINEMETA_BASE}{path}")
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Cinemeta error: {str(e)}")

def get_movie_streams(imdb_id: str):
    if not imdb_id: return []
    return [
        {"name": "VidSrc", "url": f"https://vidsrc.me/embed/movie?imdb={imdb_id}"},
        {"name": "VidAPI", "url": f"https://vidapi.xyz/embed/movie/{imdb_id}"},
        {"name": "AutoEmbed", "url": f"https://autoembed.co/movie/imdb/{imdb_id}"},
        {"name": "SuperEmbed", "url": f"https://multiembed.mov/directstream.php?video_id={imdb_id}"}
    ]

def get_episode_streams(imdb_id: str, season: int, episode: int):
    if not imdb_id: return []
    return [
        {"name": "VidSrc", "url": f"https://vidsrc.me/embed/tv?imdb={imdb_id}&season={season}&episode={episode}"},
        {"name": "VidAPI", "url": f"https://vidapi.xyz/embed/tv/{imdb_id}/{season}/{episode}"},
        {"name": "AutoEmbed", "url": f"https://autoembed.co/tv/imdb/{imdb_id}-{season}-{episode}"},
        {"name": "SuperEmbed", "url": f"https://multiembed.mov/directstream.php?video_id={imdb_id}&s={season}&e={episode}"}
    ]

def format_meta(item: dict, item_type: str = "movie") -> dict:
    imdb_id = item.get("imdb_id") or item.get("id", "")
    base = {
        "id": imdb_id,
        "type": item_type,
        "title": item.get("name"),
        "year": item.get("year"),
        "rating": item.get("imdbRating"),
        "runtime": item.get("runtime"),
        "genres": item.get("genres", []),
        "description": item.get("description"),
        "cast": item.get("cast", []),
        "director": item.get("director", []),
        "poster": item.get("poster"),
        "backdrop": item.get("background"),
        "logo": item.get("logo"),
    }

    if item_type == "movie":
        base["streams"] = get_movie_streams(imdb_id)
    elif item_type == "series":
        # Format episodes
        raw_vids = item.get("videos", [])
        episodes = []
        for v in raw_vids:
            season = v.get("season", 1)
            episode = v.get("episode", 1)
            ep_id = v.get("id", "")
            ep_name = v.get("title") or v.get("name") or f"Episode {episode}"
            episodes.append({
                "id": ep_id,
                "season": season,
                "episode": episode,
                "title": ep_name,
                "released": v.get("released"),
                "thumbnail": v.get("thumbnail"),
                "overview": v.get("overview"),
                "streams": get_episode_streams(imdb_id, season, episode)
            })
        base["episodes"] = episodes

    return base

# --- MOVIES (Backwards compatible roots) ---
@router.get("/popular")
@router.get("/movies/popular")
async def get_popular_movies(skip: int = Query(0, ge=0)):
    data = await fetch_cinemeta(f"/catalog/movie/popular/skip={skip}.json")
    return {"skip": skip, "has_more": data.get("hasMore", False), "results": [format_meta(m, "movie") for m in data.get("metas", [])]}

@router.get("/top")
@router.get("/movies/top")
async def get_top_movies(skip: int = Query(0, ge=0)):
    data = await fetch_cinemeta(f"/catalog/movie/top/skip={skip}.json")
    return {"skip": skip, "has_more": data.get("hasMore", False), "results": [format_meta(m, "movie") for m in data.get("metas", [])]}

@router.get("/search")
@router.get("/movies/search")
async def search_movies(q: str = Query(...)):
    data = await fetch_cinemeta(f"/catalog/movie/top/search={q}.json")
    return {"query": q, "results": [format_meta(m, "movie") for m in data.get("metas", [])]}

@router.get("/movie/{imdb_id}")
async def get_movie_detail(imdb_id: str):
    data = await fetch_cinemeta(f"/meta/movie/{imdb_id}.json")
    if not data.get("meta"): raise HTTPException(404, "Movie not found")
    return format_meta(data["meta"], "movie")


# --- SERIES ---
@router.get("/series/popular")
async def get_popular_series(skip: int = Query(0, ge=0)):
    data = await fetch_cinemeta(f"/catalog/series/popular/skip={skip}.json")
    return {"skip": skip, "has_more": data.get("hasMore", False), "results": [format_meta(m, "series") for m in data.get("metas", [])]}

@router.get("/series/top")
async def get_top_series(skip: int = Query(0, ge=0)):
    data = await fetch_cinemeta(f"/catalog/series/top/skip={skip}.json")
    return {"skip": skip, "has_more": data.get("hasMore", False), "results": [format_meta(m, "series") for m in data.get("metas", [])]}

@router.get("/series/search")
async def search_series(q: str = Query(...)):
    data = await fetch_cinemeta(f"/catalog/series/top/search={q}.json")
    return {"query": q, "results": [format_meta(m, "series") for m in data.get("metas", [])]}

@router.get("/series/{imdb_id}")
async def get_series_detail(imdb_id: str):
    data = await fetch_cinemeta(f"/meta/series/{imdb_id}.json")
    if not data.get("meta"): raise HTTPException(404, "Series not found")
    return format_meta(data["meta"], "series")

# --- UTILS ---
@router.get("/genres")
async def get_genres():
    return {"genres": ["action","adventure","animation","biography","comedy","crime","documentary","drama","family","fantasy","history","horror","music","mystery","romance","sci-fi","sport","thriller","war","western"]}
