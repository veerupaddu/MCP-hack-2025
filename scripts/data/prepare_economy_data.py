import modal
import os
import random

app = modal.App("prepare-economy-data")

vol_economy = modal.Volume.from_name("economy-labor-data")
vol_dataset = modal.Volume.from_name("finetune-dataset", create_if_missing=True)

image = modal.Image.debian_slim().pip_install("pandas", "openpyxl")

@app.function(image=image, volumes={"/data/economy": vol_economy})
def list_csv_files() -> list:
    """List only economy/labor CSV files"""
    files = []
    for root, _, filenames in os.walk("/data/economy"):
        for f in filenames:
            if f.lower().endswith('.csv'):
                files.append({"path": os.path.join(root, f), "source": "Japan Economy & Labor"})
    return files

@app.function(
    image=image,
    volumes={"/data/economy": vol_economy},
    timeout=1200,  # 20 minutes per file
    max_containers=50  # Reduce parallelism to avoid timeouts
)
def process_file(file_info: dict) -> dict:
    import pandas as pd
    import re
    
    file_path = file_info["path"]
    source_name = file_info["source"]
    data_points = []
    
    def clean_value(val):
        if pd.isna(val):
            return None
        val_str = str(val).strip()
        val_str = re.sub(r'^\d+_', '', val_str)  # Remove codes
        val_str = re.sub(r'^np\.(int|float)\d*\((.+)\)$', r'\2', val_str)  # Remove numpy wrappers
        return val_str if val_str and val_str.lower() not in ['nan', 'none'] else None

    try:
        filename = os.path.basename(file_path)
        filename_no_ext = os.path.splitext(filename)[0]
        parts = filename_no_ext.split('_', 1)
        title = parts[1].replace('_', ' ') if len(parts) > 1 else filename_no_ext
        
        # Read CSV
        try:
            df = pd.read_csv(file_path, low_memory=False)
        except:
            return {"data": [], "columns": None}
        
        if df.empty or len(df) < 3:
            return {"data": [], "columns": None}
        
        # Find data start row (adaptive parsing)
        data_start_row = 0
        for i in range(min(20, len(df))):
            row = df.iloc[i]
            non_null_count = row.count()
            if non_null_count >= len(df.columns) * 0.3:
                string_count = sum(1 for v in row if isinstance(v, str) and len(str(v)) > 0)
                if string_count >= non_null_count * 0.5:
                    data_start_row = i
                    break
        
        if data_start_row > 0:
            new_headers = df.iloc[data_start_row].tolist()
            df = df.iloc[data_start_row+1:].reset_index(drop=True)
            df.columns = [clean_value(h) or f"Col_{i}" for i, h in enumerate(new_headers)]
        else:
            df.columns = [clean_value(col) or f"Col_{i}" for i, col in enumerate(df.columns)]
        
        # Filter valid columns
        valid_cols = [col for col in df.columns if col and not col.startswith("Col_")]
        
        if len(valid_cols) < 2:
            return {"data": [], "columns": None}
        
        df = df[valid_cols]
        df = df.dropna(how='all')
        
        if len(df) == 0:
            return {"data": [], "columns": None}
        
        column_info = {
            "file": filename,
            "columns": list(valid_cols),
            "row_count": len(df)
        }
        
        # Sample ALL rows (no limit) for maximum data
        df_sample = df
        
        label_col = df.columns[0]
        value_cols = df.columns[1:]
        
        for _, row in df_sample.iterrows():
            row_label = clean_value(row[label_col])
            if not row_label:
                continue
            
            # Try to find a valid value column
            for _ in range(min(5, len(value_cols))):
                col = random.choice(value_cols)
                val = clean_value(row[col])
                
                if val:
                    question = f"What is the {col} for {row_label}?"
                    answer = f"The {col} for {row_label} is {val}."
                    
                    entry = {
                        "instruction": question,
                        "input": f"Context: {source_name} data from '{title}'.",
                        "output": answer
                    }
                    data_points.append(entry)
                    break
    except Exception as e:
        print(f"Error processing {file_path}: {str(e)}")
    
    return {"data": data_points, "columns": column_info}

@app.local_entrypoint()
def main():
    import json
    
    print("Listing economy/labor files...")
    files = list_csv_files.remote()
    print(f"Found {len(files)} economy/labor files. Starting processing...")
    
    batch_size = 500  # Smaller batches
    total_train = 0
    total_val = 0
    all_columns = []
    
    for batch_start in range(0, len(files), batch_size):
        batch_end = min(batch_start + batch_size, len(files))
        batch_files = files[batch_start:batch_end]
        
        print(f"Processing batch {batch_start//batch_size + 1}/{(len(files)-1)//batch_size + 1} ({len(batch_files)} files)...")
        
        batch_data = []
        for result in process_file.map(batch_files):
            batch_data.extend(result["data"])
            if result["columns"]:
                all_columns.append(result["columns"])
        
        print(f"Batch generated {len(batch_data)} data points")
        
        if not batch_data:
            continue
        
        random.shuffle(batch_data)
        split_idx = int(len(batch_data) * 0.9)
        train_batch = batch_data[:split_idx]
        val_batch = batch_data[split_idx:]
        
        save_batch.remote(train_batch, val_batch, batch_start == 0)
        
        total_train += len(train_batch)
        total_val += len(val_batch)
        
        print(f"Saved {len(train_batch)} train, {len(val_batch)} val. Total: {total_train} train, {total_val} val")
    
    print("Saving column documentation...")
    save_column_docs.remote(all_columns)
    
    print(f"✅ Done! Total: {total_train} train, {total_val} val")

@app.function(image=image, volumes={"/data/dataset": vol_dataset}, timeout=600)
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

@app.function(image=image, volumes={"/data/dataset": vol_dataset}, timeout=600)
def save_column_docs(all_columns):
    with open("/data/dataset/07-dataset-columns.md", "w", encoding="utf-8") as f:
        f.write("# Economy/Labor Dataset Column Documentation\n\n")
        f.write(f"Total Files Processed: {len(all_columns)}\n\n")
        for col_info in all_columns:
            f.write(f"## {col_info['file']}\n")
            f.write(f"- **Rows**: {col_info['row_count']}\n")
            f.write(f"- **Columns**: {', '.join(map(str, col_info['columns']))}\n\n")
    vol_dataset.commit()
