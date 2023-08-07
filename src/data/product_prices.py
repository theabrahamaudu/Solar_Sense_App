"""
Module to retrive product prices from `Jumia.com.ng`
"""

import requests
from lxml import html
import re
import datetime
import pandas as pd


products = {
    "Battery 100Ah 12V": "100Ah 12V battery",
    "Battery 150Ah 12V": "150Ah 12V battery",
    "Battery 200Ah 12V": "200Ah 12V battery",
    "Battery 220Ah 12V Tubular": "220Ah 12V tubular battery",

    "Mono Solar Panel 100W 12V": "100W 12V mono solar panel",
    "Mono Solar Panel 200W 12V": "200W 12V mono solar panel",
    "Mono Solar Panel 200W 24V": "200W 24V mono solar panel",
    "Mono Solar Panel 250W 24V": "250W 24V mono solar panel",
    "Mono Solar Panel 300W 24V": "300W 24V mono solar panel",
    "Mono Solar Panel 400W 24V": "400W 24V mono solar panel",

    "Inverter 1 KVA 12V": "1Kva 12v sine wave inverter",
    "Inverter 1.5 KVA 24V": "1.5Kva 24v inverter",
    "Inverter 2.5 KVA 24V": "2.5Kva 24v inverter",
    "Inverter 3.5 KVA 24V": "3.5Kva 24v inverter",
    "Inverter 3.5 KVA 48V": "3.5Kva 48v inverter",
    "Inverter 5 KVA 48V": "5Kva 48v inverter",
    "Inverter 7.5 KVA 48V": "7.5Kva 48v inverter",
    "Inverter 10 KVA 48V": "10Kva 48v inverter",

    "MPPT Charge Controller 60A": "60A MPPT charge controller",
    "MPPT Charge Controller 80A": "80A MPPT charge controller",
    "MPPT Charge Controller 120A": "120A MPPT charge controller",
    "PWM Charge Controller 30A": "30A PWM charge controller",
    "PWM Charge Controller 60A": "60A PWM charge controller",
    "PWM Charge Controller 80A": "80A PWM charge controller"
}


def get_product_info_by_search(search_string):
    product_name_xpath = "/html/body/div[1]/main/div[2]/div[3]/section/div/article/a/div[2]/h3"
    price_xpath = "/html/body/div[1]/main/div[2]/div[3]/section/div/article/a/div[2]/div[1]"

    url = f"https://www.jumia.com.ng/catalog/?q={search_string.replace(' ', '+')}"

    product_info_list = []
    response = requests.get(url)
    
    if response.status_code != 200:
        raise Exception(f"Failed to fetch the page. Status code: {response.status_code}")

    tree = html.fromstring(response.content)
    product_names = tree.xpath(product_name_xpath)
    prices = tree.xpath(price_xpath)

    for product_name, price in zip(product_names, prices):
        name = product_name.text_content().strip()
        price_value = price.text_content().strip()

        # Calculate the proportion of words in the search string present in the product name
        search_terms = search_string.lower().split()
        word_count = sum(term.lower() in name.lower() for term in search_terms)
        proportion = word_count / len(search_terms)

        # Skip items with "None" prices
        if not price_value.strip():
            continue

        # Extract the integer component of the price using regular expressions
        price_match = re.search(r"(\d[\d,.]*)", price_value)
        if price_match:
            price_str = price_match.group(1).replace(",", "")
            price_int = int(float(price_str))
        else:
            continue

        # Add the item to the list only if it contains a good proportion of the search terms
        if proportion >= 0.5:
            product_info_list.append({"name": name, "price": price_int})

    return product_info_list


def round_to_nearest_500(price):
    return round(price / 500) * 500


def get_average_prices(products_dict):
    results_dict = {}
    table_data = {}

    current_date = datetime.datetime.now().strftime('%Y-%m-%d')
    results_dict['Date'] = current_date
    table_data['Date'] = [current_date]

    for key, search_term in products_dict.items():
        try:
            product_info_list = get_product_info_by_search(search_term)
            prices = [item['price'] for item in product_info_list if item['price'] is not None]
            avg_price = sum(prices) / len(prices) if prices else None
            rounded_price = round_to_nearest_500(avg_price) if avg_price is not None else None
            results_dict[key] = rounded_price
            table_data[key] = [rounded_price]
        except Exception as e:
            print(f"Error while searching for '{search_term}': {e}")
            results_dict[key] = None
            table_data[key] = [None]

    df = pd.DataFrame(table_data)

    return results_dict, df
