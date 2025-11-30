import modal

app = modal.App("debug-parser")
vol_census = modal.Volume.from_name("census-data")
vol_economy = modal.Volume.from_name("economy-labor-data")

image = modal.Image.debian_slim().pip_install("pandas")

@app.function(
    image=image,
    volumes={"/data/census": vol_census, "/data/economy": vol_economy}
)
def debug_single_file():
    import pandas as pd
    import os
    import re
    
    # Get first census file
    file_path = None
    for root, _, filenames in os.walk("/data/census"):
        for f in filenames:
            if f.lower().endswith('.csv'):
                file_path = os.path.join(root, f)
                break
        if file_path:
            break
    
    if not file_path:
        print("No CSV files found!")
        return
    
    print(f"Testing file: {file_path}")
    
    # Read raw
    df_raw = pd.read_csv(file_path, header=None, low_memory=False)
    print(f"\nRaw shape: {df_raw.shape}")
    print(f"\nFirst 5 rows:")
    for i in range(min(5, len(df_raw))):
        print(f"Row {i}: {df_raw.iloc[i].tolist()[:5]}")
    
    # Test header detection
    for i in range(min(15, len(df_raw))):
        row = df_raw.iloc[i]
        non_null_count = row.count()
        
        # Check for Unnamed
        unnamed_count = sum(1 for val in row if pd.notna(val) and "Unnamed" in str(val))
        
        header_like = 0
        for val in row:
            if pd.notna(val):
                val_str = str(val).strip()
                if val_str and not val_str.replace('.', '').replace(',', '').replace('-', '').replace(' ', '').isdigit():
                    header_like += 1
        
        print(f"\nRow {i}: non_null={non_null_count}, unnamed={unnamed_count}, header_like={header_like}")
        print(f"  Ratios: unnamed={unnamed_count/non_null_count if non_null_count > 0 else 0:.2f}, header={header_like/non_null_count if non_null_count > 0 else 0:.2f}")
        
        # Check if passes filters
        if non_null_count >= len(df_raw.columns) * 0.3:
            if unnamed_count > non_null_count * 0.3:
                print(f"  → SKIPPED (too many Unnamed)")
            elif header_like >= non_null_count * 0.5:
                print(f"  → DETECTED AS HEADER ROW!")
                print(f"  → Headers: {row.tolist()[:10]}")
                break

@app.local_entrypoint()
def main():
    debug_single_file.remote()
