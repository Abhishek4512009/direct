from indexer import MovieIndexer
import asyncio

async def test_enrich():
    print("Initializing Indexer...")
    indexer = MovieIndexer()
    # Mock some data
    mock_movies = [
        {"title": "Test Movie", "link": "https://example.com/test"},
        {"title": "Real Movie", "link": "https://gotopage.xyz/real-link"} # Maybe one that exists in index
    ]
    
    print("Testing enrich_metadata...")
    try:
        enriched = indexer.enrich_metadata(mock_movies)
        print("Success!")
        print(enriched)
    except Exception as e:
        print(f"CRASH: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_enrich())
