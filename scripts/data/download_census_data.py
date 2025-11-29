import os
import requests
import time
import argparse
from urllib.parse import urlparse, parse_qs, urljoin, unquote
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

BASE_URL = "https://www.e-stat.go.jp"
START_URL = "https://www.e-stat.go.jp/en/stat-search/files?page=1&toukei=00200521&tstat=000001136464"
DATA_DIR = "data"

def download_file(url, folder, dry_run=False):
    """Downloads a file from the given URL."""
    try:
        if dry_run:
            # print(f"[Dry Run] Would download: {url}") # Silence for progress bar
            return

        # Get filename from Content-Disposition header or URL
        # Note: HEAD request might be slow in parallel, maybe skip or optimize?
        # For speed, let's try to guess from URL first if possible, but e-stat uses IDs.
        # We'll do a HEAD request.
        response = requests.head(url, allow_redirects=True)
        if "Content-Disposition" in response.headers:
            filename = response.headers["Content-Disposition"].split("filename=")[-1].strip('"')
        else:
            parsed_url = urlparse(url)
            qs = parse_qs(parsed_url.query)
            if 'statInfId' in qs:
                filename = f"{qs['statInfId'][0]}.xls" # Default extension
            else:
                filename = os.path.basename(parsed_url.path)
        
        filename = unquote(filename)
        filepath = os.path.join(folder, filename)
        
        if os.path.exists(filepath):
            # print(f"Skipping {filename} (already exists)")
            return

        # print(f"Downloading {filename}...")
        response = requests.get(url)
        with open(filepath, 'wb') as f:
            f.write(response.content)
        # print(f"Saved {filename}")
        
    except Exception as e:
        print(f"Failed to download {url}: {e}")

def get_links_from_page(url):
    """Fetches a page and returns (file_links, nav_links)."""
    file_links = []
    nav_links = []
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        links = soup.find_all('a', href=True)
        for link in links:
            href = link['href']
            full_url = urljoin(BASE_URL, href)
            
            if "file-download" in href and "statInfId" in href:
                file_links.append(full_url)
            elif "stat-search/files" in href and "toukei=00200521" in href:
                # Avoid self-reference or going back up if possible, but simple check is enough
                if full_url != url: 
                    nav_links.append(full_url)
                    
    except Exception as e:
        print(f"Error processing {url}: {e}")
    
    return file_links, nav_links

def crawl_parallel(start_url, max_workers=10):
    """Crawls the e-Stat file pages in parallel."""
    print("Fetching main category page...")
    # 1. Get initial links (Prefectures) from the start page
    # We assume the start page lists the prefectures (nav links)
    _, prefecture_links = get_links_from_page(start_url)
    
    # Filter out duplicates
    prefecture_links = list(set(prefecture_links))
    print(f"Found {len(prefecture_links)} category/prefecture pages. Scanning them in parallel...")

    all_file_links = []
    
    # 2. Process each prefecture page in parallel to find files
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit tasks
        future_to_url = {executor.submit(get_links_from_page, url): url for url in prefecture_links}
        
        for future in tqdm(as_completed(future_to_url), total=len(prefecture_links), desc="Crawling Pages"):
            url = future_to_url[future]
            try:
                f_links, _ = future.result()
                if f_links:
                    all_file_links.extend(f_links)
            except Exception as e:
                print(f"Error scanning {url}: {e}")
                
    return list(set(all_file_links))

def main():
    parser = argparse.ArgumentParser(description="Download e-Stat Census Data")
    parser.add_argument("--dry-run", action="store_true", help="Print URLs without downloading")
    parser.add_argument("--workers", type=int, default=10, help="Number of parallel threads")
    args = parser.parse_args()
    
    if not args.dry_run and not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

    # 1. Parallel Crawl
    links = crawl_parallel(START_URL, max_workers=args.workers)
    print(f"Total files found: {len(links)}")
    
    # 2. Parallel Download
    print(f"Starting downloads with {args.workers} workers...")
    # We can't use executor.map directly with tqdm easily if we want to track completion
    # So we submit futures and iterate as_completed
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = [executor.submit(download_file, url, DATA_DIR, args.dry_run) for url in links]
        for _ in tqdm(as_completed(futures), total=len(futures), desc="Downloading Files"):
            pass

if __name__ == "__main__":
    main()
