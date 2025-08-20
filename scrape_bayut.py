from bs4 import BeautifulSoup
import requests
import pandas as pd
from tqdm import tqdm
import sys
from datetime import datetime
import os

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


def scrape_bayut(emirate="dubai", furnished="all", fast_scrape=False):
    print(f"Starting scrape for {emirate.capitalize()}..")
    emirate = emirate.lower().replace(" ", "-")

    assert emirate in EMIRATES_VALUES, f"emirate attr must be one of {EMIRATES_VALUES}"
    assert furnished in ["all", "furnished", "unfurnished"]

    url = get_url(furnished=furnished, emirate=emirate, page=1)
    html_text = requests.get(url).content
    soup = BeautifulSoup(html_text, "lxml")
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

    for page in tqdm(range(1, pages + 1)):
        try:
            url = get_url(furnished=furnished, emirate=emirate, page=page)
            html_text = requests.get(url).content
            soup = BeautifulSoup(html_text, "lxml")
            properties = soup.find_all("div", class_=["_10558b58", "_2bfcaeb9a"])

            # lists only for this page
            bedrooms, bathrooms, area, prices = [], [], [], []
            locations, property_types, property_keywords = [], [], []
            furnished_bool, descriptions, amenities = [], [], []

            for property in properties:
                try:
                    prices.append(property.find("span", class_="eff033a6").text)
                except:
                    prices.append(-1)
                try:
                    locations.append(
                        property.find(attrs={"aria-label": "Location"}).text
                    )
                except:
                    locations.append(-1)
                try:
                    property_types.append(
                        property.find(attrs={"aria-label": "Type"}).text
                    )
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
                    furnished_bool.append(1 if furnished else 0)
                card = soup.find("div", class_="_666f29c2")
                if not fast_scrape:
                    try:
                        card = card.find("a")
                        if card:
                            ppty_url = "https://bayut.com" + card["href"]
                            ppty_html = requests.get(ppty_url).content
                            soup_ppty = BeautifulSoup(ppty_html, "lxml")
                            try:
                                descriptions.append(
                                    soup_ppty.find("span", class_="_812d3f30").text
                                )
                            except:
                                descriptions.append(-1)
                            try:
                                temp_amenities = [
                                    a.text
                                    for a in soup_ppty.find_all(
                                        "div", class_="_050edc8e"
                                    )
                                ]
                                amenities.append(temp_amenities)
                            except:
                                amenities.append(-1)
                    except Exception as e:
                        descriptions.append(-1)
                        amenities.append(-1)
                        print(e)

            # Build DataFrame for this page
            col_dict = {
                "bedrooms": bedrooms,
                "bathrooms": bathrooms,
                "area": area,
                "prices": prices,
                "locations": locations,
                "property_types": property_types,
                "property_keywords": property_keywords,
                "furnished": furnished_bool,
                "description": descriptions,
                "amenities": amenities,
            }
            if furnished == "all":
                del col_dict["furnished"]

            df_page = pd.DataFrame(col_dict)
            df_page.to_csv(csv_filename, mode="a", header=False, index=False)

        except Exception as e:
            print(e)
            print(f"Exiting early.. scraped {page-1}/{pages}")
            raise e


if __name__ == "__main__":
    scrape_bayut(emirate="dubai", furnished="all", fast_scrape=False)
