import pandas as pd
import csv
import os

current_dir = os.path.dirname(os.path.abspath(__file__))

input_file = os.path.join(current_dir, "..", "..", "CSV", "Initial_CSV", "raw_tracks_cleaned.csv")
output_file = os.path.join(current_dir, "..", "..", "CSV", "Cleaned_CSV", "raw_tracks_cleaned.csv")

print(f"Reading {input_file}...")

# 1. Read with Pandas engine='python' which is more forgiving with bad lines
# quotechar='"' tells pandas to expect standard quotes, but the engine handles nesting better.
try:
    df = pd.read_csv(input_file, quotechar='"', encoding='utf-8', on_bad_lines='skip')
    
    # 2. Convert album_id to integer to remove .0 decimals
    if 'album_id' in df.columns:
        df['album_id'] = df['album_id'].fillna(0).astype(int)
    
    # 3. Force all data to string to avoid type errors during export
    df = df.astype(str)
    
    # 4. Replace "nan" strings (created by pandas for empty fields) with empty strings
    df = df.replace('nan', '')

    # 4. Save to a new CSV with minimal quoting
    # QUOTE_MINIMAL only quotes fields when necessary (e.g., if they contain commas or newlines)
    df.to_csv(
        output_file, 
        index=False, 
        sep=',', 
        quotechar='"', 
        quoting=csv.QUOTE_MINIMAL, 
        encoding='utf-8'
    )
    
    print(f"Success! Created {output_file}")
    print("Use this file in your COPY command.")

except Exception as e:
    print(f"Error: {e}")