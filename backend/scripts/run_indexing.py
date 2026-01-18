import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.app.indexer import MovieIndexer

async def main():
    indexer = MovieIndexer()
    await indexer.start_indexing()

if __name__ == "__main__":
    asyncio.run(main())
