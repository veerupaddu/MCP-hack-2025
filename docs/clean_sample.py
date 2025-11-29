import pandas as pd
import re
import os

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

def find_header_row(df):
    """
    Intelligently find the row that contains real column headers.
    Returns: (header_row_index, data_start_row_index)
    """
    for i in range(min(20, len(df))):
        row = df.iloc[i]
        
        # Count non-null values
        non_null_count = row.count()
        if non_null_count < len(df.columns) * 0.3:
            continue  # Skip sparse rows
        
        # Check if this row has "Unnamed" in most values (skip these)
        unnamed_count = sum(1 for val in row if pd.notna(val) and "Unnamed" in str(val))
        if unnamed_count > non_null_count * 0.3:
            continue  # Skip rows with too many "Unnamed"
        
        # Count how many values look like headers (strings, not numbers)
        header_like = 0
        for val in row:
            if pd.notna(val):
                val_str = str(val).strip()
                # Headers are usually strings, not pure numbers
                if val_str and not val_str.replace('.', '').replace(',', '').replace('-', '').replace(' ', '').isdigit():
                    header_like += 1
        
        # If most non-null values look like headers, this is likely the header row
        if header_like >= non_null_count * 0.5:
            return i, i + 1
    
    return None, None

def process_local_file(file_path):
    print(f"Processing {file_path}...")
    
    try:
        # Read the file to extract headers from specific rows
        # Based on inspection:
        # Row 7 (index 7): Destination Areas (cols 4+)
        # Row 9 (index 9): Origin Areas metadata (cols 0-3)
        
        # Read first 15 rows to get headers
        df_headers = pd.read_csv(file_path, header=None, nrows=15, low_memory=False)
        
        # Construct headers
        headers = []
        
        # Cols 0-3 from Row 9
        row9 = df_headers.iloc[9]
        for i in range(4):
            val = clean_value(row9[i])
            headers.append(val if val else f"Meta_{i}")
            
        # Cols 4+ from Row 7
        row7 = df_headers.iloc[7]
        for i in range(4, len(row7)):
            val = clean_value(row7[i])
            # Add prefix to indicate it's a destination column
            headers.append(f"Dest_{val}" if val else f"Col_{i}")
            
        # Read data starting from Row 10
        # We need to read the whole file now, skipping first 10 rows
        df = pd.read_csv(file_path, header=None, skiprows=10, low_memory=False)
        
        # Assign headers
        if len(df.columns) != len(headers):
            print(f"Column count mismatch: Data has {len(df.columns)}, Headers have {len(headers)}")
            # Adjust headers if needed
            if len(df.columns) < len(headers):
                headers = headers[:len(df.columns)]
            else:
                headers += [f"Extra_{i}" for i in range(len(headers), len(df.columns))]
        
        # Deduplicate headers
        unique_headers = []
        seen_headers = {}
        for h in headers:
            if h in seen_headers:
                seen_headers[h] += 1
                unique_headers.append(f"{h}_{seen_headers[h]}")
            else:
                seen_headers[h] = 0
                unique_headers.append(h)
        headers = unique_headers
        
        df.columns = headers
        
        # Clean values in all columns
        for col in df.columns:
            # Only clean string columns to avoid converting numbers to strings if not needed
            if df[col].dtype == 'object':
                df[col] = df[col].apply(clean_value)
        
        # Save clean CSV
        output_path = "clean_sample.csv"
        df.to_csv(output_path, index=False)
        print(f"Saved clean CSV to {output_path}")
        print(f"Shape: {df.shape}")
        print("\nFirst 5 rows:")
        # Print first 5 columns to avoid mess
        print(df.iloc[:5, :5].to_markdown(index=False))
        
    except Exception as e:
        print(f"Error processing file: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    process_local_file("sample.csv")
