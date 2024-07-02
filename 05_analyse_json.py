import json

master_file_path = 'master_data_profile.json'

with open(master_file_path, 'r', encoding='utf-8') as master_file:
    data_profiles = json.load(master_file)
    profile_count = len(data_profiles)

print(f'Total number of data profiles: {profile_count}')
