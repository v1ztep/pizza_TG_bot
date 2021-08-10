import textwrap

from telegram import InlineKeyboardButton
from telegram import InlineKeyboardMarkup

from moltin import get_products_per_page


def get_menu_keyboard(context):
    user_current_page = context.user_data['menu_page']
    products_per_page = get_products_per_page(context.bot_data['moltin_token'],
                                         context.bot_data['moltin_secret'],
                                         user_current_page*6,
                                         limit_per_page=6)
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
