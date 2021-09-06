import json
import os

from dotenv import load_dotenv
from slugify import slugify

from moltin import create_entry
from moltin import create_field
from moltin import create_flow


def main():
    load_dotenv()
    moltin_token = os.getenv('ELASTICPATH_CLIENT_ID')
    moltin_secret = os.getenv('ELASTICPATH_CLIENT_SECRET')

    flow_name = 'Pizzeria'
    flow_description = 'pizzeria addresses'
    flow_fields = {
        'Address': 'string',
        'Alias': 'string',
        'Longitude': 'float',
        'Latitude': 'float'
    }

    flow = create_flow(moltin_token, moltin_secret, flow_name, flow_description)
    flow_id = flow['data']['id']

    for field_name, field_type in flow_fields.items():
        create_field(
            moltin_token,
            moltin_secret,
            field_name,
            field_type,
            f'{field_name} {field_type}',
            flow_id
        )

    with open("addresses.json", "r", encoding="utf8") as file:
        addresses_json = file.read()
    addresses = json.loads(addresses_json)

    for address in addresses:
        entry_fields = {
            'address': address['address']['full'],
            'alias': address['alias'],
            'longitude': address['coordinates']['lon'],
            'latitude': address['coordinates']['lat']
        }
        create_entry(moltin_token, moltin_secret, slugify(flow_name), entry_fields)


if __name__ == '__main__':
    main()
