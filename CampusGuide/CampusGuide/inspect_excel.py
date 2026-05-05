import pandas as pd
import os
base = r'D:/CampusGuide (2)/CampusGuide (2)/CampusGuide/CampusGuide/CampusGuide'
path = os.path.join(base, 'University_Data.xlsx')
print('path', path)
xl = pd.ExcelFile(path)
print('sheets', xl.sheet_names)
df = xl.parse('Course_info')
print('cols', list(df.columns))
rows = df[df.apply(lambda row: row.astype(str).str.contains('BCA', case=False, na=False).any(), axis=1)]
print('rows found', len(rows))
print(rows.head(20).to_string(index=False))
