import sqlite3
import pandas as pd
import os

def setup_all_tables():
    data_dir = 'data'
    db_path = 'data/bi_project.db'
    
    print(f"--- Starting Ingestion ---")
    print(f"Checking directory: {os.path.abspath(data_dir)}")
    
    if not os.path.exists(data_dir):
        print(f"❌ Error: Folder '{data_dir}' not found!")
        return

    files = os.listdir(data_dir)
    print(f"Files found in folder: {files}")

    csv_files = [f for f in files if f.endswith('.csv')]
    if not csv_files:
        print("❌ No CSV files found to process.")
        return

    conn = sqlite3.connect(db_path)
    for file in csv_files:
        print(f"Processing {file}...")
        df = pd.read_csv(os.path.join(data_dir, file))
        table_name = file.replace('.csv', '')
        df.to_sql(table_name, conn, if_exists='replace', index=False)
        print(f"✅ Table '{table_name}' created.")
    
    conn.close()
    print(f"--- Finished! Database ready at {db_path} ---")

if __name__ == "__main__":
    setup_all_tables()