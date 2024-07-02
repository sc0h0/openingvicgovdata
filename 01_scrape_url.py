from playwright.sync_api import sync_playwright
import pandas as pd

url = "https://discover.data.vic.gov.au/dataset/"

def extract_dataset_info(page):
    # Wait for the datasets to load
    page.wait_for_selector(".dataset-item .dataset-heading a")

    # Extract all dataset URLs and available file types
    dataset_info = page.evaluate('''() => {
        const datasets = document.querySelectorAll(".dataset-item");
        return Array.from(datasets).map(dataset => {
            const url = dataset.querySelector(".dataset-heading a").href;
            const fileTypes = Array.from(dataset.querySelectorAll(".dataset-resources .label"))
                                   .map(file => file.getAttribute('data-format'))
                                   .join('; ');
            return { url, fileTypes };
        });
    }''')
    return dataset_info

def go_to_next_page(page):
    next_button = page.query_selector('.pagination .page-item.active + .page-item a.page-link')
    if next_button:
        next_button.click()
        page.wait_for_load_state('networkidle')
        return True
    else:
        return False

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()

    page.goto(url)

    all_dataset_info = []

    while True:
        dataset_info = extract_dataset_info(page)
        all_dataset_info.extend(dataset_info)

        # Create a temporary DataFrame to print the results of the current page
        temp_df = pd.DataFrame(dataset_info)
        print(temp_df)

        if not go_to_next_page(page):
            break

    browser.close()

# Create a DataFrame and append the URLs and available file types
df = pd.DataFrame(all_dataset_info)
df["url"] = df["url"]
print(df)

# Optionally, save the DataFrame to a CSV file
df.to_csv("dataset_info.csv", index=False)
