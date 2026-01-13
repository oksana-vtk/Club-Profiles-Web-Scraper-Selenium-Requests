import random

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pandas as pd
from dotenv import load_dotenv
import os
import logging
import requests
from bs4 import BeautifulSoup


pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)


# Load environment variables from .env
load_dotenv()


# CONFIG
BASE_URL = os.getenv("BASE_URL")
SEARCH_URL = os.getenv("SEARCH_URL")
OUTPUT_FILE_1 = os.getenv("OUTPUT_FILE_1")
OUTPUT_FILE_2 = os.getenv("OUTPUT_FILE_2")
OUTPUT_FILE_PARTIAL = os.getenv("OUTPUT_FILE_PARTIAL")
LOG_FILE = os.getenv("LOG_FILE")
PARTIAL_SAVE_EVERY = int(os.getenv("PARTIAL_SAVE_EVERY", 50))
POP_UP_SELECTOR = os.getenv("POP_UP_SELECTOR")
SEARCH_SELECTOR = os.getenv("SEARCH_SELECTOR")
EXPANDED_SEARCH_PANEL = os.getenv("EXPANDED_SEARCH_PANEL")
BUTTON_PATH = os.getenv("BUTTON_PATH")
RESULTS_SELECTOR = os.getenv("RESULTS_SELECTOR")
NAME_LINK_SELECTOR = os.getenv("NAME_LINK_SELECTOR")
INSTALLATION_TAB_XPATH = os.getenv("INSTALLATION_TAB_XPATH")
INSTALL_PANEL_XPATH = os.getenv("INSTALL_PANEL_XPATH")
PRESIDENT_PANEL_XPATH = os.getenv("PRESIDENT_PANEL_XPATH")
PRESIDENT_SELECTOR = os.getenv("PRESIDENT_SELECTOR")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/118.0.0.0 Safari/537.36"
}


# Selenium options
def create_driver():

    options = webdriver.ChromeOptions()
    options.add_argument('--headless=new')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument("--start-maximized")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    options.add_argument("--enable-javascript")

    return webdriver.Chrome(options=options)


# Create a blank line in a log file without timestamp
class BlankLineFormatter(logging.Formatter):
    def format(self, record):
        # If the message is empty or whitespace only, return just a newline (no timestamp)
        if not record.msg.strip():
            return "\n"
        return super().format(record)


# Create logger
def setup_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    log_path = LOG_FILE

    # Avoid re-adding handlers if already set
    if not logger.handlers:
        file_handler = logging.FileHandler(log_path, mode="a", encoding="utf-8")
        stream_handler = logging.StreamHandler()
        formatter = BlankLineFormatter('%(asctime)s - %(levelname)s - %(message)s', datefmt="%Y-%m-%d %H:%M:%S")
        file_handler.setFormatter(formatter)
        stream_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)
        return logger


def extract_all_clubs(url):

    # Launch logger
    logger = setup_logger()
    logger.info("")
    logger.info(f"URL: {url}")

    # Create Chrome webdriver for Selenium
    driver = create_driver()

    # Launch Selenium
    driver.get(url)
    logger.info("Start driver...")

    wait = WebDriverWait(driver, 10)

    # Close AFT registration warning popup if present
    try:
        close_btn = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, POP_UP_SELECTOR))
        )
        driver.execute_script("arguments[0].click();", close_btn)
        logger.info("Popup closed successfully.")
        time.sleep(1)
    except Exception as e:
        logger.info(f"No registration popup found: {e}")

    # Expand search filters panel
    try:
        logger.info("Trying to open search panel...")

        search_toggle = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, SEARCH_SELECTOR)))
        driver.execute_script("arguments[0].click();", search_toggle)
        time.sleep(1)  # allow animation

        # Wait until panel is expanded (CSS class "in" appears)
        wait.until(EC.visibility_of_element_located((By.ID, EXPANDED_SEARCH_PANEL)))
        logger.info("Search panel expanded successfully!")

    except Exception as e:
        logger.info("Failed to expand search panel:", e)

    # wait for the button and click
    button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, BUTTON_PATH))
    )
    button.click()

    # Wait until results are loaded
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, RESULTS_SELECTOR)))

    # Find all clubs
    clubs = driver.find_elements(By.CSS_SELECTOR, RESULTS_SELECTOR)
    logger.info(f"Found {len(clubs)} clubs")

    results = []
    club_index = 1

    for club in clubs:
        logger.info(f"Extraction [{club_index}/{len(clubs)}]")
        try:
            # Club name and ID
            name_link = club.find_element(By.CSS_SELECTOR, NAME_LINK_SELECTOR)
            full_name = name_link.text

            club_url_part = name_link.get_attribute("data-url")
            club_url = BASE_URL + club_url_part

            club_id = full_name.split("(")[-1].replace(")", "")

            # Find tags with address and
            dd_elements = club.find_elements(By.TAG_NAME, "dd")

            # Address
            address = dd_elements[1].text.strip() if len(dd_elements) > 1 else "/"

            # Split into zip and city
            if "," in address:
                zip_code, city = [part.strip() for part in address.split(",", 1)]
            else:
                zip_code, city = "/", address

            # Court info (optional)
            court_info = dd_elements[2].text.strip() if len(dd_elements) > 2 else "/"

            # Club image
            try:
                img = club.find_element(By.CSS_SELECTOR, "img.profile")
                img_url = img.get_attribute("src")
            except:
                img_url = "/"

            club_data = {
                "club_index": club_index,
                "id": club_id,
                "name": full_name,
                "url": club_url,
                "address": address,
                "postal code": zip_code,
                "city": city,
                "court_info": court_info,
                "image": img_url
            }

            results.append(club_data)

            club_index += 1

        except Exception as e:
            logger.info("Error parsing a club:", e)

    # Save to CSV
    df_clubs = pd.DataFrame(results)

    df_clubs.to_csv(OUTPUT_FILE_1, index=False, encoding='utf-8-sig', sep='*')
    logger.info(f"Saved {len(df_clubs)} total records to {OUTPUT_FILE_1}")

    logger.info(f"Club data saved to {OUTPUT_FILE_1}")

    driver.quit()


def extract_all_clubs_info():

    # Launch logger
    logger = setup_logger()

    logger.info("")
    logger.info(f"Start extracting clubs info")

    results = []

    # Read all URLs from CSV using pandas
    df_clubs = pd.read_csv(OUTPUT_FILE_1, sep="*", encoding="utf-8-sig")

    if "url" not in df_clubs.columns:
        logger.error(f"No 'url' column found in clubs_list.csv")
        return

    urls = df_clubs["url"].dropna().tolist()

    logger.info(f"Read file: {OUTPUT_FILE_1}")
    logger.info(f"Found {len(urls)} product URLs to extract product info")

    driver = create_driver()
    wait = WebDriverWait(driver, 10)

    # Parse each event page
    for idx, row in df_clubs.iterrows():

        club_index = row["club_index"]
        club_id = row["id"]
        club_name = row["name"]
        url = row["url"]
        # address = row["address"]
        postal_code = row["postal code"]
        city = row["city"]
        court_info = row["court_info"]
        image = row["image"]

        logger.info(f"Extracting product [{idx + 1}/{len(urls)}] info, url: {url}")

        installations = []

        try:
            # =====================================================
            # PART 1 — Requests + BeautifulSoup (Static content)
            # =====================================================

            response = requests.get(url, headers=HEADERS, timeout=10)

            if response.status_code != 200:
                logger.warning(f"Failed to fetch {url}: {response.status_code}")
                continue

            soup = BeautifulSoup(response.content, "html.parser")

            # Full Name
            h1_tag = soup.find("div", class_="detail-body").find("h1")
            full_name = h1_tag.get_text(separator=" ", strip=True)
            full_name_clean = full_name.replace("javascript:void(0)", "").strip()

            # Select the <div> containing club info
            club_info_div = soup.find("div", id="colInfo")

            # All <dd> elements
            dd_elements = club_info_div.find_all("dd") if club_info_div else []

            # Street & number
            street = dd_elements[0].get_text(strip=True) if len(dd_elements) > 0 else "/"

            # Zip, city, country
            zip_city_country = dd_elements[1].get_text(strip=True) if len(dd_elements) > 1 else "/"
            parts = zip_city_country.split(" ", 1)
            zip_code = parts[0] if len(parts) > 0 else "/"
            city_country = parts[1] if len(parts) > 1 else "/"

            phone = "/"
            email = "/"
            website = "/"
            president_name = "/"

            for dd in dd_elements[2:len(dd_elements)+1]:
                text = dd.get_text(strip=True)
                a_tag = dd.find("a")

                # Detect email
                if a_tag and "mailto:" in a_tag.get("href", "").lower():
                    email = a_tag.get("href", "").replace("mailto:", "").strip()
                    continue

                # Detect website
                if a_tag:
                    href = a_tag.get("href", "").strip()
                    if href.startswith("http"):
                        website = href
                        continue

                # Detect phone (contains digits, maybe spaces or plus sign)
                if any(char.isdigit() for char in text) and not text.startswith("Extérieur"):
                    phone = text
                    continue

            # Get the last column (Total)
            total_members_element = soup.select_one("table.table-infor tbody tr td:last-child")
            total_members = total_members_element.get_text(strip=True) if total_members_element else "/"

            logger.info(f"Extraction using requests was successful")

            # =====================================================
            # PART 2 — Selenium (Dynamic content: President)
            # =====================================================
            try:
                driver.get(url)

                time.sleep(random.uniform(3, 4))

                logger.info(f"Start Selenium for dynamic content")

                # Close AFT registration warning popup if present
                if idx == 0:
                    try:

                        close_btn = wait.until(EC.element_to_be_clickable(
                            (By.CSS_SELECTOR, POP_UP_SELECTOR)))
                        driver.execute_script("arguments[0].click();", close_btn)
                        logger.info("Popup closed successfully")
                        time.sleep(1)
                    except Exception as e:
                        logger.info(f"No registration popup found: {e}")
                        pass

                # Click the Installation tab to extract installations
                time.sleep(random.uniform(4, 5))
                try:
                    installation_tab = wait.until(EC.element_to_be_clickable((By.XPATH, INSTALLATION_TAB_XPATH)))
                    #installation_tab.click()
                    driver.execute_script("arguments[0].click();", installation_tab)
                    logger.info("Clicked Installation tab")

                    # Wait for Installations content to appear
                    install_panel = wait.until(EC.visibility_of_element_located(
                        (By.XPATH, INSTALL_PANEL_XPATH)))

                    # Loop through each installation block (dl)
                    dl_elements = install_panel.find_elements(By.XPATH, ".//div[contains(@class,'panel-body')]//dl")

                    for dl in dl_elements:
                        dd_texts = [dd.text.strip() for dd in dl.find_elements(By.TAG_NAME, "dd") if dd.text.strip()]
                        if dd_texts:
                            first_dd = dd_texts[0]
                            if first_dd:
                                installations.append(first_dd)
                except Exception as e:
                    logger.error(f"Could not click Installation tab: {e}")

                # Click the Comité tab to extract President info
                time.sleep(random.uniform(2, 3))
                try:
                    comite_tab = wait.until(EC.element_to_be_clickable((By.ID, "tabResult")))
                    comite_tab.click()
                    logger.info("Clicked Comité tab")

                    # Wait until Comité panel content loads
                    wait.until(EC.visibility_of_element_located((By.ID, "tabClubCommittee")))

                    # Wait until the Président panel is visible
                    president_panel = wait.until(EC.visibility_of_element_located(
                        (By.XPATH, PRESIDENT_PANEL_XPATH)))

                    # Extract the President info
                    member_tag = president_panel.find_element(By.CSS_SELECTOR, PRESIDENT_SELECTOR)
                    president_name = member_tag.text.strip()
                    # president_url = member_tag.get_attribute("href")
                except Exception as e:
                    logger.error(f"Could not click Comité tab: {e}")

            except Exception as e:
                logger.error(f"Selenium error for {url}: {e}")

            # Correct postal_code (some postal codes doesnt exist and perform as /)
            if pd.notna(postal_code) and str(postal_code).isdigit():
                postal_code_value = int(postal_code)
            else:
                postal_code_value = postal_code

            # Save collected data
            club_info = {
                "club_index": club_index,
                "club_id": club_id,
                "name_preview": club_name,
                #"address": address,
                "postal_code_preview": postal_code_value,
                "city_preview": city,
                "preview_line_3": court_info,
                "detailed_url": url,
                "logo_url_preview": image,
                "full_name": full_name_clean,
                "full_address": street,
                "PostalCityCountry": f"{zip_code} {city_country}",
                #"zip": zip_code,
                #"city_country": city_country,
                "phone": phone,
                "website": website,
                "email": email,
                "total_members": total_members
            }

            # Fill up to 4 installation columns
            for i in range(4):
                col_name = f"installation_{i + 1}"
                club_info[col_name] = installations[i] if i < len(installations) else "/"

            # Add President
            club_info["president"] = president_name

            results.append(club_info)

            logger.info(f"Extraction successful")

            # Partial save every `partial_save_every` clubs
            if (idx + 1) % PARTIAL_SAVE_EVERY == 0:
                df_partial = pd.DataFrame(results)
                df_partial.to_csv(OUTPUT_FILE_PARTIAL, index=False, encoding="utf-8-sig", sep="*")
                logger.info(f"Saved partial CSV after {idx + 1} clubs")

        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")

    # Save to CSV
    df_clubs_info = pd.DataFrame(results)

    df_clubs_info.to_csv(OUTPUT_FILE_2, index=False, encoding='utf-8-sig', sep='*')
    logger.info(f"Saved {len(df_clubs_info)} total records to {OUTPUT_FILE_2}")

    driver.quit()


if __name__ == "__main__":

    extract_all_clubs(SEARCH_URL)

    # extract_all_clubs_info()



