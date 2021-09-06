import json
import os

from dotenv import load_dotenv

from moltin import create_file
from moltin import create_image_relationship
from moltin import create_product


def main():
    load_dotenv()
    moltin_token = os.getenv('ELASTICPATH_CLIENT_ID')
    moltin_secret = os.getenv('ELASTICPATH_CLIENT_SECRET')

    with open('menu.json', 'r', encoding='utf8') as file:
        menu_json = file.read()
    menu = json.loads(menu_json)

    for pizza in menu:
        name = pizza['name']
        sku = pizza['id']
        description = pizza['description']
        price = pizza['price']
        image_url = pizza['product_image']['url']
        product = create_product(
            moltin_token,
            moltin_secret,
            name,
            sku,
            description,
            price
        )
        product_id = product['data']['id']
        image = create_file(moltin_token, moltin_secret, image_url)
        image_id = image['data']['id']
        create_image_relationship(
            moltin_token, moltin_secret, product_id, image_id
        )


if __name__ == '__main__':
    main()
