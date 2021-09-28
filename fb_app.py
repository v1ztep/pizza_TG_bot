import os
import json
from dotenv import load_dotenv

import requests
from flask import Flask, request

from connect_to_redis_db import get_database_connection
from facebook_contents import send_cart
from facebook_contents import send_menu
from moltin import add_product_to_cart
from moltin import remove_item_in_cart

load_dotenv()
app = Flask(__name__)


@app.route('/', methods=['GET'])
def verify():
    if request.args.get('hub.mode') == 'subscribe' and request.args.get('hub.challenge'):
        if not request.args.get('hub.verify_token') == os.environ['FB_APP_VERIFY_TOKEN']:
            return 'Verification token mismatch', 403
        return request.args['hub.challenge'], 200

    return 'Hello world', 200


@app.route('/', methods=['POST'])
def webhook():
    data = json.loads(request.data.decode('utf-8'))
    if data['object'] == 'page':
        for entry in data['entry']:
            for messaging_event in entry['messaging']:
                if messaging_event.get('message'):
                    sender_id = messaging_event['sender']['id']
                    handle_users_reply(sender_id, '/start')
                elif messaging_event.get('postback'):
                    sender_id = messaging_event['sender']['id']
                    postback = messaging_event['postback']
                    handle_users_reply(sender_id, postback)
    return 'ok', 200


def handle_start(sender_id, message_text, db):
    send_menu(sender_id, 'Основные', db)
    return 'HANDLE_MENU'


def menu_handler(sender_id, message_text, db):
    if message_text['title'] in ('Основные', 'Особые', 'Сытные', 'Острые'):
        send_menu(sender_id, message_text['title'], db)
        return 'HANDLE_MENU'
    elif message_text['title'] == 'Добавить в корзину':
        add_product_to_cart(
            moltin_token=os.environ['ELASTICPATH_CLIENT_ID'],
            moltin_secret=os.environ['ELASTICPATH_CLIENT_SECRET'],
            cart_id=f'fb_{sender_id}',
            product_id=message_text['payload'].split()[0],
            quantity=1
        )
        send_message(
            sender_id,
            f'В корзину добавлена пицца {message_text["payload"].split(maxsplit=1)[1]}'
        )
        return 'HANDLE_MENU'
    elif message_text['title'] == 'Корзина':
        send_cart(sender_id)
        return 'HANDLE_CART'


def cart_handler(sender_id, message_text, db):
    if message_text['title'] == 'К меню':
        send_menu(sender_id, 'Основные', db)
        return 'HANDLE_MENU'
    elif message_text['title'] == 'Добавить ещё одну':
        add_product_to_cart(
            moltin_token=os.environ['ELASTICPATH_CLIENT_ID'],
            moltin_secret=os.environ['ELASTICPATH_CLIENT_SECRET'],
            cart_id=f'fb_{sender_id}',
            product_id=message_text['payload'].split()[0],
            quantity=1
        )
        send_message(
            sender_id,
            f'В корзину добавлена пицца {message_text["payload"].split(maxsplit=1)[1]}'
        )
        send_cart(sender_id)
        return 'HANDLE_CART'
    elif message_text['title'] == 'Убрать из корзины':
        remove_item_in_cart(
            moltin_token=os.environ['ELASTICPATH_CLIENT_ID'],
            moltin_secret=os.environ['ELASTICPATH_CLIENT_SECRET'],
            cart_id=f'fb_{sender_id}',
            cart_item_id=message_text['payload'].split()[0]
        )
        send_message(
            sender_id,
            f'Пицца {message_text["payload"].split(maxsplit=1)[1]} удалена из корзины'
        )
        send_cart(sender_id)
        return 'HANDLE_CART'


def handle_users_reply(sender_id, message_text):
    db = get_database_connection()
    states_functions = {
        'START': handle_start,
        'HANDLE_MENU': menu_handler,
        'HANDLE_CART': cart_handler
    }
    recorded_state = db.get(f'fb_{sender_id}')
    if not recorded_state or recorded_state.decode('utf-8') not in states_functions.keys():
        user_state = 'START'
    else:
        user_state = recorded_state.decode('utf-8')
    if message_text == '/start':
        user_state = 'START'
    state_handler = states_functions[user_state]
    next_state = state_handler(sender_id, message_text, db)
    db.set(f'fb_{sender_id}', next_state)


def send_message(recipient_id, message_text):
    params = {'access_token': os.environ['FB_PAGE_ACCESS_TOKEN']}
    headers = {'Content-Type': 'application/json'}
    request_content = json.dumps({
        'recipient': {
            'id': recipient_id
        },
        'message': {
            'text': message_text
        }
    })
    response = requests.post(
        'https://graph.facebook.com/v2.6/me/messages',
        params=params, headers=headers, data=request_content
    )
    response.raise_for_status()


if __name__ == '__main__':
    app.run(debug=True)
