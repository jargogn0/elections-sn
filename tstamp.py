import pandas as pd
import random
from datetime import timedelta

# Read the Excel file
df = pd.read_excel('elections_senegal.xlsx')

# Remove spaces from column names
df = df.rename(columns=lambda x: x.replace(' ', '_'))

# Create a new 'Timestamp' column with random dates
start_date = pd.Timestamp(2022, 1, 1)
end_date = pd.Timestamp(2022, 3, 31)
df['Timestamp'] = [start_date + pd.Timedelta(days=random.randint(0, 89)) for _ in range(len(df))]

# Split each department into multiple rows with different timestamps
new_rows = []
current_time = start_date

for _, row in df.iterrows():
    for i in range(1, 4):
        new_row = {}
        for col in df.columns:
            if col == 'Department':
                new_row[col] = row[col]  # Keep the original department name
            elif col == 'Timestamp':
                current_time += timedelta(seconds=5)
                new_row[col] = current_time  # Assign the current_time as the new timestamp
            else:
                new_row[col] = row[col]
        new_rows.append(new_row)

# Create a new DataFrame from the list of new rows
new_df = pd.DataFrame(new_rows)

# Save the new DataFrame to excel file
new_df.to_excel('elections_senegal_with_timestamps.xlsx', index=False)
print(new_df)
