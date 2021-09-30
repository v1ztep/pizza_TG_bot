import json
import os

import requests

from moltin import get_cart_items


def send_menu(recipient_id, category, db):
    menu_elements = get_menu_elements(category, db)
    send_message_template(recipient_id, menu_elements)


def get_menu_elements(category, db):
    categories_id = json.loads(db.get('categories_id'))
    products_by_categories = json.loads(db.get('products_by_categories'))
    menu_elements = [get_generic_template(
        title='Меню',
        image_url='https://i.postimg.cc/cCCG3PHN/pizza-logo.png',
        subtitle='Здесь вы можете выбрать один из вариантов',
        buttons_payload=dict.fromkeys(
            ['Корзина', 'Акции', 'Сделать заказ'],
            'DEVELOPER_DEFINED_PAYLOAD'
        )
    )]
    for product in products_by_categories[category]:
        menu_elements.append(
            get_generic_template(
                title=product['title'],
                image_url=product['image_url'],
                subtitle=product['subtitle'],
                buttons_payload={
                    'Добавить в корзину': f'{product["id"]} {product["title"]}'
                }
            )
        )
    categories_id.pop(category)
    menu_elements.append(
        get_generic_template(
            title='Не нашли нужную пиццу?',
            image_url='https://i.postimg.cc/656vP91V/few-pizzas.jpg',
            subtitle='Остальные пиццы можно посмотреть в других категориях',
            buttons_payload=categories_id
        )
    )
    return menu_elements


def send_cart(recipient_id):
    moltin_token = os.environ['ELASTICPATH_CLIENT_ID']
    moltin_secret = os.environ['ELASTICPATH_CLIENT_SECRET']
    cart_elements = get_cart_elements(moltin_token, moltin_secret, recipient_id)
    send_message_template(recipient_id, cart_elements)


def get_cart_elements(moltin_token, moltin_secret, recipient_id):
    cart_items = get_cart_items(
        moltin_token,
        moltin_secret,
        f'fb_{recipient_id}'
    )
    cart_elements = [get_generic_template(
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
        cart_elements.append(
            get_generic_template(
                title=f'{product["name"]} ({product["quantity"]} шт.)',
                image_url=image_url,
                subtitle=product['description'],
                buttons_payload={
                    'Добавить ещё одну': f'{product["product_id"]} {product["name"]}',
                    'Убрать из корзины': f'{product["id"]} {product["name"]}'
                }
            )
        )
    return cart_elements


def send_message_template(recipient_id, elements):
    url = 'https://graph.facebook.com/v11.0/me/messages'
    params = {'access_token': os.environ['FB_PAGE_ACCESS_TOKEN']}
    headers = {'Content-Type': 'application/json'}
    request_content = json.dumps({
        'recipient': {
            'id': recipient_id
        },
        'message': {
            'attachment': {
                'type': 'template',
                'payload': {
                    'template_type': 'generic',
                    'elements': elements
                }
            }
        }
    })
    response = requests.post(
        url, params=params, headers=headers, data=request_content
    )
    response.raise_for_status()
    return response.json()


def get_generic_template(title, image_url, subtitle, buttons_payload):
    buttons = []
    for button_title, payload in buttons_payload.items():
        buttons.append({
            'type': 'postback',
            'title': button_title,
            'payload': payload
        })
    template = {
        'title': title,
        'image_url': image_url,
        'subtitle': subtitle,
        'buttons': buttons
    }
    return template
