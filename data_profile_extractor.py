import os
import pandas as pd
import json
import chardet
from datetime import datetime

def detect_encoding(file_path):
    with open(file_path, 'rb') as file:
        raw_data = file.read()
    result = chardet.detect(raw_data)
    return result['encoding']

def convert_timestamp(obj):
    """Convert Timestamp objects to strings."""
    if isinstance(obj, (pd.Timestamp, datetime)):
        return obj.isoformat()
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serialisable")

def create_data_profile(url, title, description, index, temp_dir='temp'):
    # Define the directory and file path
    file_path = None

    # Find the file in the temp directory
    for file in os.listdir(temp_dir):
        if os.path.isfile(os.path.join(temp_dir, file)):
            file_path = os.path.join(temp_dir, file)
            break

    if file_path is None:
        raise FileNotFoundError("No file found in the temp directory")

    # Extract the file name
    filename = os.path.basename(file_path)

    # Detect the encoding of the file
    encoding = detect_encoding(file_path)

    try:
        # Read the file based on its type
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path, encoding=encoding)
        elif file_path.endswith('.xlsx') or file_path.endswith('.xls'):
            df = pd.read_excel(file_path)
        else:
            raise ValueError("Unsupported file type")

        # Get the columns and sample data
        columns = list(df.columns)
        sample_data = df.head(2).to_dict(orient='records')

        # Convert any Timestamp objects to strings
        sample_data = json.loads(json.dumps(sample_data, default=convert_timestamp))

        # Get file size in bytes and convert to kilobytes
        filesize_bytes = os.path.getsize(file_path)
        filesize_kb = filesize_bytes / 1024
        rows = df.shape[0]

        # Define the data profile
        data_profile = {
            "url": url,
            "filename": filename,
            "title": title,
            "description": description,
            "filesize": filesize_kb,
            "rows": rows,
            "columns": columns,
            "sample_data": sample_data
        }

        # Create the directory for the index if it doesn't exist
        index_dir = os.path.join('data_profiles', str(index))
        os.makedirs(index_dir, exist_ok=True)

        # Save the data profile to a JSON file in the index directory
        json_file_path = os.path.join(index_dir, 'data_profile.json')
        with open(json_file_path, 'w') as json_file:
            json.dump(data_profile, json_file, indent=4, default=convert_timestamp)
            
        # then delete the file
        os.remove(file_path)

        print(f"Data profile has been saved to {json_file_path}")

    except ValueError as e:
        print(f"Error: {e}")

