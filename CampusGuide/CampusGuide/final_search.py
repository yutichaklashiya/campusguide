import pandas as pd
import os

def search_excel(file_path, term):
    if not os.path.exists(file_path):
        return
    print(f"--- Searching in {file_path} ---")
    xl = pd.ExcelFile(file_path)
    for name in xl.sheet_names:
        df = xl.parse(name)
        for i, row in df.iterrows():
            row_str = " ".join(map(str, row.values)).lower()
            if term.lower() in row_str:
                print(f"Found in sheet '{name}', row {i}: {row_str}")

search_excel('Book1 (1).xlsx', 'Kalpit')
search_excel('data/University_Data.xlsx', 'Kalpit')
search_excel('Book1 (1).xlsx', 'Soni')
search_excel('data/University_Data.xlsx', 'Soni')
