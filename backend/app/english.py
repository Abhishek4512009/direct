import httpx
from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/api/english", tags=["English Movies"])

CINEMETA_BASE = "https://v3-cinemeta.strem.io"

async def fetch_cinemeta(path: str) -> dict:
    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            response = await client.get(f"{CINEMETA_BASE}{path}")
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Cinemeta error: {str(e)}")

def format_movie(movie: dict) -> dict:
    imdb_id = movie.get("imdb_id") or movie.get("id", "")
    return {
        "id": imdb_id,
        "title": movie.get("name"),
        "year": movie.get("year"),
        "rating": movie.get("imdbRating"),
        "runtime": movie.get("runtime"),
        "genres": movie.get("genres", []),
        "description": movie.get("description"),
        "cast": movie.get("cast", []),
        "director": movie.get("director", []),
        "poster": movie.get("poster"),
        "backdrop": movie.get("background"),
        "logo": movie.get("logo"),
        "trailers": movie.get("trailerStreams", []),
        "streams": [
            {"name": "VidSrc", "url": f"https://vidsrc.me/embed/movie?imdb={imdb_id}"},
            {"name": "VidLink", "url": f"https://vidlink.pro/movie/{imdb_id}"}
        ] if imdb_id else []
    }

@router.get("/popular")
async def get_popular_movies(skip: int = Query(0, ge=0)):
    data = await fetch_cinemeta(f"/catalog/movie/popular/skip={skip}.json")
    movies = data.get("metas", [])
    return {"skip": skip, "has_more": data.get("hasMore", False), "results": [format_movie(m) for m in movies]}

@router.get("/top")
async def get_top_movies(skip: int = Query(0, ge=0)):
    data = await fetch_cinemeta(f"/catalog/movie/top/skip={skip}.json")
    movies = data.get("metas", [])
    return {"skip": skip, "has_more": data.get("hasMore", False), "results": [format_movie(m) for m in movies]}

@router.get("/genre/{genre}")
async def get_movies_by_genre(genre: str, skip: int = Query(0, ge=0)):
    data = await fetch_cinemeta(f"/catalog/movie/top/genre={genre}&skip={skip}.json")
    movies = data.get("metas", [])
    return {"genre": genre, "skip": skip, "has_more": data.get("hasMore", False), "results": [format_movie(m) for m in movies]}

@router.get("/search")
async def search_movies(q: str = Query(..., description="Movie title to search")):
    # Cinemeta search catalog format
    data = await fetch_cinemeta(f"/catalog/movie/top/search={q}.json")
    movies = data.get("metas", [])
    return {"query": q, "results": [format_movie(m) for m in movies]}

@router.get("/movie/{imdb_id}")
async def get_movie_detail(imdb_id: str):
    data = await fetch_cinemeta(f"/meta/movie/{imdb_id}.json")
    meta = data.get("meta")
    if not meta:
        raise HTTPException(status_code=404, detail="Movie not found")
    return format_movie(meta)

@router.get("/genres")
async def get_genres():
    return {"genres": ["action","adventure","animation","biography","comedy","crime","documentary","drama","family","fantasy","history","horror","music","mystery","romance","sci-fi","sport","thriller","war","western"]}

@router.get("/test")
async def test_connection():
    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            response = await client.get(f"{CINEMETA_BASE}/catalog/movie/popular/skip=0.json")
            data = response.json()
            movie_count = len(data.get("metas", []))
            return {"status": "ok", "cinemeta_reachable": True, "sample_count": movie_count}
    except Exception as e:
        return {"status": "error", "cinemeta_reachable": False, "detail": str(e)}
