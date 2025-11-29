import modal
import os
import hashlib

# Modal app for duplicate CSV cleanup
app = modal.App("duplicate-csv-cleanup")

# Volumes where CSVs are stored
census_volume = modal.Volume.from_name("census-data")
economy_volume = modal.Volume.from_name("economy-labor-data")

# Use a lightweight image (no extra packages needed)
image = modal.Image.debian_slim()

def _hash_file(path: str) -> str:
    """Compute MD5 hash of a file's contents."""
    hash_md5 = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def _clean_volume(mount_path: str, volume_obj: modal.Volume) -> dict:
    """Delete duplicate CSV files under ``mount_path``.
    Returns a summary dict with total, unique, and deleted counts.
    """
    csv_files = []
    for root, _, files in os.walk(mount_path):
        for f in files:
            if f.lower().endswith('.csv'):
                csv_files.append(os.path.join(root, f))
    # Map hash -> list of file paths
    hash_map = {}
    for f in csv_files:
        try:
            h = _hash_file(f)
            hash_map.setdefault(h, []).append(f)
        except Exception as e:
            print(f"Error hashing {f}: {e}")
    deleted = 0
    kept = 0
    for paths in hash_map.values():
        # Keep the first file, delete the rest
        for dup in paths[1:]:
            try:
                os.remove(dup)
                deleted += 1
                print(f"Deleted duplicate: {dup}")
            except Exception as e:
                print(f"Failed to delete {dup}: {e}")
        kept += 1
    # Commit changes to the volume so deletions persist
    volume_obj.commit()
    return {"total_files": len(csv_files), "unique": kept, "deleted": deleted}

@app.function(image=image, volumes={"/data": census_volume})
def clean_census() -> dict:
    """Clean duplicate CSVs in the census-data volume."""
    return _clean_volume("/data", census_volume)

@app.function(image=image, volumes={"/data": economy_volume})
def clean_economy() -> dict:
    """Clean duplicate CSVs in the economy-labor-data volume."""
    return _clean_volume("/data", economy_volume)

@app.local_entrypoint()
def main():
    print("🔎 Cleaning census-data volume...")
    census_summary = clean_census.remote()
    print("Census summary:", census_summary)
    print("🔎 Cleaning economy-labor-data volume...")
    economy_summary = clean_economy.remote()
    print("Economy summary:", economy_summary)
