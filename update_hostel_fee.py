import pandas as pd
import os

file_path = r'c:\Users\dell\Downloads\CampusGuide (2)\CampusGuide\CampusGuide\CampusGuide\University_Data.xlsx'

# Load the entire Excel file
with pd.ExcelFile(file_path) as xls:
    # Read all sheets into a dictionary
    sheets_dict = {sheet_name: pd.read_excel(xls, sheet_name) for sheet_name in xls.sheet_names}

# Update the 'Hostel' sheet
if 'Hostel' in sheets_dict:
    df_hostel = sheets_dict['Hostel']
    # Check if 'Category' and 'Fees' columns exist
    if 'Category' in df_hostel.columns and 'Fees' in df_hostel.columns:
        df_hostel.loc[df_hostel['Category'] == 'A/C Room', 'Fees'] = 25000
        sheets_dict['Hostel'] = df_hostel
        print("Updated A/C Room fee to 25000 in 'Hostel' sheet.")
    else:
        print("Error: 'Category' or 'Fees' column not found in 'Hostel' sheet.")
else:
    print("Error: 'Hostel' sheet not found in the Excel file.")

# Write all sheets back to the Excel file
with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
    for sheet_name, df in sheets_dict.items():
        df.to_excel(writer, sheet_name=sheet_name, index=False)

print("Excel file updated successfully.")
