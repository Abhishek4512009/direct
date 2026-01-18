import httpx
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from typing import Optional, List, Dict
import urllib.parse
import re

class MoviesdaScraper:
    def __init__(self):
        self.ua = UserAgent()
        self.headers = {
            "User-Agent": self.ua.random,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }
        self.base_url = "https://gotopage.xyz/?ref=2026"  # Seed URL
        self.client = httpx.AsyncClient(headers=self.headers, follow_redirects=True, timeout=30.0)
        self.resolved_base = None

    async def _get_soup(self, url: str) -> BeautifulSoup:
        print(f"Fetching: {url}")
        response = await self.client.get(url)
        response.raise_for_status()
        # Update resolved_base if this was the seed URL or if we were redirected to a new domain
        final_url = str(response.url)
        parsed = urllib.parse.urlparse(final_url)
        new_base = f"{parsed.scheme}://{parsed.netloc}"
        
        if self.resolved_base != new_base:
             self.resolved_base = new_base
        
        return BeautifulSoup(response.text, 'html.parser')

    async def _resolve_url(self, relative_url: str) -> str:
        # If relative_url is full, return it
        if relative_url.startswith("http"):
            return relative_url
            
        # If we haven't resolved base yet, we might be in trouble, but let's try to infer from last request or seed
        if not self.resolved_base:
            # Trigger a fetch to root to resolve
             await self._get_soup(self.base_url)
             
        return urllib.parse.urljoin(self.resolved_base, relative_url)

    async def get_years(self) -> List[Dict[str, str]]:
        """Level 1: Get list of years"""
        soup = await self._get_soup(self.base_url)
        # Look for folder icons or specific list items
        # Heuristic: Links containing 'Movies' and a year
        items = []
        for a in soup.find_all('a'):
            text = a.get_text(strip=True)
            if re.search(r'\d{4}\s+Movies', text, re.IGNORECASE):
                 items.append({"name": text, "link": await self._resolve_url(a['href'])})
        return items

    async def get_movies_in_year(self, year_url: str) -> List[Dict[str, str]]:
        """Level 2: List movies in a specific year page"""
        soup = await self._get_soup(year_url)
        items = []
        # Typically these are inside a specific div or list
        # Heuristic: Links that are NOT pagination links and look like movie titles
        # Common structure in these sites: <div class="f"><img ...> <a href="...">Title</a></div>
        # But sometimes structure varies or div.f is used for nav.
        # Fallback to scanning ALL links, relying on robust filtering to remove junk.
        blocks = soup.find_all('a')
        
        for i, block in enumerate(blocks):
            # If we are scanning 'a' tags directly, 'block' IS 'a'.
            # But if 'block' was div, we look for 'a'.
            # To be safe for mixed usage (if we revert):
            a_tag = block if block.name == 'a' else block.find('a')
            if not a_tag: continue
            
            text = a_tag.get_text(strip=True)
            href = a_tag.get('href', '')
            
            # Filtering logic
            if not href: continue
            if "page" in href.lower(): continue
            if len(text) <= 1: continue # Skip A, B, C navigation
            if text == "0-9": continue # Skip numeric index
            if "telegram" in text.lower(): continue
            if "group" in text.lower(): continue
            
            # Filter specifically logic related to "Movies" backlinks
            if "movies" in text.lower() and re.search(r'\d{4}', text): 
                # Skip "Tamil 2025 Movies" etc.
                if text.lower().startswith("tamil") and text.lower().endswith("movies"):
                     continue
                if text.lower().startswith("20") and text.lower().endswith("movies"):
                     continue

            items.append({"title": text, "link": await self._resolve_url(href)})
        
        # Deduplicate
        seen = set()
        unique_items = []
        for i in items:
            if i['link'] not in seen:
                seen.add(i['link'])
                unique_items.append(i)
                
        return unique_items

    async def get_qualities(self, movie_url: str) -> Dict[str, any]:
        """Level 3: Get available qualities (e.g. Original, 640x360) AND Metadata"""
        soup = await self._get_soup(movie_url)
        
        # --- Metadata Extraction ---
        meta = {"poster": None, "desc": None, "rating": None}
        
        # 1. Poster
        # Heuristic: Look for img inside a div.f or near top with alt text
        # Or just the first image that isn't a likely icon
        try:
            images = soup.find_all('img')
            for img in images:
                src = img.get('src')
                if not src: continue
                # Skip common icons
                if "folder" in src or "arrow" in src or "dir" in src: continue
                
                # If we find a substantial image, take it.
                # Use resolve_url to get absolute path
                full_src = await self._resolve_url(src)
                meta['poster'] = full_src
                break # Take the first valid non-icon image
        except:
            pass
            

        try:
            candidates = []
            
            # 1. Try finding 'Movie Information' specific node (parent)
            # This generally contains the main block
            info_node = soup.find(string=re.compile(r"Movie Information", re.I))
            if info_node:
                 candidates.append(info_node.parent.get_text(separator=' ', strip=True))

            # 2. Also check specifically for "Synopsis:"
            synopsis_node = soup.find(string=re.compile(r"Synopsis\s*:", re.I))
            if synopsis_node:
                 candidates.append(synopsis_node.parent.get_text(separator=' ', strip=True))

            # 3. Fallback: Check containers with keywords
            for element in soup.find_all(['p', 'div', 'font']):
                text = element.get_text(separator=' ', strip=True)
                lower_text = text.lower()
                if "director:" in lower_text or "synopsis:" in lower_text:
                    candidates.append(text)

            best_desc = None
            for text in candidates:
                # Cleaning Phase
                # 0. Normalize whitespace first to make matching reliable
                cleaned_text = re.sub(r'\s+', ' ', text).strip()

                # 1. Strip Pre-Header Junk
                # Regex split to handle case and spacing variations
                # Look for "Movie Information" case insensitive
                split_match = re.search(r"Movie\s+Information", cleaned_text, re.IGNORECASE)
                if split_match:
                    # Keep "Movie Information" and everything after
                    cleaned_text = cleaned_text[split_match.start():]
                
                # 2. Strip Post-Footer Junk
                # Regex patterns for stop markers
                stop_patterns = [
                    r"Incoming\s+Search\s+Terms",
                    r"Page\s+Tags",
                    r"Moviesda\s+Home",
                    r"Disclaimer",
                    r"A-Z\s+Movie\s+Categories",
                    r"Join\s+our\s+Telegram"
                ]
                
                for pattern in stop_patterns:
                    m_match = re.search(pattern, cleaned_text, re.IGNORECASE)
                    if m_match:
                        cleaned_text = cleaned_text[:m_match.start()].strip()

                # Final cleanup just in case
                cleaned_text = cleaned_text.strip()

                # Validation
                # Must look like a description (contain keys or be decent length)
                if len(cleaned_text) > 30 and ("Director" in cleaned_text or "Synopsis" in cleaned_text or "Movie:" in cleaned_text):
                     # If we have a decent candidate, prefer the one starting with "Movie Information"
                     if "Movie Information" in cleaned_text:
                         best_desc = cleaned_text
                         break # Found the gold standard
                     
                     # Otherwise keep looking but store this as fallback
                     if not best_desc:
                         best_desc = cleaned_text
            
            if best_desc:
                meta['desc'] = best_desc

        except Exception as e:
            print(f"Error extracting metadata: {e}")
            pass

        # --- Quality Links ---
        items = []
        blocks = soup.find_all('div', class_='f')
        if not blocks: blocks = soup.find_all('a') # Fallback

        for block in blocks:
            a_tag = block if block.name == 'a' else block.find('a')
            if not a_tag: continue
            text = a_tag.get_text(strip=True)
            href = a_tag.get('href')
            if not href or "page" in href: continue 
            
            # Filter out social links if fallback was used
            if "telegram" in text.lower() or "whatsapp" in text.lower(): continue
            
            items.append({"name": text, "link": await self._resolve_url(href)})
            
        return {"qualities": items, "meta": meta}

    async def get_files(self, quality_url: str, depth: int = 0) -> List[Dict[str, str]]:
        """Level 4: Get actual file entries (Drills down if it finds folders)"""
        # Level 4 is usually very similar to Level 3 in structure, but we only care about links here
        # So we unwrap the result from get_qualities
        
        if depth > 2:
            return []

        result = await self.get_qualities(quality_url)
        items = result.get('qualities', [])
        
        # Check if we need to drill down
        # Heuristic: If we only have 1 item, and it looks like a folder (nested), we drill down.
        # MoviesDA structure: Movie -> Original -> Tamil -> 720p -> File
        
        if len(items) == 1:
            item = items[0]
            # If item name is generic or doesn't look like a file page (no apparent way to distinguish easily structurally, 
            # but usually file pages have multiple items or specific naming).
            # Let's peek: If this item LEADS to another list of qualities/files, we recursively fetch THAT.
            
            # Simple heuristic: Always drill down once if only 1 item, assuming it's a wrapper category.
            # But we must be careful not to loop.
            print(f"Drill checking (Depth {depth}): Found single item '{item['name']}'. Peeking one level deeper...")
            
            sub_items = await self.get_files(item['link'], depth=depth+1)
            
            # If drill down yielded more specific items (more counts, or different names), return THOSE.
            if sub_items and len(sub_items) > 0:
                print(f"Drill success: Flattening {len(sub_items)} items from sub-folder.")
                return sub_items
            else:
                 # If sub-drill failed or returned nothing, return original item
                 return items
                 
        return items

    async def get_servers(self, file_url: str) -> List[Dict[str, str]]:
        """Level 5: Get download servers"""
        soup = await self._get_soup(file_url)
        items = []
        # Look for "Download Server" buttons/links
        for a in soup.find_all('a'):
            text = a.get_text(strip=True)
            href = a.get('href', '')
            # print(f"DEBUG: Found link on server page: {text} -> {href}") # Uncomment for deep debug
            # Broaden search: server, download, link in text OR download in href
            if (("server" in text.lower() or "download" in text.lower() or "link" in text.lower()) or "download" in href.lower()) and "home" not in text.lower() and "back" not in text.lower():
                  items.append({"server": text, "link": await self._resolve_url(href)})
        
        if not items:
            print("DEBUG: No servers found. dumping all links on page:")
            for a in soup.find_all('a'):
                 print(f" - {a.get_text(strip=True)} -> {a.get('href')}")
            pass
        return items

    async def resolve_final_link(self, server_url: str, depth: int = 0) -> Optional[str]:
        """Level 6+: Recursively follow redirect/server pages to get final media link"""
        if depth > 3:
            print("Max depth reached in resolving link.")
            return None
            
        try:
            print(f"Resolving (Depth {depth}): {server_url}")
            soup = await self._get_soup(server_url)
            
            # 1. Check for specific download button with .mp4/.mkv (Success case)
            for a in soup.find_all('a'):
                href = a.get('href', '')
                if href.endswith('.mp4') or href.endswith('.mkv'):
                    return await self._resolve_url(href)
            
            # 2. Check for "Download Server" buttons again (Recursive case)
            for a in soup.find_all('a'):
                text = a.get_text(strip=True)
                href = a.get('href', '')
                if ("download server" in text.lower() or "server" in text.lower()) and "home" not in text.lower():
                     next_link = await self._resolve_url(href)
                     # Avoid infinite loops if link is same as current
                     if next_link != server_url:
                         print(f"Following recursive link: {text} -> {next_link}")
                         result = await self.resolve_final_link(next_link, depth + 1)
                         if result: return result

            # 3. Meta refresh fallback
            meta_refresh = soup.find('meta', attrs={'http-equiv': re.compile("refresh", re.I)})
            if meta_refresh:
                content = meta_refresh.get('content', '')
                if 'url=' in content.lower():
                    next_url = content.split('url=')[-1].strip()
                    return await self._resolve_url(next_url)

            return None
        except Exception as e:
            print(f"Error resolving final link: {e}")
            return None

    async def find_movie_download(self, year: str, movie_title: str) -> Dict:
        """High-level orchestration flow to find a download link."""
        
        # 1. Years
        years = self.get_years()
        year_entry = next((y for y in years if year in y['name']), None)
        if not year_entry:
            return {"error": f"Year {year} not found", "available_years": [y['name'] for y in years]}
            
        print(f"Found Year: {year_entry['name']}")
        
        # 2. Movies
        # 2. Movies - with pagination
        movie_entry = None
        base_year_url = year_entry['link']
        
        # strip trailing slash to append page cleanly if needed
        if base_year_url.endswith('/'):
            base_year_url = base_year_url[:-1]

        # Scan up to 15 pages
        for page_num in range(1, 16):
            if page_num == 1:
                current_url = base_year_url
            else:
                current_url = f"{base_year_url}/?page={page_num}"
            
            print(f"Scanning Page {page_num}: {current_url}")
            try:
                movies = self.get_movies_in_year(current_url)
            except Exception as e:
                print(f"Stopping pagination at page {page_num}: {e}")
                break
                
            if not movies:
                print(f"No movies found on page {page_num}. Stopping.")
                break
                
            # Search in this batch
            movie_entry = next((m for m in movies if movie_title.lower() in m['title'].lower()), None)
            if movie_entry:
                print(f"Found Movie: {movie_entry['title']} on page {page_num}")
                break
        
        if not movie_entry:
             return {"error": f"Movie '{movie_title}' not found in {year} (scanned 15 pages)", "last_page_sample": [m['title'] for m in movies[:10]]}
        
        # 3. Drill Down Loop (Levels 3, 4, 5...)
        # Sometimes movies are nested: Movie -> Original -> Tamil -> 720p -> File
        # We need to drill down until we find Servers.
        
        current_link = movie_entry['link']
        current_name = movie_entry['title']
        
        # Max drill attempts to avoid infinite loops
        for depth in range(4):
            print(f"Drill Level {depth}: Checking {current_name} -> {current_link}")
            
            # Step A: Get Contents (treat as Qualities/Folder)
            # This parses list of links (Folder1, Folder2 OR File1, File2)
            content = await self.get_qualities(current_link)
            items = content.get('qualities', [])
            
            if not items:
                print("No items found at this level.")
                break
                
            # Prefer "Original", "HD", or non-sample items
            # Heuristic: Match 'Original' or '1080p' if available, else first non-sample
            selected_item = items[0]
            
            # Sort/Pick strategy:
            # 1. Prefer "Original"
            # 2. Prefer containing "HD"
            # 3. Prefer not "Sample"
            
            originals = [i for i in items if "original" in i['name'].lower()]
            hds = [i for i in items if "hd" in i['name'].lower()]
            non_samples = [i for i in items if "sample" not in i['name'].lower()]
            
            if originals: selected_item = originals[0]
            elif hds: selected_item = hds[0]
            elif non_samples: selected_item = non_samples[0]
            
            print(f"Selected Item: {selected_item['name']}")
            
            # Step B: Check if this item LEADS to servers directly (Level 5 check)
            # We peek at the next page.
            # If get_servers finds servers, we are done.
            # If not, we assumed it's another folder and continue loop using this item.
            
            servers = await self.get_servers(selected_item['link'])
            if servers:
                # Found servers! We are at the end of the tunnel.
                selected_server = servers[0]
                print(f"Found Server: {selected_server['server']}")
                
                final_link = await self.resolve_final_link(selected_server['link'])
                if final_link:
                    return {
                        "status": "success",
                        "movie": movie_title,
                        "year": year,
                        "quality": selected_item['name'], # approximates final quality
                        "filename": selected_item['name'],
                        "download_link": final_link
                    }
                else:
                    return {"error": "Could not resolve final direct link from server page"}
            
            # If no servers, we iterate, setting current_link to this item
            current_link = selected_item['link']
            current_name = selected_item['name']
            
        return {"error": "Max folder depth reached or no servers found."}

if __name__ == "__main__":
    # Test block
    scraper = MoviesdaScraper()
    # Replace these with real values found in browsing if you want to test
    # print(scraper.find_movie_download("2026", "Vaa Vaathiyaar")) 
    pass
