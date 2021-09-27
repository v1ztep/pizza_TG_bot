import json
import os

from dotenv import load_dotenv

from connect_to_redis_db import get_database_connection
from moltin import get_all_categories
from moltin import get_image
from moltin import get_products_by_category


def get_categories_id(moltin_token, moltin_secret):
    categories_id = {}
    all_categories = get_all_categories(moltin_token, moltin_secret)
    for category in all_categories['data']:
        categories_id.update({category['name']:category['id']})
    return categories_id


def get_products_by_categories(moltin_token, moltin_secret, categories_id):
    page_offset = 0
    limit_per_page = 10
    category_names = ('Основные', 'Особые', 'Сытные', 'Острые')
    products_by_categories = {}
    for category in category_names:
        products_by_category = get_products_by_category(
            moltin_token, moltin_secret,
            page_offset, limit_per_page,
            category_id=categories_id[category]
        )
        products_by_category_with_image = get_products_by_category_with_image(
            products_by_category, moltin_token, moltin_secret
        )
        products_by_categories[category] = products_by_category_with_image
    return products_by_categories


def get_products_by_category_with_image(
        products_by_category, moltin_token, moltin_secret
):
    products_by_category_with_image = []
    for product in products_by_category['data']:
        image_id = product['relationships']['main_image']['data']['id']
        image_url = get_image(moltin_token, moltin_secret, image_id)
        products_by_category_with_image.append({
            'title': product['name'],
            'image_url': image_url,
            'subtitle': product['description'],
            'id': product['id']
        })
    return products_by_category_with_image


def main():
    load_dotenv()
    moltin_token = os.environ["ELASTICPATH_CLIENT_ID"]
    moltin_secret = os.environ["ELASTICPATH_CLIENT_SECRET"]
    db = get_database_connection()

    categories_id = get_categories_id(moltin_token, moltin_secret)
    db.set('categories_id', json.dumps(categories_id))

    products_by_categories = get_products_by_categories(
        moltin_token, moltin_secret, categories_id
    )
    db.set('products_by_categories', json.dumps(products_by_categories))


if __name__ == '__main__':
    main()
