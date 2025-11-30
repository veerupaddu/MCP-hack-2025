import modal
from urllib.parse import urlparse, parse_qs, urljoin, unquote
from bs4 import BeautifulSoup
import requests
import os

# Create Modal app
app = modal.App("economy-labor-downloader")

# Create a volume to store the downloaded files
# Using a separate volume for this new data
volume = modal.Volume.from_name("economy-labor-data", create_if_missing=True)

# Define the image with required dependencies
image = modal.Image.debian_slim().pip_install(
    "requests",
    "beautifulsoup4",
    "tqdm"
)

BASE_URL = "https://www.e-stat.go.jp"
VOLUME_PATH = "/data"

# Dataset configurations
DATASETS = {
    "income_economy": {
        "url": "https://www.e-stat.go.jp/en/stat-search/files?page=1&toukei=00200564",
        "id": "00200564",
        "name": "National Survey of Family Income, Consumption and Wealth"
    },
    "labor_wages": {
        "url": "https://www.e-stat.go.jp/en/stat-search/files?page=1&toukei=00450091",
        "id": "00450091",
        "name": "Wage Structure Basic Statistical Survey"
    }
}

@app.function(
    image=image,
    volumes={VOLUME_PATH: volume},
    timeout=600,
    retries=3,
    max_containers=500,
    cpu=1.0,
)
def download_file(url: str, category: str) -> dict:
    """Downloads a single file from e-Stat into a category subdirectory."""
    try:
        # Extract statInfId from URL for filename
        parsed_url = urlparse(url)
        qs = parse_qs(parsed_url.query)
        if 'statInfId' not in qs:
            return {"url": url, "status": "error", "message": "No statInfId in URL"}
            
        stat_id = qs['statInfId'][0]
        
        # Create category directory
        category_path = os.path.join(VOLUME_PATH, category)
        os.makedirs(category_path, exist_ok=True)
        
        # Check if file already exists (try common extensions)
        for ext in ['.xls', '.xlsx', '.csv']:
            potential_file = os.path.join(category_path, f"{stat_id}{ext}")
            if os.path.exists(potential_file) and os.path.getsize(potential_file) > 0:
                return {"url": url, "status": "skipped", "filename": f"{stat_id}{ext}"}
        
        # Get actual filename from headers
        response = requests.head(url, allow_redirects=True, timeout=10)
        if "Content-Disposition" in response.headers:
            filename = response.headers["Content-Disposition"].split("filename=")[-1].strip('"')
        else:
            filename = f"{stat_id}.xls"
        
        filename = unquote(filename)
        filepath = os.path.join(category_path, filename)
        
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
def get_links_from_page(url: str, target_toukei_id: str) -> tuple:
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
            # Generic navigation check + specific toukei ID check
            elif "stat-search/files" in href and f"toukei={target_toukei_id}" in href:
                if full_url != url: 
                    nav_links.append(full_url)
                    
    except Exception as e:
        print(f"Error processing {url}: {e}")
    
    return file_links, nav_links

@app.local_entrypoint()
def main():
    """Main function to orchestrate the download for both datasets."""
    
    for key, config in DATASETS.items():
        print(f"\n{'='*60}")
        print(f"Processing: {config['name']}")
        print(f"{'='*60}")
        
        print(f"Fetching main category page: {config['url']}")
        
        # Get sub-category links (e.g., by year or region)
        _, sub_pages = get_links_from_page.remote(config['url'], config['id'])
        sub_pages = list(set(sub_pages))
        print(f"Found {len(sub_pages)} sub-category pages.")
        
        # If no sub-pages found, the main page might have the files directly (though unlikely for e-Stat top levels)
        # But we'll add the main page to the list just in case
        pages_to_scan = sub_pages + [config['url']]
        
        # Get all file links from pages in parallel
        print("Scanning pages for file links...")
        all_file_links = []
        
        # We need to pass the target_toukei_id to the map function
        # Using a helper or partial isn't straightforward with .map, so we'll use a list of tuples
        map_args = [(page, config['id']) for page in pages_to_scan]
        
        for file_links, _ in get_links_from_page.starmap(map_args):
            all_file_links.extend(file_links)
        
        all_file_links = list(set(all_file_links))
        print(f"Total files found: {len(all_file_links)}")
        
        if not all_file_links:
            print("No files found. Moving to next dataset.")
            continue
            
        # Download all files in parallel
        print(f"Starting downloads for {config['name']}...")
        # Prepare arguments for download_file: (url, category_key)
        download_args = [(link, key) for link in all_file_links]
        
        results = list(download_file.starmap(download_args))
        
        # Summary for this dataset
        success = sum(1 for r in results if r["status"] == "success")
        skipped = sum(1 for r in results if r["status"] == "skipped")
        errors = sum(1 for r in results if r["status"] == "error")
        
        print(f"\n--- Summary for {config['name']} ---")
        print(f"Total files: {len(results)}")
        print(f"Successfully downloaded: {success}")
        print(f"Skipped (already exists): {skipped}")
        print(f"Errors: {errors}")
        
        if errors > 0:
            print(f"\nFailed URLs:")
            for r in results:
                if r["status"] == "error":
                    print(f"  - {r['url']}: {r.get('message', 'Unknown error')}")

    print("\n✅ All datasets processed!")
