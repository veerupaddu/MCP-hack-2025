import modal
import os
import random

app = modal.App("prepare-finetune-data-parallel")

# Volumes
vol_census = modal.Volume.from_name("census-data")
vol_economy = modal.Volume.from_name("economy-labor-data")
vol_dataset = modal.Volume.from_name("finetune-dataset", create_if_missing=True)

image = modal.Image.debian_slim().pip_install("pandas", "openpyxl")

@app.function(
    image=image,
    volumes={
        "/data/census": vol_census,
        "/data/economy": vol_economy
    }
)
def list_csv_files() -> list:
    """Lists all CSV files in both volumes."""
    files = []
    
    # Census
    for root, _, filenames in os.walk("/data/census"):
        for f in filenames:
            if f.lower().endswith('.csv'):
                files.append({"path": os.path.join(root, f), "source": "Japan Census"})
                
    # Economy
    for root, _, filenames in os.walk("/data/economy"):
        for f in filenames:
            if f.lower().endswith('.csv'):
                files.append({"path": os.path.join(root, f), "source": "Japan Economy & Labor"})
                
    return files

@app.function(
    image=image,
    volumes={
        "/data/census": vol_census,
        "/data/economy": vol_economy
    },
    timeout=1200,  # 20 minutes for complex files
    max_containers=100
)
def process_file(file_info: dict) -> list:
    """Process a single CSV file with robust parsing logic."""
    import pandas as pd
    import re
    import random
    
    file_path = file_info["path"]
    source_name = file_info["source"]
    data_points = []
    
    def clean_value(val):
        """Clean and normalize values"""
        if pd.isna(val):
            return None
        val_str = str(val).strip()
        # Remove leading codes like "13103_"
        val_str = re.sub(r'^\d+_', '', val_str)
        # Remove numpy type wrappers
        val_str = re.sub(r'^np\.(int|float)\d*\((.+)\)$', r'\2', val_str)
        return val_str if val_str and val_str.lower() not in ['nan', 'none', ''] else None
    
    try:
        # Extract title from filename
        filename = os.path.basename(file_path)
        filename_no_ext = os.path.splitext(filename)[0]
        parts = filename_no_ext.split('_', 1)
        title = parts[1].replace('_', ' ') if len(parts) > 1 else filename_no_ext
        
        # Strategy 1: Try Cross-Tabulation Parsing (Row 7 + Row 9 headers)
        # This is common in census data
        try:
            df_headers = pd.read_csv(file_path, header=None, nrows=15, low_memory=False)
            
            # Check if Row 7 and Row 9 look like headers
            if len(df_headers) >= 10:
                row7 = df_headers.iloc[7]
                row9 = df_headers.iloc[9]
                
                # Heuristic: Row 9 has metadata in first few cols, Row 7 has destinations in later cols
                if pd.notna(row9[0]) and pd.notna(row7[4]):
                    headers = []
                    # Cols 0-3 from Row 9
                    for i in range(min(4, len(row9))):
                        val = clean_value(row9[i])
                        headers.append(val if val else f"Meta_{i}")
                    
                    # Cols 4+ from Row 7
                    for i in range(4, len(row7)):
                        val = clean_value(row7[i])
                        headers.append(f"Dest_{val}" if val else f"Col_{i}")
                    
                    # Read data skipping metadata
                    df = pd.read_csv(file_path, header=None, skiprows=10, low_memory=False)
                    
                    # Adjust header length
                    if len(df.columns) < len(headers):
                        headers = headers[:len(df.columns)]
                    else:
                        headers += [f"Extra_{i}" for i in range(len(headers), len(df.columns))]
                    
                    df.columns = headers
        except:
            df = None

        # Strategy 2: Fallback to Smart Header Detection if Strategy 1 failed
        if df is None or df.empty:
            df_raw = pd.read_csv(file_path, header=None, low_memory=False)
            
            # Find header row
            header_row_idx = None
            data_start_idx = 0
            
            for i in range(min(20, len(df_raw))):
                row = df_raw.iloc[i]
                non_null_count = row.count()
                if non_null_count < len(df_raw.columns) * 0.3: continue
                
                # Skip if too many Unnamed
                unnamed_count = sum(1 for val in row if pd.notna(val) and "Unnamed" in str(val))
                if unnamed_count > non_null_count * 0.3: continue
                
                # Check for string headers
                header_like = sum(1 for val in row if pd.notna(val) and not str(val).replace('.','').isdigit())
                if header_like >= non_null_count * 0.5:
                    header_row_idx = i
                    data_start_idx = i + 1
                    break
            
            if header_row_idx is not None:
                headers = df_raw.iloc[header_row_idx].tolist()
                df = df_raw.iloc[data_start_idx:].reset_index(drop=True)
                df.columns = headers
            else:
                return []

        # Common Cleaning Steps
        
        # Deduplicate headers
        unique_headers = []
        seen_headers = {}
        for h in df.columns:
            h_clean = clean_value(h) or "Unknown"
            if h_clean in seen_headers:
                seen_headers[h_clean] += 1
                unique_headers.append(f"{h_clean}_{seen_headers[h_clean]}")
            else:
                seen_headers[h_clean] = 0
                unique_headers.append(h_clean)
        df.columns = unique_headers
        
        # Filter valid columns
        valid_cols = [c for c in df.columns if "Unknown" not in c and "Unnamed" not in c]
        if len(valid_cols) < 2: return []
        df = df[valid_cols]
        
        # Clean values
        for col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].apply(clean_value)
        
        df = df.dropna(how='all')
        if len(df) == 0: return []

        # Generate QA Pairs
        # Sample 200 rows per file
        sample_rows = 200
        if len(df) > sample_rows:
            df_sample = df.sample(sample_rows, random_state=42)
        else:
            df_sample = df
        
        label_col = df.columns[0] # Assume first column is the label (Area Name)
        value_cols = df.columns[1:]
        
        for _, row in df_sample.iterrows():
            row_label = row[label_col]
            if not row_label: continue
            
            # Create 3 QA pairs per row
            for _ in range(3):
                if len(value_cols) == 0: break
                col = random.choice(value_cols)
                val = row[col]
                
                if not val: continue
                
                question = f"What is the {col} for {row_label} in the '{title}' dataset?"
                answer = f"According to '{title}', the {col} for {row_label} is {val}."
                
                entry = {
                    "instruction": question,
                    "input": f"Context: {source_name} data.",
                    "output": answer
                }
                data_points.append(entry)
                        
    except Exception as e:
        pass
    
    return data_points

@app.local_entrypoint()
def main():
    import json
    
    print("Listing files...")
    files = list_csv_files.remote()
    print(f"Found {len(files)} files. Starting parallel processing...")
    
    # Process in batches
    batch_size = 1000
    total_train = 0
    total_val = 0
    
    for batch_start in range(0, len(files), batch_size):
        batch_end = min(batch_start + batch_size, len(files))
        batch_files = files[batch_start:batch_end]
        
        print(f"Processing batch {batch_start//batch_size + 1}/{(len(files)-1)//batch_size + 1} ({len(batch_files)} files)...")
        
        batch_data = []
        for result in process_file.map(batch_files):
            batch_data.extend(result)
        
        print(f"Batch generated {len(batch_data)} data points")
        
        if not batch_data:
            continue
        
        # Shuffle and split
        random.shuffle(batch_data)
        split_idx = int(len(batch_data) * 0.9)
        train_batch = batch_data[:split_idx]
        val_batch = batch_data[split_idx:]
        
        # Save
        save_batch.remote(train_batch, val_batch, batch_start == 0)
        
        total_train += len(train_batch)
        total_val += len(val_batch)
        
        print(f"Saved {len(train_batch)} train, {len(val_batch)} val. Total: {total_train} train, {total_val} val")
    
    print(f"✅ Done! Total: {total_train} train, {total_val} val")

@app.function(
    image=image,
    volumes={"/data/dataset": vol_dataset},
    timeout=600
)
def save_batch(train_data, val_data, is_first_batch):
    import json
    
    mode = 'w' if is_first_batch else 'a'
    
    with open("/data/dataset/train.jsonl", mode, encoding='utf-8') as f:
        for entry in train_data:
            json.dump(entry, f, ensure_ascii=False)
            f.write('\n')
    
    with open("/data/dataset/val.jsonl", mode, encoding='utf-8') as f:
        for entry in val_data:
            json.dump(entry, f, ensure_ascii=False)
            f.write('\n')
    
    vol_dataset.commit()
