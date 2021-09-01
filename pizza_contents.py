import textwrap
from itertools import count

from geopy import distance
from telegram import InlineKeyboardButton
from telegram import InlineKeyboardMarkup

from moltin import get_entries
from moltin import get_products


def get_menu_keyboard(context):
    on_page = 6
    user_current_page = context.user_data['menu_page']
    products_per_page = get_products(context.bot_data['moltin_token'],
                                     context.bot_data['moltin_secret'],
                                     page_offset=user_current_page * on_page,
                                     limit_per_page=on_page)
    keyboard = []
    for product in products_per_page['data']:
        keyboard.append([InlineKeyboardButton(product['name'],
                                              callback_data=product['id'])])
    product_current_page = products_per_page['meta']['page']['current']
    product_total_page = products_per_page['meta']['page']['total']
    if product_total_page > 1:
        pagination_buttons = get_pagination_buttons(product_current_page,
                                                      product_total_page)
        keyboard.append(pagination_buttons)
    keyboard.append([InlineKeyboardButton("Корзина", callback_data='to_cart')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    return reply_markup


def get_pagination_buttons(product_current_page, product_total_page):
    if product_current_page == 1:
        pagination_buttons = (
            [InlineKeyboardButton("Следующая ➡️",callback_data='forward +1')]
        )
    elif product_current_page == product_total_page:
        pagination_buttons = (
            [InlineKeyboardButton("⬅️ Предыдущая",callback_data='back -1')]
        )
    else:
        pagination_buttons = (
            [InlineKeyboardButton("⬅️ Пред", callback_data='back -1'),
             InlineKeyboardButton("След ➡️", callback_data='forward +1')]
        )
    return pagination_buttons


def get_description_text(product):
    text = f'''
        <b>{product['name']}</b>
        Стоимость: {product['price'][0]['amount']}рублей

        <i>{product['description']}</i>
        '''
    return textwrap.dedent(text)


def get_description_keyboard(product_id):
    keyboard = [[InlineKeyboardButton('Положить в корзину',
                                      callback_data=product_id)],
                [InlineKeyboardButton("Корзина", callback_data='to_cart')],
                [InlineKeyboardButton("В меню", callback_data='to_menu')]
                ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    return reply_markup


def get_cart_text(cart_items):
    text = ''
    for product in cart_items['data']:
        text += f'''
            <b>{product['name']}</b>
            <i>{product['description']}</i>
            {product['quantity']} пицц в корзине на сумму {product['meta']
            ['display_price']['with_tax']['value']['formatted']}рублей
            '''
    text += f'''
            <b>К оплате: {cart_items['meta']['display_price']['with_tax']
            ['formatted']}рублей</b>
            '''
    return textwrap.dedent(text)


def get_cart_keyboard(cart_items):
    keyboard = []
    for product in cart_items['data']:
        keyboard.append([InlineKeyboardButton(f"Убрать из корзины {product['name']}",
                                              callback_data=product['id'])])
    if keyboard:
        keyboard.append(
            [InlineKeyboardButton('Оплатить', callback_data='to_payment')])
    keyboard.append([InlineKeyboardButton('В меню', callback_data='to_menu')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    return reply_markup


def get_location_text(distance_to_user, nearest_pizzeria):
    if distance_to_user <= 0.5:
        text = f''' 
                Может заберёте пиццу из нашей пиццерии неподалёку? 
                Она всего в <b>{int(distance_to_user * 1000)}</b> метрах от Вас!
                Вот её адрес: <i><b>{nearest_pizzeria['address']}</b></i>.

                А можем и бесплатно доставить, нам не сложно ;)
                '''
    elif distance_to_user <= 5:
        text = f''' 
                Похоже придётся ехать до вас на самокате. Доставка будет 
                стоить 100 рублей. Доставляем или самовывоз? 
                '''
    elif distance_to_user <= 20:
        text = f'''
                Похоже придётся ехать до вас на авто. Доставка будет стоить 
                300 рублей. Доставляем или самовывоз?
                '''
    else:
        text = f''' 
                Простите, но так далеко мы пиццу не доставим. Ближайшая 
                пиццерия аж в <b>{int(distance_to_user)}</b> километрах от Вас!
                '''
    return textwrap.dedent(text)


def get_location_keyboard(distance_to_user):
    keyboard = [[InlineKeyboardButton('Самовывоз', callback_data='self-pickup')]]
    if distance_to_user <= 20:
        keyboard.append(
            [InlineKeyboardButton("Доставка", callback_data='delivery')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    return reply_markup


def get_all_pizzerias(context, flow_slug='pizzeria'):
    on_page = 25
    pizzerias = []

    for current_page in count():
        entries = get_entries(context.bot_data['moltin_token'],
                              context.bot_data['moltin_secret'],
                              flow_slug,
                              page_offset=current_page * on_page,
                              limit_per_page=on_page)
        pizzerias.extend(entries['data'])
        if (current_page + 1) == entries['meta']['page']['total']:
            break

    return pizzerias


def get_distance_to_user(pizzeria, user_position):
    return distance.distance(user_position,
                             (pizzeria['latitude'], pizzeria['longitude'])
                             ).km


def get_deliveryman_text(cart_items, distance_to_user):
    text = '<b>Сообщение для курьера!</b>'
    total_pizzas = 0
    delivery_cost = get_delivery_cost(distance_to_user)
    for product in cart_items['data']:
        text += f'''
            <b>{product['name']}</b>
            {product['quantity']} пицц на сумму {product['meta']
            ['display_price']['with_tax']['value']['formatted']}рублей
            '''
        total_pizzas += product['quantity']
    text += f'''
            <i>Необходимо доставить {total_pizzas} пицц на сумму: {cart_items['meta']
            ['display_price']['with_tax']['formatted']}рублей</i> (<b>Оплачено</b>)
            <b>К оплате за доставку: {delivery_cost}рублей</b>
            '''
    return textwrap.dedent(text)


def get_delivery_cost(distance_to_user):
    if distance_to_user <= 0.5:
        delivery_cost = 0
    elif distance_to_user <= 5:
        delivery_cost = 100
    else:
        delivery_cost = 300
    return delivery_cost
