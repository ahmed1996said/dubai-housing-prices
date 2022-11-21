from bs4 import BeautifulSoup
import requests
import pandas as pd
from tqdm import tqdm
import sys
from datetime import datetime


EMIRATES_VALUES = ['abu-dhabi','dubai','sharjah','ajman','umm-al-quwain','ras-al-khaimah','fujairah']
NUM_PROPERTIES_PER_PAGE = 24

def get_url(furnished='all',emirate='dubai',page=1):
    if page == 1:
        url = f'https://www.bayut.com/to-rent/property/{emirate}/'
    else:
        url = f'https://www.bayut.com/to-rent/property/{emirate}/page-{page}/'
    
    if furnished == 'furnished':
        url += '?furnishing_status=furnished'
    elif furnished == 'unfurnished':
        url += '?furnishing_status=unfurnished'
    return url


def scrape_bayut(emirate='dubai',furnished='all',fast_scrape=False): 

    print(f"Starting scrape for {emirate.capitalize()}..")
    emirate = emirate.lower().replace(' ','-')
    
    assert emirate in EMIRATES_VALUES, f'emirate attr must be one of {EMIRATES_VALUES}'
    assert furnished in ['all','furnished','unfurnished'], f"furnished attr must be one of {['all','furnished','unfurnished']}"
    
    bedrooms,bathrooms,area,prices,locations,property_types,property_keywords,furnished_bool, descriptions, amenities = [],[],[],[],[],[],[],[],[],[]

    url = get_url(furnished=furnished,emirate=emirate,page=1)
    
    html_text = requests.get(url).content
    soup = BeautifulSoup(html_text,'lxml')
    num_properties = int(soup.find('span',class_='ca3976f7').text.split(' ')[-2].replace(',',''))

    pages = (num_properties//NUM_PROPERTIES_PER_PAGE) + 1
    print(f"Found {num_properties} properties with furnished={furnished} ({pages} pages)")

    for page in tqdm(range(1,pages)):
        try:
            url = get_url(furnished=furnished,emirate=emirate,page=page)            
            html_text = requests.get(url).content
            soup = BeautifulSoup(html_text,'lxml')
            properties = soup.find_all('div',class_='d6e81fd0')        
            
            for property in properties:
                try:
                    prices.append(property.find('span',class_='f343d9ce').text)
                except:
                    prices.append(-1)
                try:
                    locations.append(property.find('div',class_='_7afabd84').text)
                except:
                    locations.append(-1)
                try:
                    property_types.append(property.find('div',class_='_9a4e3964').text)
                except:
                    property_types.append(-1)
                try:
                    property_keywords.append(property.find('h2',class_='_7f17f34f').text)
                except:
                    property_keywords.append(-1)
                temp = []
                for i in property.find('div',class_='_22b2f6ed').children:
                    try:
                        temp.append(i.text)
                    except:
                        temp.append(-1)
                try:
                    bedrooms.append(temp[0])
                except:
                    bedrooms.append(-1)
                try:
                    bathrooms.append(temp[1])
                except:
                    bathrooms.append(-1)
                try:
                    area.append(temp[2])
                except:
                    area.append(-1)
                if furnished != 'all':
                    furnished_bool.append(1 if furnished else 0)
                card = soup.find('div',class_='_4041eb80')
                if  fast_scrape: 
                    continue
                ppty_url = 'https://bayut.com'+card.find('a')['href']
                ppty_html = requests.get(ppty_url).content
                soup_ppty = BeautifulSoup(ppty_html,'lxml')
                try:
                    descriptions.append(soup_ppty.find('span',class_='_2a806e1e').text)
                except:
                    descriptions.append(-1)
                try:
                    amenities.append(soup_ppty.find('div',class_='e475b606').text)
                except:
                    amenities.append(-1)
        except Exception as e:
            print(e)
            print(f"Exiting early.. scraped {page-1}/{pages}")
            break

    col_dict = {
    "bedrooms" : bedrooms,
    "bathrooms": bathrooms,
    "area": area,
    "prices" : prices,
    "locations" : locations,
    "property_types" : property_types,
    "property_keywords" : property_keywords,
    "furnished": furnished_bool,
    "description": descriptions,
    "amenities": amenities
    }
    if furnished == 'all':
        del col_dict['furnished']
    df = pd.DataFrame(col_dict)
    if fast_scrape:
        del descriptions
        del amenities

    df.to_csv(f'properties_{emirate}_furnished={furnished}_{str(datetime.now()).split(".")[0]}.csv',index=False)

if __name__ == '__main__':
    scrape_bayut(emirate='dubai',furnished='all',fast_scrape=False)

