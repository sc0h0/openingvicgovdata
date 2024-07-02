import pandas as pd
import matplotlib.pyplot as plt

# Load the CSV file into a DataFrame
df = pd.read_csv('dataset_info.csv')

# Fill NaN values in the 'fileTypes' column with empty lists
df['fileTypes'] = df['fileTypes'].fillna('').str.split('; ')

# Extract all distinct file types
all_file_types = set(file_type for file_types in df['fileTypes'] for file_type in file_types if file_type)

# Initialize columns for each distinct file type with zeros
for file_type in all_file_types:
    df[file_type] = 0

# Set the flag to 1 if the file type is present
for index, row in df.iterrows():
    for file_type in row['fileTypes']:
        if file_type in all_file_types:
            df.at[index, file_type] = 1

# Drop the original 'fileTypes' column
df = df.drop(columns=['fileTypes'])

# Print the resulting DataFrame
print(df)

# Optionally, save the modified DataFrame to a new CSV file
df.to_csv('modified_dataset_info.csv', index=False)

# Create a distribution plot for file types
file_type_counts = df[list(all_file_types)].sum().sort_values(ascending=False)
file_type_counts.plot(kind='barh', figsize=(10, 6))

plt.title('Distribution of File Types')
plt.xlabel('Count')
plt.ylabel('File Type')
plt.tight_layout()

# Show the plot
plt.show()
