# MoviesDA Backend

## Structure
- `app/`: Core application (FastAPI, Scraper, Indexer)
- `data/`: Storage for `movies_index.json`
- `scripts/`: Helper scripts like `run_indexing.py` and debug tools
- `tests/`: Test files

## Usage

### Run API
Run from the root `moviesda-server` directory:
```bash
uvicorn backend.app.main:app --reload
```

### Run Indexing
```bash
python backend/scripts/run_indexing.py
```

### Install Dependencies
```bash
pip install -r backend/requirements.txt
```
