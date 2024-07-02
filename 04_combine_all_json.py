import os
import json

root_folder = 'data_profiles'
combined_data = []

for subdir, _, files in os.walk(root_folder):
    for file in files:
        if file == "data_profile.json":
            file_path = os.path.join(subdir, file)
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if data.get('rows', 0) >= 10:
                    combined_data.append(data)

with open('master_data_profile.json', 'w', encoding='utf-8') as master_file:
    json.dump(combined_data, master_file, indent=4)
