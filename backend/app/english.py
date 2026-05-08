import httpx
from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/api/english", tags=["English Movies"])

CINEMETA_BASE = "https://v3-cinemeta.strem.io"
VIDSRC_BASE = "https://vidsrc.to/embed"


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
        "stream_url": f"{VIDSRC_BASE}/movie/{imdb_id}" if imdb_id else None,
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

YTS_BASE = "https://yts.mx/api/v2"
VIDSRC_BASE = "https://vidsrc.to/embed"

# ─────────────────────────────────────────
# HELPER
# ─────────────────────────────────────────

async def fetch_yts(endpoint: str, params: dict) -> dict:
    """Call YTS API and return JSON. Raises 502 on failure."""
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(f"{YTS_BASE}/{endpoint}", params=params)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"YTS API error: {str(e)}")


def format_movie(movie: dict) -> dict:
    """Normalize a YTS movie object for the frontend."""
    return {
        "id": movie.get("id"),
        "imdb_id": movie.get("imdb_code"),
        "title": movie.get("title"),
        "year": movie.get("year"),
        "rating": movie.get("rating"),
        "runtime": movie.get("runtime"),
        "genres": movie.get("genres", []),
        "summary": movie.get("summary", ""),
        "language": movie.get("language"),
        "poster": movie.get("large_cover_image"),
        "backdrop": movie.get("background_image_original"),
        "trailer": f"https://www.youtube.com/watch?v={movie.get('yt_trailer_code')}" if movie.get("yt_trailer_code") else None,
        "stream_url": f"{VIDSRC_BASE}/movie/{movie.get('imdb_code')}",
        "qualities": [t.get("quality") for t in movie.get("torrents", [])],
    }


# ─────────────────────────────────────────
# ENDPOINTS
# ─────────────────────────────────────────

@router.get("/popular")
async def get_popular_movies(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=50),
    genre: str = Query(None, description="e.g. action, comedy, drama"),
    rating: float = Query(None, description="Minimum rating e.g. 7.0"),
):
    """
    Get popular English movies sorted by download count.
    Optional filters: genre, minimum rating.
    """
    params = {
        "limit": limit,
        "page": page,
        "sort_by": "download_count",
        "order_by": "desc",
        "quality": "1080p",
    }
    if genre:
        params["genre"] = genre
    if rating:
        params["minimum_rating"] = rating

    data = await fetch_yts("list_movies.json", params)
    movies = data.get("data", {}).get("movies", [])
    total = data.get("data", {}).get("movie_count", 0)

    return {
        "page": page,
        "total": total,
        "results": [format_movie(m) for m in movies],
    }


@router.get("/trending")
async def get_trending_movies(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=50),
):
    """
    Get trending English movies sorted by rating.
    """
    params = {
        "limit": limit,
        "page": page,
        "sort_by": "rating",
        "order_by": "desc",
        "minimum_rating": 7,
        "quality": "1080p",
    }
    data = await fetch_yts("list_movies.json", params)
    movies = data.get("data", {}).get("movies", [])
    total = data.get("data", {}).get("movie_count", 0)

    return {
        "page": page,
        "total": total,
        "results": [format_movie(m) for m in movies],
    }


@router.get("/latest")
async def get_latest_movies(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=50),
):
    """
    Get latest English movies sorted by date added.
    """
    params = {
        "limit": limit,
        "page": page,
        "sort_by": "date_added",
        "order_by": "desc",
        "quality": "1080p",
    }
    data = await fetch_yts("list_movies.json", params)
    movies = data.get("data", {}).get("movies", [])
    total = data.get("data", {}).get("movie_count", 0)

    return {
        "page": page,
        "total": total,
        "results": [format_movie(m) for m in movies],
    }


@router.get("/search")
async def search_movies(
    q: str = Query(..., description="Movie title to search"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=50),
):
    """
    Search English movies by title.
    """
    params = {
        "query_term": q,
        "limit": limit,
        "page": page,
    }
    data = await fetch_yts("list_movies.json", params)
    movies = data.get("data", {}).get("movies", [])
    total = data.get("data", {}).get("movie_count", 0)

    return {
        "page": page,
        "total": total,
        "query": q,
        "results": [format_movie(m) for m in movies],
    }


@router.get("/movie/{imdb_id}")
async def get_movie_detail(imdb_id: str):
    """
    Get full details of a single movie by IMDb ID (e.g. tt1375666).
    Also returns the VidSrc stream URL.
    """
    params = {"query_term": imdb_id, "with_images": True, "with_cast": True}
    data = await fetch_yts("list_movies.json", params)
    movies = data.get("data", {}).get("movies", [])

    if not movies:
        raise HTTPException(status_code=404, detail="Movie not found")

    movie = movies[0]
    formatted = format_movie(movie)
    formatted["cast"] = movie.get("cast", [])
    return formatted


@router.get("/genres")
async def get_genres():
    """
    Returns the list of available genres.
    """
    return {
        "genres": [
            "action", "adventure", "animation", "biography", "comedy",
            "crime", "documentary", "drama", "family", "fantasy",
            "film-noir", "history", "horror", "music", "musical",
            "mystery", "romance", "sci-fi", "short", "sport",
            "superhero", "thriller", "war", "western"
        ]
    }


@router.get("/test")
async def test_connection():
    """
    Test if YTS API is reachable from this server.
    Useful to verify Render can access YTS.
    """
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"{YTS_BASE}/list_movies.json", params={"limit": 1})
            return {
                "status": "ok",
                "yts_reachable": response.status_code == 200,
                "http_status": response.status_code,
            }
    except Exception as e:
        return {"status": "error", "yts_reachable": False, "detail": str(e)}
