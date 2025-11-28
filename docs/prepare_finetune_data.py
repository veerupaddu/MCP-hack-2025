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
    timeout=600,
    max_containers=100  # Parallel processing
)
def process_file(file_info: dict) -> list:
    """Process a single CSV file and return a list of QA pairs."""
    import pandas as pd
    import os
    
    file_path = file_info["path"]
    source_name = file_info["source"]
    data_points = []
    
    try:
        # Extract title
        filename = os.path.basename(file_path)
        filename_no_ext = os.path.splitext(filename)[0]
        parts = filename_no_ext.split('_', 1)
        if len(parts) > 1:
            title = parts[1].replace('_', ' ')
        else:
            title = filename_no_ext
            
        # Read CSV
        try:
            df = pd.read_csv(file_path, low_memory=False)
        except:
            return []
            
        if df.empty or len(df.columns) < 2:
            return []
            
        # Smart sampling: Use 200 rows per file (balance between coverage and memory)
        # This gives ~1.4M QA pairs total (6888 files × 200 rows)
        sample_rows = 500
        if len(df) > sample_rows:
            df_sample = df.sample(sample_rows, random_state=42)
        else:
            df_sample = df
            
        label_col = df.columns[0]
        value_cols = df.columns[1:]
        
        for _, row in df_sample.iterrows():
            row_label = str(row[label_col])
            
            if len(value_cols) > 0:
                col = random.choice(value_cols)
                val = str(row[col])
                
                if val.lower() in ['nan', '', 'none', '-']:
                    continue
                    
                question = f"What is the {col} for {row_label} in the dataset '{title}'?"
                answer = f"According to the '{title}' dataset, the {col} for {row_label} is {val}."
                
                entry = {
                    "instruction": question,
                    "input": f"Context: {source_name} data.",
                    "output": answer
                }
                data_points.append(entry)
                
    except Exception as e:
        # print(f"Error in {file_path}: {e}")
        pass
        
    return data_points

@app.local_entrypoint()
def main():
    import json
    
    print("Listing files...")
    files = list_csv_files.remote()
    print(f"Found {len(files)} files. Starting parallel processing...")
    
    # Process in batches and save incrementally to avoid OOM
    batch_size = 1000  # With 200 rows/file, this is ~200K data points per batch
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
        
        # Shuffle and split this batch
        import random
        random.shuffle(batch_data)
        split_idx = int(len(batch_data) * 0.9)
        train_batch = batch_data[:split_idx]
        val_batch = batch_data[split_idx:]
        
        # Append to files (streaming write)
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
    import os
    
    mode = 'w' if is_first_batch else 'a'  # Overwrite first batch, append rest
    
    train_path = "/data/dataset/train.jsonl"
    val_path = "/data/dataset/val.jsonl"
    
    with open(train_path, mode, encoding='utf-8') as f:
        for entry in train_data:
            json.dump(entry, f, ensure_ascii=False)
            f.write('\n')
    
    with open(val_path, mode, encoding='utf-8') as f:
        for entry in val_data:
            json.dump(entry, f, ensure_ascii=False)
            f.write('\n')
    
    vol_dataset.commit()
