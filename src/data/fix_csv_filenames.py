import modal
import os
import urllib.parse

app = modal.App("fix-csv-filenames")

# Volumes
census_volume = modal.Volume.from_name("census-data")
economy_volume = modal.Volume.from_name("economy-labor-data")

image = modal.Image.debian_slim()

def clean_filename(filename: str) -> str:
    """Cleans up the filename by removing garbage prefixes."""
    # 1. Unquote URL encoding
    # e.g. attachment%3B%20filename*%3DUTF-8%27%27a01e... -> attachment; filename*=UTF-8''a01e...
    cleaned = urllib.parse.unquote(filename)
    
    # 2. Remove common garbage prefixes
    prefixes = [
        "attachment; filename*=UTF-8''",
        "attachment; filename=",
        "attachment;",
    ]
    
    for prefix in prefixes:
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix):]
    
    # 3. Clean up any remaining quotes or whitespace
    cleaned = cleaned.strip('"\' ')
    
    return cleaned

def process_volume(volume_path: str, volume_obj: modal.Volume) -> dict:
    """Renames files in the volume."""
    renamed_count = 0
    errors = 0
    
    print(f"Scanning {volume_path}...")
    
    for root, _, files in os.walk(volume_path):
        for filename in files:
            if not filename.lower().endswith('.csv'):
                continue
                
            new_name = clean_filename(filename)
            
            if new_name != filename:
                old_path = os.path.join(root, filename)
                new_path = os.path.join(root, new_name)
                
                # Avoid overwriting if target exists (unless it's the same file)
                if os.path.exists(new_path) and new_path != old_path:
                    print(f"Skipping rename {filename} -> {new_name} (Target exists)")
                    continue
                    
                try:
                    os.rename(old_path, new_path)
                    renamed_count += 1
                    # print(f"Renamed: {filename} -> {new_name}")
                except Exception as e:
                    print(f"Error renaming {filename}: {e}")
                    errors += 1
    
    volume_obj.commit()
    return {"renamed": renamed_count, "errors": errors}

@app.function(image=image, volumes={"/data/census": census_volume})
def fix_census():
    return process_volume("/data/census", census_volume)

@app.function(image=image, volumes={"/data/economy": economy_volume})
def fix_economy():
    return process_volume("/data/economy", economy_volume)

@app.local_entrypoint()
def main():
    print("Fixing Census filenames...")
    census_res = fix_census.remote()
    print(f"Census: Renamed {census_res['renamed']} files. Errors: {census_res['errors']}")
    
    print("Fixing Economy filenames...")
    economy_res = fix_economy.remote()
    print(f"Economy: Renamed {economy_res['renamed']} files. Errors: {economy_res['errors']}")
