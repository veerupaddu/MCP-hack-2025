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
    """Converts a single Excel file to CSV."""
    import pandas as pd
    try:
        # Determine output path
        directory, filename = os.path.split(file_path)
        name, ext = os.path.splitext(filename)
        
        if ext.lower() not in ['.xls', '.xlsx']:
            return {"file": file_path, "status": "skipped", "reason": "Not an Excel file"}
            
        csv_filename = f"{name}.csv"
        csv_path = os.path.join(directory, csv_filename)
        
        # Check if CSV already exists
        if os.path.exists(csv_path):
             return {"file": file_path, "status": "skipped", "reason": "CSV already exists"}

        # Read Excel file
        # Using 'None' for sheet_name to read all sheets if multiple exist, 
        # but for simplicity/standardization, we'll default to the first sheet 
        # or concatenate if needed. Let's stick to the first sheet for now 
        # as these stats usually have the main data there.
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
