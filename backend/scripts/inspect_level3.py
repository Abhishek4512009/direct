import httpx
from bs4 import BeautifulSoup

url = "https://moviesda15.com/bha-bha-ba-2025-tamil-movie/"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

print(f"Fetching {url}...")
try:
    resp = httpx.get(url, headers=headers)
    print(f"Status: {resp.status_code}")
    soup = BeautifulSoup(resp.text, 'html.parser')
    
    # 1. Find Poster
    # Usually it's an <img> inside a div, often near the top
    print("\n--- Potential Posters ---")
    images = soup.find_all('img')
    for img in images:
        src = img.get('src', '')
        # Filter out icons/small images
        if 'folder' not in src and 'icon' not in src:
            print(f"Image: {src}")
            parent = img.parent
            print(f"  Parent class: {parent.get('class')}")
            
    # 2. Find Description/Synopsis
    # Look for "Synopsis" keyword
    print("\n--- Potential Synopsis ---")
    # Method A: text search
    synopsis_tag = soup.find(string=lambda t: t and "Synopsis" in t)
    if synopsis_tag:
        print(f"Found 'Synopsis' text in: {synopsis_tag.parent.name}")
        print(f"Content: {synopsis_tag.parent.get_text(strip=True)}")
        # Check next sibling
        # element might be like <b>Synopsis:</b> Description...
        # or <div>Synopsis</div><div>Description</div>
    
    # Method B: Look for generic text block if A fails
    # The screenshot showed a yellow box. Let's look for colored divs or specific classes.
    
except Exception as e:
    print(f"Error: {e}")
