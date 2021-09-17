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
    elements = [get_generic_template(
        title='Меню',
        image_url='https://i.postimg.cc/cCCG3PHN/pizza-logo.png',
        subtitle='Здесь вы можете выбрать один из вариантов',
        buttons_title=('Корзина', 'Акции', 'Сделать заказ')
    )]
    for product in products_per_page['data']:
        image_id = product['relationships']['main_image']['data']['id']
        image_url = get_image(
            moltin_token,
            moltin_secret,
            image_id
        )
        elements.append(
            get_generic_template(
                title=product['name'],
                image_url=image_url,
                subtitle=product['description'],
                buttons_title=['Добавить в корзину']
            )
        )
    return elements


def get_generic_template(title, image_url, subtitle, buttons_title):
    buttons = []
    for button_title in buttons_title:
        buttons.append({
            "type": "postback",
            "title": button_title,
            "payload": "DEVELOPER_DEFINED_PAYLOAD"
        })
    template = {
        "title": title,
        "image_url": image_url,
        "subtitle": subtitle,
        "buttons": buttons
    }
    return template

