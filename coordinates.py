import os

import requests
from dotenv import load_dotenv


def fetch_coordinates(apikey, place):
    base_url = "https://geocode-maps.yandex.ru/1.x"
    params = {"geocode": place, "apikey": apikey, "format": "json"}
    response = requests.get(base_url, params=params)
    print(response.text)
    response.raise_for_status()
    found_places = response.json()['response']['GeoObjectCollection']['featureMember']
    most_relevant = found_places[0]
    lon, lat = most_relevant['GeoObject']['Point']['pos'].split(" ")
    return lon, lat


def main():
    load_dotenv()
    yandex_geocoder_api = os.getenv('YANDEX_GEOCODER_API')
    lon, lat = fetch_coordinates(yandex_geocoder_api, 'sdfgsdfgsdf sd')
    print(lon, lat)

if __name__ == '__main__':
    main()