import json
import os

import requests

from moltin import get_all_categories
from moltin import get_cart_items
from moltin import get_image
from moltin import get_products_by_category_id


def send_menu(recipient_id, category):
    moltin_token = os.environ["ELASTICPATH_CLIENT_ID"]
    moltin_secret = os.environ["ELASTICPATH_CLIENT_SECRET"]
    elements = get_menu_elements(moltin_token, moltin_secret, category)
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
    print('send_menu', response.json())
    response.raise_for_status()
    return response.json()


def get_categories_id(moltin_token, moltin_secret):
    categories = {}
    all_categories = get_all_categories(moltin_token, moltin_secret)
    for category in all_categories['data']:
        categories.update({category['name']:category['id']})
    return categories


def get_menu_elements(moltin_token, moltin_secret, category):
    page_offset = 0
    limit_per_page = 10
    categories_id = get_categories_id(moltin_token, moltin_secret)
    products = get_products_by_category_id(
        moltin_token, moltin_secret,
        page_offset, limit_per_page,
        category_id=categories_id[category]
    )
    elements = [get_generic_template(
        title='Меню',
        image_url='https://i.postimg.cc/cCCG3PHN/pizza-logo.png',
        subtitle='Здесь вы можете выбрать один из вариантов',
        buttons_payload=dict.fromkeys(
            ['Корзина', 'Акции', 'Сделать заказ'],
            'DEVELOPER_DEFINED_PAYLOAD'
        )
    )]
    for product in products['data']:
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
                buttons_payload={
                    'Добавить в корзину': f"{product['id']} {product['name']}"
                }
            )
        )
    categories_id.pop(category)
    elements.append(
        get_generic_template(
            title='Не нашли нужную пиццу?',
            image_url='https://i.postimg.cc/656vP91V/few-pizzas.jpg',
            subtitle='Остальные пиццы можно посмотреть в других категориях',
            buttons_payload=categories_id
        )
    )
    return elements


def send_cart(recipient_id):
    moltin_token = os.environ["ELASTICPATH_CLIENT_ID"]
    moltin_secret = os.environ["ELASTICPATH_CLIENT_SECRET"]
    elements = get_cart_elements(moltin_token, moltin_secret, recipient_id)
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
    print('send_cart', response.json())
    response.raise_for_status()
    return response.json()


def get_cart_elements(moltin_token, moltin_secret, recipient_id):
    cart_items = get_cart_items(
        moltin_token,
        moltin_secret,
        f'fb_{recipient_id}'
    )
    elements = [get_generic_template(
        title=f'''
        К оплате: {cart_items['meta']['display_price']['with_tax']['formatted']}рублей
        ''',
        image_url='https://i.postimg.cc/6pc6968R/cart.jpg',
        subtitle=None,
        buttons_payload=dict.fromkeys(
            ['Самовывоз', 'Доставка', 'К меню'],
            'DEVELOPER_DEFINED_PAYLOAD'
        )
    )]
    for product in cart_items['data']:
        image_url = product['image']['href']
        elements.append(
            get_generic_template(
                title=f"{product['name']} ({product['quantity']} шт.)",
                image_url=image_url,
                subtitle=product['description'],
                buttons_payload={
                    'Добавить ещё одну': f"{product['product_id']} {product['name']}",
                    'Убрать из корзины': f"{product['id']} {product['name']}"
                }
            )
        )
    return elements


def get_generic_template(title, image_url, subtitle, buttons_payload):
    buttons = []
    for button_title, payload in buttons_payload.items():
        buttons.append({
            "type": "postback",
            "title": button_title,
            "payload": payload
        })
    template = {
        "title": title,
        "image_url": image_url,
        "subtitle": subtitle,
        "buttons": buttons
    }
    return template
