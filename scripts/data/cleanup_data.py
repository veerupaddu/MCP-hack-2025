import modal
import os
import glob

app = modal.App("data-cleanup")

# Define volumes
vol_census = modal.Volume.from_name("census-data")
vol_economy = modal.Volume.from_name("economy-labor-data")

image = modal.Image.debian_slim()

@app.function(
    image=image,
    volumes={
        "/data/census": vol_census,
        "/data/economy": vol_economy
    },
    timeout=600
)
def cleanup_volume(root_path: str, volume_name: str):
    print(f"🧹 Cleaning up {volume_name} at {root_path}...")
    
    deleted_excel = 0
    deleted_duplicates = 0
    
    for root, dirs, files in os.walk(root_path):
        # 1. Delete Excel files
        for f in files:
            if f.lower().endswith(('.xls', '.xlsx')):
                full_path = os.path.join(root, f)
                try:
                    os.remove(full_path)
                    deleted_excel += 1
                except Exception as e:
                    print(f"Error deleting {f}: {e}")

        # 2. Delete duplicate CSVs
        # Logic: If 'ID_Title.csv' exists, delete 'ID.csv'
        csv_files = [f for f in files if f.lower().endswith('.csv')]
        
        # Group by ID (assuming ID is the part before the first underscore or the whole name)
        # Actually, the pattern is:
        # Old: ID.csv
        # New: ID_Title.csv
        
        # Find all "ID.csv" candidates
        simple_csvs = {} # Map ID -> filename
        complex_csvs = set() # Set of IDs that have a complex version
        
        for f in csv_files:
            name, _ = os.path.splitext(f)
            if '_' in name:
                # Likely ID_Title
                # We need to extract the ID. 
                # Based on previous scripts, ID is the first part, but title might contain underscores.
                # However, the simple file is just "ID.csv".
                # So we can check if there is a file named "{ID}.csv" corresponding to this complex one.
                # But we don't know the ID for sure just from splitting by underscore if ID itself has underscores (unlikely for these datasets, usually alphanumeric).
                # Let's assume ID is everything before the *first* underscore.
                parts = name.split('_', 1)
                if len(parts) > 1:
                    complex_csvs.add(parts[0])
            else:
                # Likely ID.csv
                simple_csvs[name] = f

        # Now check for duplicates
        for simple_id, simple_filename in simple_csvs.items():
            if simple_id in complex_csvs:
                # We have both ID.csv and ID_Title.csv -> Delete ID.csv
                full_path = os.path.join(root, simple_filename)
                try:
                    os.remove(full_path)
                    deleted_duplicates += 1
                    # print(f"Deleted duplicate: {simple_filename}")
                except Exception as e:
                    print(f"Error deleting {simple_filename}: {e}")

    # Commit changes (needed for Modal Volumes)
    if volume_name == "census-data":
        vol_census.commit()
    else:
        vol_economy.commit()
        
    print(f"✅ {volume_name}: Deleted {deleted_excel} Excel files and {deleted_duplicates} duplicate CSVs.")

@app.local_entrypoint()
def main():
    # Cleanup Census Data
    cleanup_volume.remote("/data/census", "census-data")
    
    # Cleanup Economy & Labor Data
    cleanup_volume.remote("/data/economy", "economy-labor-data")
