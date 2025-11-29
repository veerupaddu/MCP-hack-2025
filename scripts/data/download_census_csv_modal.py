import modal
from urllib.parse import urlparse, parse_qs, urljoin, unquote
from bs4 import BeautifulSoup
import requests
import pandas as pd
import os

# Create Modal app
app = modal.App("census-csv-downloader")

# Create a volume to store the downloaded files
volume = modal.Volume.from_name("census-csv-data", create_if_missing=True)

# Define the image with required dependencies
image = modal.Image.debian_slim().pip_install(
    "requests",
    "beautifulsoup4",
    "tqdm",
    "pandas",
    "openpyxl",
    "xlrd"
)

BASE_URL = "https://www.e-stat.go.jp"
START_URL = "https://www.e-stat.go.jp/en/stat-search/files?page=1&toukei=00200521&tstat=000001136464"
VOLUME_PATH = "/data"

@app.function(
    image=image,
    volumes={VOLUME_PATH: volume},
    timeout=900,  # Increased for conversion time
    retries=3,
    max_containers=100,  # Reduced for memory usage
    cpu=1.0,
    memory=1024,  # Added memory for Excel processing
)
def download_and_convert_to_csv(url: str) -> dict:
    """Downloads Excel file and converts to CSV."""
    import os
    
    try:
        # Extract statInfId from URL for filename
        parsed_url = urlparse(url)
        qs = parse_qs(parsed_url.query)
        if 'statInfId' not in qs:
            return {"url": url, "status": "error", "message": "No statInfId in URL"}
            
        stat_id = qs['statInfId'][0]
        
        # Check if CSV file already exists
        csv_filename = f"{stat_id}.csv"
        csv_filepath = os.path.join(VOLUME_PATH, csv_filename)
        
        if os.path.exists(csv_filepath) and os.path.getsize(csv_filepath) > 0:
            return {"url": url, "status": "skipped", "filename": csv_filename, "type": "csv"}
        
        # Download the Excel file
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        
        # Save temporary Excel file
        temp_excel_path = os.path.join(VOLUME_PATH, f"temp_{stat_id}.xlsx")
        with open(temp_excel_path, 'wb') as f:
            f.write(response.content)
        
        try:
            # Convert Excel to CSV
            # Try different Excel engines
            for engine in ['openpyxl', 'xlrd']:
                try:
                    # Read Excel file (try first sheet)
                    df = pd.read_excel(temp_excel_path, engine=engine, sheet_name=0)
                    
                    # Clean the data
                    df = df.dropna(how='all')  # Remove empty rows
                    df = df.fillna('')  # Replace NaN with empty string
                    
                    # Save as CSV
                    df.to_csv(csv_filepath, index=False, encoding='utf-8')
                    
                    # Remove temporary Excel file
                    os.remove(temp_excel_path)
                    
                    # Commit changes to volume
                    volume.commit()
                    
                    return {
                        "url": url, 
                        "status": "success", 
                        "filename": csv_filename, 
                        "type": "csv",
                        "rows": len(df),
                        "columns": len(df.columns)
                    }
                    
                except Exception as e:
                    continue  # Try next engine
            
            # If all engines failed
            os.remove(temp_excel_path)
            return {"url": url, "status": "error", "message": "Could not read Excel file"}
            
        except Exception as e:
            # Clean up temp file if conversion fails
            if os.path.exists(temp_excel_path):
                os.remove(temp_excel_path)
            raise e
        
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

@app.function(
    image=image,
    volumes={VOLUME_PATH: volume},
    timeout=600
)
def analyze_file_batch(filenames: list) -> list:
    """Analyze a batch of files and return their metadata."""
    import os
    
    results = []
    for filename in filenames:
        try:
            filepath = os.path.join(VOLUME_PATH, filename)
            
            # Get basic file info
            file_info = {
                'filename': filename,
                'stat_id': filename.replace('.csv', ''),
                'size_bytes': os.path.getsize(filepath),
                'modified': os.path.getmtime(filepath)
            }
            
            # Read column information
            try:
                df = pd.read_csv(filepath, nrows=0)  # Just read header
                file_info['columns'] = len(df.columns)
                file_info['column_names'] = str(list(df.columns))  # Convert to string for CSV
            except Exception as e:
                file_info['columns'] = 0
                file_info['column_names'] = str([])
            
            results.append(file_info)
        except Exception as e:
            print(f"Error processing {filename}: {e}")
            
    return results

@app.function(
    image=image,
    volumes={VOLUME_PATH: volume},
    timeout=1800  # 30 minutes
)
def create_master_csv() -> dict:
    """Creates a master CSV file with metadata about all downloaded files."""
    import os
    import json
    
    try:
        print("Scanning volume for CSV files...")
        filenames = [f for f in os.listdir(VOLUME_PATH) if f.endswith('.csv') and not f.startswith('temp_')]
        print(f"Found {len(filenames)} CSV files to process")
        
        # Process files in parallel batches
        batch_size = 100
        batches = [filenames[i:i+batch_size] for i in range(0, len(filenames), batch_size)]
        
        print(f"Processing {len(batches)} batches of {batch_size} files each...")
        
        all_results = []
        for i, batch_results in enumerate(analyze_file_batch.map(batches)):
            all_results.extend(batch_results)
            print(f"Completed batch {i+1}/{len(batches)} ({len(all_results)} files processed)")
        
        print("Creating master CSV file...")
        # Create master CSV
        if all_results:
            master_df = pd.DataFrame(all_results)
            master_path = os.path.join(VOLUME_PATH, 'master_inventory.csv')
            master_df.to_csv(master_path, index=False)
            
            volume.commit()
            
            return {
                "status": "success",
                "total_files": len(all_results),
                "master_file": "master_inventory.csv"
            }
        else:
            return {"status": "error", "message": "No CSV files found"}
            
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.function(
    image=image,
    volumes={VOLUME_PATH: volume},
    timeout=300
)
def list_csv_files() -> dict:
    """Lists all CSV files in the volume."""
    import os
    
    try:
        files = []
        for filename in os.listdir(VOLUME_PATH):
            if filename.endswith('.csv'):
                filepath = os.path.join(VOLUME_PATH, filename)
                files.append({
                    'filename': filename,
                    'size_bytes': os.path.getsize(filepath)
                })
        
        return {
            "status": "success",
            "total_files": len(files),
            "files": files[:20]  # Show first 20 files
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.local_entrypoint()
def main():
    """Main function to orchestrate download and conversion."""
    print("Starting Japan Census Data Downloader (CSV Converter)...")
    
    # Get prefecture links
    print("Fetching main category page...")
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
    
    # Download and convert all files to CSV in parallel
    print(f"Starting downloads and CSV conversion across Modal containers...")
    results = list(download_and_convert_to_csv.map(all_file_links))
    
    # Summary
    success = sum(1 for r in results if r["status"] == "success")
    skipped = sum(1 for r in results if r["status"] == "skipped")
    errors = sum(1 for r in results if r["status"] == "error")
    
    print(f"\n=== Download & Conversion Summary ===")
    print(f"Total files: {len(results)}")
    print(f"Successfully converted to CSV: {success}")
    print(f"Skipped (already exists): {skipped}")
    print(f"Errors: {errors}")
    
    # Show details of successful conversions
    if success > 0:
        total_rows = sum(r.get('rows', 0) for r in results if r["status"] == "success")
        print(f"\nTotal data rows converted: {total_rows:,}")
    
    # Show errors
    if errors > 0:
        print(f"\nFailed URLs:")
        for r in results:
            if r["status"] == "error":
                print(f"  - {r['url']}: {r.get('message', 'Unknown error')}")
    
    # Create master inventory
    print(f"\nCreating master inventory CSV...")
    master_result = create_master_csv.remote()
    if master_result["status"] == "success":
        print(f"Master inventory created: {master_result['total_files']} files indexed")
    else:
        print(f"Failed to create master inventory: {master_result.get('message', 'Unknown error')}")

@app.local_entrypoint()
def check_files():
    """Check what files are in the volume."""
    result = list_csv_files.remote()
    if result["status"] == "success":
        print(f"Found {result['total_files']} CSV files:")
        for file_info in result["files"]:
            print(f"  - {file_info['filename']} ({file_info['size_bytes']:,} bytes)")
    else:
        print(f"Error: {result.get('message', 'Unknown error')}")

@app.local_entrypoint()
def create_inventory():
    """Create master inventory of all files."""
    print("Creating master inventory CSV...")
    master_result = create_master_csv.remote()
    if master_result["status"] == "success":
        print(f"Master inventory created: {master_result['total_files']} files indexed")
        print(f"Master file: {master_result['master_file']}")
    else:
        print(f"Failed to create master inventory: {master_result.get('message', 'Unknown error')}")

@app.function(
    image=image,
    volumes={VOLUME_PATH: volume},
    timeout=300
)
def download_file(filename: str) -> str:
    """Download a specific file from the volume."""
    import os
    
    filepath = os.path.join(VOLUME_PATH, filename)
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    else:
        return f"File {filename} not found"

@app.local_entrypoint()
def get_master_inventory():
    """Get the master inventory content."""
    print("Fetching master inventory...")
    content = download_file.remote("master_inventory.csv")
    print("Master inventory content:")
    print(content[:1000] + "..." if len(content) > 1000 else content)

@app.function(
    image=image,
    volumes={VOLUME_PATH: volume},
    timeout=600
)
def analyze_column_patterns() -> dict:
    """Analyze column patterns across all files."""
    import os
    from collections import Counter
    
    try:
        # Read master inventory
        master_path = os.path.join(VOLUME_PATH, 'master_inventory.csv')
        df = pd.read_csv(master_path)
        
        # Analyze column counts
        column_counts = Counter(df['columns'])
        
        # Analyze unique column names
        all_columns = []
        for col_names_str in df['column_names'].dropna():
            try:
                cols = eval(col_names_str)  # Convert string back to list
                all_columns.extend(cols)
            except:
                continue
        
        column_frequency = Counter(all_columns)
        
        return {
            "status": "success",
            "total_files": len(df),
            "column_count_distribution": dict(column_counts),
            "most_common_columns": dict(column_frequency.most_common(20)),
            "unique_columns": len(column_frequency)
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.local_entrypoint()
def analyze_columns():
    """Analyze column patterns across all census files."""
    print("Analyzing column patterns...")
    result = analyze_column_patterns.remote()
    
    if result["status"] == "success":
        print(f"\n=== Column Analysis Results ===")
        print(f"Total files analyzed: {result['total_files']}")
        print(f"Unique column names found: {result['unique_columns']}")
        
        print(f"\nColumn count distribution:")
        for count, files in sorted(result["column_count_distribution"].items()):
            print(f"  {count} columns: {files} files")
        
        print(f"\nMost common column names:")
        for col, freq in result["most_common_columns"].items():
            print(f"  '{col}': {freq} files")
    else:
        print(f"Error: {result.get('message', 'Unknown error')}")

if __name__ == "__main__":
    main()
