import modal
import os

app = modal.App("clear-census-volume")
volume = modal.Volume.from_name("census-data")

@app.function(volumes={"/data": volume})
def clear_volume():
    """Delete all files and directories under the mounted volume."""
    base_path = "/data"
    for root, dirs, files in os.walk(base_path, topdown=False):
        for f in files:
            try:
                os.remove(os.path.join(root, f))
            except Exception as e:
                print(f"Failed to delete file {f}: {e}")
        for d in dirs:
            try:
                os.rmdir(os.path.join(root, d))
            except Exception as e:
                print(f"Failed to delete dir {d}: {e}")
    # Commit deletions
    volume.commit()
    return "census-data volume cleared"

@app.local_entrypoint()
def main():
    result = clear_volume.remote()
    print(result)
