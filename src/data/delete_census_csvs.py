import modal
import os

app = modal.App("delete-census-csvs")
volume = modal.Volume.from_name("census-data")

@app.function(volumes={"/data": volume})
def delete_csvs():
    """Delete all CSV files in the census-data volume, preserving Excel files."""
    base_path = "/data"
    deleted = 0
    for root, _, files in os.walk(base_path):
        for f in files:
            if f.lower().endswith('.csv'):
                try:
                    os.remove(os.path.join(root, f))
                    deleted += 1
                except Exception as e:
                    print(f"Failed to delete {f}: {e}")
    volume.commit()
    return f"Deleted {deleted} CSV files from census-data volume"

@app.local_entrypoint()
def main():
    result = delete_csvs.remote()
    print(result)
