from bs4 import BeautifulSoup
import requests
import pandas as pd
from tqdm import tqdm
import sys
from datetime import datetime
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from typing import List, Dict, Any, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

EMIRATES_VALUES = [
    "abu-dhabi",
    "dubai",
    "sharjah",
    "ajman",
    "umm-al-quwain",
    "ras-al-khaimah",
    "fujairah",
]
NUM_PROPERTIES_PER_PAGE = 24

# Rate limiting and concurrency settings
MAX_WORKERS = 8  # Adjust based on your system and target website
REQUEST_DELAY = 0.1  # Delay between requests to be respectful
MAX_RETRIES = 3


def get_url(furnished="all", emirate="dubai", page=1):
    """
    args:
        furnished : one of {'all','furnished','unfurnished'}
        emirate: one of {'abu-dhabi','dubai','sharjah','ajman','umm-al-quwain','ras-al-khaimah','fujairah'}
        page (URL for page number): int

    This function returns the appropriate URL for www.bayut.com given the arguments
    """
    if page == 1:
        url = f"https://www.bayut.com/to-rent/property/{emirate}/"
    else:
        url = f"https://www.bayut.com/to-rent/property/{emirate}/page-{page}/"

    if furnished == "furnished":
        url += "?furnishing_status=furnished"
    elif furnished == "unfurnished":
        url += "?furnishing_status=unfurnished"
    return url


def scrape_property_details(
    property_url: str, fast_scrape: bool = False
) -> Dict[str, Any]:
    """Scrape individual property details with retry logic"""
    for attempt in range(MAX_RETRIES):
        try:
            if fast_scrape:
                return {"description": -1, "amenities": -1}

            response = requests.get(property_url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "lxml")
            description = -1
            amenities = -1

            try:
                desc_elem = soup.find("span", class_="_812d3f30")
                description = desc_elem.text if desc_elem else -1
            except:
                pass

            try:
                amenity_elems = soup.find_all("div", class_="_050edc8e")
                amenities = [a.text for a in amenity_elems] if amenity_elems else -1
            except:
                pass

            return {"description": description, "amenities": amenities}

        except Exception as e:
            if attempt == MAX_RETRIES - 1:
                logger.warning(
                    f"Failed to scrape property {property_url} after {MAX_RETRIES} attempts: {e}"
                )
                return {"description": -1, "amenities": -1}
            time.sleep(REQUEST_DELAY * (2**attempt))  # Exponential backoff

    return {"description": -1, "amenities": -1}


def scrape_page(
    emirate: str, furnished: str, page: int, fast_scrape: bool = False
) -> Optional[pd.DataFrame]:
    """Scrape a single page and return DataFrame"""
    try:
        url = get_url(furnished=furnished, emirate=emirate, page=page)
        response = requests.get(url, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "lxml")
        properties = soup.find_all("div", class_=["_10558b58", "_2bfcaeb9a"])

        if not properties:
            logger.warning(f"No properties found on page {page}")
            return None

        # Lists for this page
        bedrooms, bathrooms, area, prices = [], [], [], []
        locations, property_types, property_keywords = [], [], []
        furnished_bool, descriptions, amenities = [], [], []

        # Process properties in parallel if not fast_scrape
        if not fast_scrape:
            property_urls = []
            for property in properties:
                try:
                    card = soup.find("div", class_="_666f29c2")
                    if card:
                        link = card.find("a")
                        if link and link.get("href"):
                            property_urls.append("https://bayut.com" + link["href"])
                        else:
                            property_urls.append(None)
                    else:
                        property_urls.append(None)
                except:
                    property_urls.append(None)

            # Scrape property details in parallel
            with ThreadPoolExecutor(
                max_workers=min(MAX_WORKERS, len(properties))
            ) as executor:
                future_to_property = {
                    executor.submit(scrape_property_details, url, fast_scrape): i
                    for i, url in enumerate(property_urls)
                    if url
                }

                # Initialize with default values
                descriptions = [-1] * len(properties)
                amenities = [-1] * len(properties)

                for future in as_completed(future_to_property):
                    property_idx = future_to_property[future]
                    try:
                        result = future.result()
                        descriptions[property_idx] = result["description"]
                        amenities[property_idx] = result["amenities"]
                    except Exception as e:
                        logger.error(f"Error processing property {property_idx}: {e}")

        # Extract basic property information
        for property in properties:
            try:
                prices.append(property.find("span", class_="eff033a6").text)
            except:
                prices.append(-1)
            try:
                locations.append(property.find(attrs={"aria-label": "Location"}).text)
            except:
                locations.append(-1)
            try:
                property_types.append(property.find(attrs={"aria-label": "Type"}).text)
            except:
                property_types.append(-1)
            try:
                property_keywords.append(
                    property.find(attrs={"aria-label": "Title"}).text
                )
            except:
                property_keywords.append(-1)
            try:
                bedrooms.append(property.find(attrs={"aria-label": "Beds"}).text)
            except:
                bedrooms.append(-1)
            try:
                bathrooms.append(property.find(attrs={"aria-label": "Baths"}).text)
            except:
                bathrooms.append(-1)
            try:
                area.append(property.find(attrs={"aria-label": "Area"}).text)
            except:
                area.append(-1)

            if furnished != "all":
                furnished_bool.append(1 if furnished == "furnished" else 0)

        # Build DataFrame for this page
        col_dict = {
            "bedrooms": bedrooms,
            "bathrooms": bathrooms,
            "area": area,
            "prices": prices,
            "locations": locations,
            "property_types": property_types,
            "property_keywords": property_keywords,
            "furnished": furnished_bool if furnished != "all" else [],
            "description": descriptions if not fast_scrape else [-1] * len(properties),
            "amenities": amenities if not fast_scrape else [-1] * len(properties),
        }

        if furnished == "all":
            del col_dict["furnished"]

        df_page = pd.DataFrame(col_dict)
        time.sleep(REQUEST_DELAY)  # Rate limiting
        return df_page

    except Exception as e:
        logger.error(f"Error scraping page {page}: {e}")
        return None


def scrape_bayut(emirate="dubai", furnished="all", fast_scrape=False, max_workers=None):
    """Parallelized scraping function"""
    if max_workers is None:
        max_workers = MAX_WORKERS

    print(
        f"Starting parallel scrape for {emirate.capitalize()} with {max_workers} workers.."
    )
    emirate = emirate.lower().replace(" ", "-")

    assert emirate in EMIRATES_VALUES, f"emirate attr must be one of {EMIRATES_VALUES}"
    assert furnished in ["all", "furnished", "unfurnished"]

    # Get total number of properties and pages
    url = get_url(furnished=furnished, emirate=emirate, page=1)
    response = requests.get(url, timeout=15)
    response.raise_for_status()

    soup = BeautifulSoup(response.content, "lxml")
    num_properties = int(
        soup.find("span", class_="_61f285f1").text.split(" ")[-2].replace(",", "")
    )

    pages = (num_properties // NUM_PROPERTIES_PER_PAGE) + 1
    print(
        f"Found {num_properties} properties with furnished={furnished} ({pages} pages)"
    )

    # CSV file name
    csv_filename = f'properties_{emirate}_furnished={furnished}_{str(datetime.now()).split(".")[0]}.csv'

    # Write header once
    col_names = [
        "bedrooms",
        "bathrooms",
        "area",
        "prices",
        "locations",
        "property_types",
        "property_keywords",
        "furnished",
        "description",
        "amenities",
    ]
    if furnished == "all":
        col_names.remove("furnished")

    if not os.path.exists(csv_filename):
        pd.DataFrame(columns=col_names).to_csv(csv_filename, index=False)

    # Scrape pages in parallel
    successful_pages = 0
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all page scraping tasks
        future_to_page = {
            executor.submit(scrape_page, emirate, furnished, page, fast_scrape): page
            for page in range(1, pages + 1)
        }

        # Process completed tasks with progress bar
        with tqdm(total=pages, desc="Scraping pages") as pbar:
            for future in as_completed(future_to_page):
                page = future_to_page[future]
                try:
                    df_page = future.result()
                    if df_page is not None and not df_page.empty:
                        df_page.to_csv(
                            csv_filename, mode="a", header=False, index=False
                        )
                        successful_pages += 1
                    pbar.update(1)
                except Exception as e:
                    logger.error(f"Failed to process page {page}: {e}")
                    pbar.update(1)

    print(f"Scraping completed! Successfully scraped {successful_pages}/{pages} pages")
    return successful_pages


def scrape_multiple_emirates(
    emirates: List[str],
    furnished: str = "all",
    fast_scrape: bool = False,
    max_workers: int = None,
):
    """Scrape multiple emirates in parallel"""
    if max_workers is None:
        max_workers = MAX_WORKERS

    print(
        f"Starting parallel scrape for {len(emirates)} emirates with {max_workers} workers.."
    )

    with ThreadPoolExecutor(max_workers=min(max_workers, len(emirates))) as executor:
        future_to_emirate = {
            executor.submit(
                scrape_bayut,
                emirate,
                furnished,
                fast_scrape,
                max_workers // len(emirates),
            ): emirate
            for emirate in emirates
        }

        results = {}
        for future in as_completed(future_to_emirate):
            emirate = future_to_emirate[future]
            try:
                pages_scraped = future.result()
                results[emirate] = pages_scraped
                print(f"Completed {emirate}: {pages_scraped} pages scraped")
            except Exception as e:
                logger.error(f"Failed to scrape {emirate}: {e}")
                results[emirate] = 0

    return results


if __name__ == "__main__":
    scrape_bayut(emirate="dubai", furnished="all", fast_scrape=False, max_workers=8)
