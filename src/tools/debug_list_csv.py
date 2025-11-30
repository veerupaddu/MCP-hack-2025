import modal
import os

app = modal.App("debug-list-csv")
volume = modal.Volume.from_name("census-data")

@app.function(volumes={"/data": volume})
def list_csvs():
    csv_dir = "/data/csv" # Assuming flat structure or we need to walk
    print(f"Listing files in {csv_dir}...")
    if not os.path.exists(csv_dir):
        # Try finding csv dirs
        print("Searching for csv directories...")
        for root, dirs, files in os.walk("/data"):
            if "csv" in dirs:
                print(f"Found csv dir in {root}")
                for f in os.listdir(os.path.join(root, "csv"))[:5]:
                    print(f"  - {f}")
    else:
        files = os.listdir(csv_dir)
        print(f"Found {len(files)} files in {csv_dir}")
        for f in files[:10]:
            print(f"  - {f}")

@app.local_entrypoint()
def main():
    list_csvs.remote()
