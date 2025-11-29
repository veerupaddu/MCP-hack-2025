import modal
import os


# Create Modal app
app = modal.App("economy-labor-csv-converter")

# Use the same volume where data was downloaded
volume = modal.Volume.from_name("economy-labor-data")

# Define image with pandas and openpyxl for Excel processing
image = modal.Image.debian_slim().pip_install(
    "pandas",
    "openpyxl",
    "xlrd"
)

VOLUME_PATH = "/data"

@app.function(
    image=image,
    volumes={VOLUME_PATH: volume},
    timeout=600,
    max_containers=100,
)
def convert_to_csv(file_path: str) -> dict:
    """Converts a single Excel file to CSV with a human-readable name."""
    import pandas as pd
    import re

    try:
        # Determine output path
        directory, filename = os.path.split(file_path)
        name, ext = os.path.splitext(filename)
        
        if ext.lower() not in ['.xls', '.xlsx']:
            return {"file": file_path, "status": "skipped", "reason": "Not an Excel file"}
            
        # 1. Extract Title for Filename
        # Read first few rows to find a title
        try:
            df_meta = pd.read_excel(file_path, header=None, nrows=10)
            title = None
            # Search for the first long string which is likely the title
            for val in df_meta.values.flatten():
                if isinstance(val, str) and len(val) > 5:
                    title = val
                    break
            
            if title:
                # Sanitize title
                clean_title = re.sub(r'[\\/*?:"<>|]', "", title)
                clean_title = re.sub(r'\s+', "_", clean_title)
                clean_title = clean_title.strip()[:100]
                
                # Use ID + Title to ensure uniqueness and readability
                csv_filename = f"{name}_{clean_title}.csv"
            else:
                csv_filename = f"{name}.csv"
                
        except Exception as e:
            print(f"Warning: Could not extract title from {filename}: {e}")
            csv_filename = f"{name}.csv"

        csv_path = os.path.join(directory, csv_filename)
        
        # Check if CSV already exists
        if os.path.exists(csv_path):
             return {"file": file_path, "status": "skipped", "reason": "CSV already exists", "csv_path": csv_path}

        # 2. Convert Content
        # Read full file
        df = pd.read_excel(file_path)
        
        # Save as CSV
        df.to_csv(csv_path, index=False, encoding='utf-8')
        
        # Commit changes
        volume.commit()
        
        return {"file": file_path, "status": "success", "csv_path": csv_path}
        
    except Exception as e:
        return {"file": file_path, "status": "error", "message": str(e)}

@app.function(image=image, volumes={VOLUME_PATH: volume})
def list_excel_files() -> list:
    """Lists all Excel files in the volume."""
    excel_files = []
    for root, dirs, files in os.walk(VOLUME_PATH):
        for file in files:
            if file.lower().endswith(('.xls', '.xlsx')):
                excel_files.append(os.path.join(root, file))
    return excel_files

@app.local_entrypoint()
def main():
    """Main function to orchestrate CSV conversion."""
    print("Scanning for Excel files...")
    files = list_excel_files.remote()
    print(f"Found {len(files)} Excel files.")
    
    if not files:
        print("No files to convert.")
        return

    print("Starting conversion...")
    results = list(convert_to_csv.map(files))
    
    # Summary
    success = sum(1 for r in results if r["status"] == "success")
    skipped = sum(1 for r in results if r["status"] == "skipped")
    errors = sum(1 for r in results if r["status"] == "error")
    
    print(f"\n=== Conversion Summary ===")
    print(f"Total files processed: {len(results)}")
    print(f"Successfully converted: {success}")
    print(f"Skipped: {skipped}")
    print(f"Errors: {errors}")
    
    if errors > 0:
        print(f"\nFailed Conversions:")
        for r in results:
            if r["status"] == "error":
                print(f"  - {r['file']}: {r.get('message', 'Unknown error')}")

    print("\n✅ Conversion complete!")
