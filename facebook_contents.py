import json
import os

import requests

from moltin import get_image
from moltin import get_products


def send_menu(recipient_id):
    moltin_token = os.environ["ELASTICPATH_CLIENT_ID"]
    moltin_secret = os.environ["ELASTICPATH_CLIENT_SECRET"]
    elements = get_elements(moltin_token, moltin_secret)
    url = 'https://graph.facebook.com/v11.0/me/messages'
    params = {"access_token": os.environ["FB_PAGE_ACCESS_TOKEN"]}
    headers = {"Content-Type": "application/json"}
    request_content = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "attachment": {
                "type": "template",
                "payload": {
                    "template_type": "generic",
                    "elements": elements
                }
            }
        }
    })
    response = requests.post(
        url, params=params, headers=headers, data=request_content
    )
    print(response.json())
    response.raise_for_status()
    return response.json()


def get_elements(moltin_token, moltin_secret):
    user_current_page = 0
    on_page = 5
    products_per_page = get_products(
        moltin_token,
        moltin_secret,
        page_offset=user_current_page * on_page,
        limit_per_page=on_page
    )
    elements = []
    for product in products_per_page['data']:
        image_id = product['relationships']['main_image']['data']['id']
        image = get_image(
            moltin_token,
            moltin_secret,
            image_id
        )
        elements.append({
            "title": product['name'],
            "image_url": image,
            "subtitle": product['description'],
            "buttons": [{
                    "type": "postback",
                    "title": "Добавить в корзину",
                    "payload": "DEVELOPER_DEFINED_PAYLOAD"
                }]
        })
    return elements