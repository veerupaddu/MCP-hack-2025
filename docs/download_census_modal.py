import modal
from urllib.parse import urlparse, parse_qs, urljoin, unquote
from bs4 import BeautifulSoup
import requests

# Create Modal app
app = modal.App("census-data-downloader")

# Create a volume to store the downloaded files
volume = modal.Volume.from_name("census-data", create_if_missing=True)

# Define the image with required dependencies
image = modal.Image.debian_slim().pip_install(
    "requests",
    "beautifulsoup4",
    "tqdm"
)

BASE_URL = "https://www.e-stat.go.jp"
START_URL = "https://www.e-stat.go.jp/en/stat-search/files?page=1&toukei=00200521&tstat=000001136464"
VOLUME_PATH = "/data"

@app.function(
    image=image,
    volumes={VOLUME_PATH: volume},
    timeout=600,
    retries=3,
    concurrency_limit=500,  # Run up to 500 downloads in parallel
    cpu=1.0,  # 1 CPU is enough for network I/O
)
def download_file(url: str) -> dict:
    """Downloads a single file from e-Stat."""
    import os
    
    try:
        # Extract statInfId from URL for filename
        parsed_url = urlparse(url)
        qs = parse_qs(parsed_url.query)
        if 'statInfId' not in qs:
            return {"url": url, "status": "error", "message": "No statInfId in URL"}
            
        stat_id = qs['statInfId'][0]
        
        # Check if file already exists (try common extensions)
        for ext in ['.xls', '.xlsx', '.csv']:
            potential_file = os.path.join(VOLUME_PATH, f"{stat_id}{ext}")
            if os.path.exists(potential_file) and os.path.getsize(potential_file) > 0:
                return {"url": url, "status": "skipped", "filename": f"{stat_id}{ext}"}
        
        # Get actual filename from headers
        response = requests.head(url, allow_redirects=True, timeout=10)
        if "Content-Disposition" in response.headers:
            filename = response.headers["Content-Disposition"].split("filename=")[-1].strip('"')
        else:
            filename = f"{stat_id}.xls"
        
        filename = unquote(filename)
        filepath = os.path.join(VOLUME_PATH, filename)
        
        # Double-check if file exists after getting real filename
        if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
            return {"url": url, "status": "skipped", "filename": filename}
        
        # Download the file
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        # Commit changes to volume
        volume.commit()
        
        return {"url": url, "status": "success", "filename": filename, "size": len(response.content)}
        
    except Exception as e:
        return {"url": url, "status": "error", "message": str(e)}

@app.function(image=image, timeout=3600)
def get_links_from_page(url: str) -> tuple:
    """Fetches a page and returns (file_links, nav_links)."""
    file_links = []
    nav_links = []
    try:
        response = requests.get(url, timeout=30)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        links = soup.find_all('a', href=True)
        for link in links:
            href = link['href']
            full_url = urljoin(BASE_URL, href)
            
            if "file-download" in href and "statInfId" in href:
                file_links.append(full_url)
            elif "stat-search/files" in href and "toukei=00200521" in href:
                if full_url != url: 
                    nav_links.append(full_url)
                    
    except Exception as e:
        print(f"Error processing {url}: {e}")
    
    return file_links, nav_links

@app.local_entrypoint()
def main():
    """Main function to orchestrate the download."""
    print("Fetching main category page...")
    
    # Get prefecture links
    _, prefecture_links = get_links_from_page.remote(START_URL)
    prefecture_links = list(set(prefecture_links))
    print(f"Found {len(prefecture_links)} category/prefecture pages.")
    
    # Get all file links from prefecture pages in parallel
    print("Scanning prefecture pages for file links...")
    all_file_links = []
    
    for file_links, _ in get_links_from_page.map(prefecture_links):
        all_file_links.extend(file_links)
    
    all_file_links = list(set(all_file_links))
    print(f"Total files found: {len(all_file_links)}")
    
    # Download all files in parallel
    print(f"Starting downloads across Modal containers...")
    results = list(download_file.map(all_file_links))
    
    # Summary
    success = sum(1 for r in results if r["status"] == "success")
    skipped = sum(1 for r in results if r["status"] == "skipped")
    errors = sum(1 for r in results if r["status"] == "error")
    
    print(f"\n=== Download Summary ===")
    print(f"Total files: {len(results)}")
    print(f"Successfully downloaded: {success}")
    print(f"Skipped (already exists): {skipped}")
    print(f"Errors: {errors}")
    
    if errors > 0:
        print(f"\nFailed URLs:")
        for r in results:
            if r["status"] == "error":
                print(f"  - {r['url']}: {r.get('message', 'Unknown error')}")
