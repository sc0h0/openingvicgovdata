import pandas as pd
import os
import psutil
from playwright.sync_api import sync_playwright, TimeoutError
from data_profile_extractor import create_data_profile

# Define the history CSV file path
history_csv_path = 'dataset_info_with_history.csv'

# Load the CSV file into a DataFrame
df = pd.read_csv('modified_dataset_info.csv')

# Define the columns to check for file availability
file_columns = ['csv', 'xlsx', 'xls']

# Check if the history CSV file exists
if os.path.exists(history_csv_path):
    # Load the history DataFrame
    df_history = pd.read_csv(history_csv_path)
    print("Resumed from existing history CSV.")
else:
    # Create a new DataFrame df_history with additional columns
    df_history = df.copy()
    df_history['eligible_url'] = df[file_columns].sum(axis=1) > 0
    df_history['file_downloaded'] = False
    df_history['json_created'] = False
    print("Created new history DataFrame.")

# Ensure temp directory exists
temp_dir = os.path.join(os.getcwd(), 'temp')
os.makedirs(temp_dir, exist_ok=True)

# Function to kill all Chromium sessions
def kill_chromium_sessions():
    for process in psutil.process_iter(['name']):
        if 'chromium' in process.info['name'].lower():
            process.kill()
            print("Killed Chromium session.")

def get_description(page):
    # Locate all paragraph elements within the div.notes section
    paragraphs = page.locator('div.notes p')
    description = '\n'.join([paragraph.inner_text().strip() for paragraph in paragraphs.element_handles()])
    return description

# Function to navigate to a URL and download the file
def navigate_and_download(url):
    browser = None
    context = None
    page = None
    try:
        playwright = sync_playwright().start()
        browser = playwright.chromium.launch(headless=False)  # Set headless=True if you don't need a browser window
        context = browser.new_context()
        page = context.new_page()
        page.goto(url)
        print(f"Navigated to {url}")

        # Identify all resource items
        resource_items = page.locator('li.resource-item')

        # Define the priorities for downloading
        #priorities = ['CSV', 'XLSX', 'XLS']
        # too many bad xlsx reports, so only download csv
        priorities = ['CSV']

        for priority in priorities:
            for i in range(resource_items.count()):
                resource_item = resource_items.nth(i)

                if priority in resource_item.inner_text():
                    # Click the Explore button within the identified row
                    explore_button = resource_item.locator('a#dropdownExplorer')
                    explore_button.click()

                    # Wait for the dropdown menu to appear
                    page.wait_for_selector('ul.dropdown-menu.show')

                    download_link = resource_item.locator('ul.dropdown-menu.show a:has-text("Download")')
                    try:
                        with page.expect_download(timeout=5000) as download_info:
                            download_link.click()
                        download = download_info.value
                        download_path = os.path.join(temp_dir, download.suggested_filename)
                        download.save_as(download_path)
                        print(f"Downloaded file: {download_path}")

                        # Print the title and description      
                        try:
                            title = page.locator('h1').inner_text().strip()
                        except:
                            title = "not_found"
                        try:
                            description = get_description(page)
                        except:
                            description = "not_found"
                        print(f"Title: {title}")
                        print(f"Description: {description}")

                        return True, title, description
                    except TimeoutError:
                        print(f"Timeout while waiting for download for {url}")
                        return False, "not_found", "not_found"

        print(f"No downloadable file found for {url}")
        return False, "not_found", "not_found"
    except Exception as e:
        print(f"An error occurred: {e}")
        return False, "not_found", "not_found"
    finally:
        if page:
            try:
                page.close()
                print("Page closed successfully.")
            except Exception as e:
                print(f"Error closing page: {e}")
        if context:
            try:
                context.close()
                print("Context closed successfully.")
            except Exception as e:
                print(f"Error closing context: {e}")
        if browser:
            try:
                browser.close()
                print("Browser closed successfully.")
            except Exception as e:
                print(f"Error closing browser: {e}")
        if 'playwright' in locals() and playwright is not None:
            try:
                playwright.stop()
                print("Playwright stopped successfully.")
            except Exception as e:
                print(f"Error stopping Playwright: {e}")

# Use Playwright to navigate to the filtered URLs and download files
count = 0
for index, row in df_history.iterrows():
    if row['eligible_url'] and not row['file_downloaded']:
        kill_chromium_sessions()
        
        # ensure no files in temp folder
        for file in os.listdir(temp_dir):
            file_path = os.path.join(temp_dir, file)
            os.remove(file_path)

        result, title, description = navigate_and_download(row['url'])
        if result:
            df_history.at[index, 'file_downloaded'] = True


            # if the file is downloaded then: get the file name, size, rows, columns and first 10 rows
            create_data_profile(row['url'], title, description, index)

            # check in the data_profiles/index folder to see if the json file is created
            # if the json file is created then update the 'json_created' column to True
            json_file = os.path.join('data_profiles', str(index), 'data_profile.json')
            if os.path.exists(json_file):
                df_history.at[index, 'json_created'] = True
                print(f"Data profile created for {row['url']}")
            else:
                print(f"Data profile not created for {row['url']}")

        count += 1

        kill_chromium_sessions()

        # Save the DataFrame every 10 runs
        if count % 10 == 0:
            df_history.to_csv(history_csv_path, index=False)
            print(f"Saved progress after {count} navigations.")

# Final save of the DataFrame
df_history.to_csv(history_csv_path, index=False)
print("Final save completed.")
