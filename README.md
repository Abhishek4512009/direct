# MoviesDA MCP Server

An MCP server to browse and download Tamil movies from MoviesDA (via gotopage.xyz).

## Installation

1. Navigate to this directory:
   ```bash
   cd c:\Users\kanna\Desktop\Antigravity\mcp\moviesda-server
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Running the Server
Run the server using the MCP CLI or directly with Python (if using FastMCP stdio):

```bash
python server.py
```

### Tools

- **`list_years()`**: Returns available years (e.g., "2026 Movies").
- **`get_download_link(year, movie_title)`**: Fully automated tool.
  - Example: `get_download_link("2026", "Vaa Vaathiyaar")`
  - Returns: `{ "download_link": "https://...", ... }`
