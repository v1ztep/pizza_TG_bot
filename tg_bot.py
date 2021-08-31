import logging
import os
import textwrap
from functools import partial

import telegram
from dotenv import load_dotenv
from telegram import InlineKeyboardButton
from telegram import InlineKeyboardMarkup
from telegram import LabeledPrice
from telegram.ext import CallbackQueryHandler
from telegram.ext import CommandHandler
from telegram.ext import Filters
from telegram.ext import MessageHandler
from telegram.ext import PreCheckoutQueryHandler
from telegram.ext import Updater

from connect_to_redis_db import get_database_connection
from geolocation import fetch_coordinates
from logs_handler import TelegramLogsHandler
from moltin import add_product_to_cart
from moltin import get_cart_items
from moltin import get_image
from moltin import get_product
from moltin import remove_item_in_cart
from pizza_contents import get_all_pizzerias
from pizza_contents import get_cart_keyboard
from pizza_contents import get_cart_text
from pizza_contents import get_description_keyboard
from pizza_contents import get_description_text
from pizza_contents import get_distance_to_user
from pizza_contents import get_location_keyboard
from pizza_contents import get_location_text
from pizza_contents import get_menu_keyboard

logger = logging.getLogger('pizza_bots logger')


def show_menu(context, chat_id, message_id):
    menu_keyboard = get_menu_keyboard(context)
    context.bot.send_message(chat_id=chat_id, text='Please choose:',
                             reply_markup=menu_keyboard)
    context.bot.delete_message(chat_id=chat_id, message_id=message_id)


def show_cart(context, chat_id, message_id):
    cart_items = get_cart_items(context.bot_data['moltin_token'],
                                context.bot_data['moltin_secret'],
                                chat_id)
    cart_text = get_cart_text(cart_items)
    cart_keyboard = get_cart_keyboard(cart_items)
    context.bot.send_message(chat_id=chat_id,
                             text=cart_text,
                             reply_markup=cart_keyboard,
                             parse_mode='HTML')
    context.bot.delete_message(chat_id=chat_id, message_id=message_id)


def del_extra_invoice(chat_id, context):
    db = context.bot_data['db']
    last_invoice = db.get(f'{chat_id}_invoice_message_id')
    if last_invoice and last_invoice != b'clear':
        context.bot.delete_message(chat_id=chat_id,
                                   message_id=last_invoice.decode("utf-8"))
        db.set(f'{chat_id}_invoice_message_id', 'clear')


def start(update, context):
    context.user_data['menu_page'] = 0
    reply_markup = get_menu_keyboard(context)
    update.message.reply_text('Please choose:', reply_markup=reply_markup)
    return 'HANDLE_MENU'


def menu_handler(update, context):
    query = update.callback_query
    query.answer()
    chat_id = query.message.chat_id
    message_id = query.message.message_id
    if query.data == 'to_cart':
        show_cart(context, chat_id, message_id)
        return 'HANDLE_CART'
    elif 'back' in query.data or 'forward' in query.data:
        current_user_page = context.user_data['menu_page']
        context.user_data['menu_page'] = int(current_user_page) \
                                         + int(query.data.split()[1])
        menu_keyboard = get_menu_keyboard(context)
        context.bot.edit_message_text(chat_id=chat_id,
                                      text='Please choose:',
                                      reply_markup=menu_keyboard,
                                      message_id=message_id)
        return 'HANDLE_MENU'
    product_id = query.data
    product = get_product(context.bot_data['moltin_token'],
                          context.bot_data['moltin_secret'],
                          product_id)['data']
    image_id = product['relationships']['main_image']['data']['id']
    image = get_image(context.bot_data['moltin_token'],
                      context.bot_data['moltin_secret'],
                      image_id)

    description_text = get_description_text(product)
    description_keyboard = get_description_keyboard(product_id)
    context.bot.send_photo(chat_id=chat_id, photo=image,
                           caption=description_text,
                           reply_markup=description_keyboard,
                           parse_mode='HTML')
    context.bot.delete_message(chat_id=chat_id, message_id=message_id)
    return 'HANDLE_DESCRIPTION'


def description_handler(update, context):
    query = update.callback_query
    chat_id = query.message.chat_id
    message_id = query.message.message_id

    if query.data == 'to_menu':
        show_menu(context, chat_id, message_id)
        return 'HANDLE_MENU'
    elif query.data == 'to_cart':
        show_cart(context, chat_id, message_id)
        return 'HANDLE_CART'

    product_id = query.data
    add_product_to_cart(moltin_token=context.bot_data['moltin_token'],
                        moltin_secret=context.bot_data['moltin_secret'],
                        cart_id=chat_id,
                        product_id=product_id,
                        quantity=1)
    query.answer(text='Добавлено в корзину')
    return 'HANDLE_DESCRIPTION'


def cart_handler(update, context):
    query = update.callback_query
    query.answer()
    chat_id = query.message.chat_id
    message_id = query.message.message_id

    if query.data == 'to_menu':
        show_menu(context, chat_id, message_id)
        return 'HANDLE_MENU'
    if query.data == 'to_payment':
        context.bot.edit_message_text(
            chat_id=chat_id,
            text='Пришлите, пожалуйста, ваш адрес текстом или геопозицию',
            message_id=message_id
        )
        return 'WAITING_LOCATION'

    cart_item_id = query.data
    remaining_items = remove_item_in_cart(context.bot_data['moltin_token'],
                                          context.bot_data['moltin_secret'],
                                          chat_id, cart_item_id)
    cart_text = get_cart_text(remaining_items)
    cart_keyboard = get_cart_keyboard(remaining_items)
    context.bot.edit_message_text(chat_id=chat_id,
                                  text=cart_text,
                                  reply_markup=cart_keyboard,
                                  message_id=message_id,
                                  parse_mode='HTML')
    return 'HANDLE_CART'


def location_handler(update, context):
    if update.message.location:
        user_location = update.message.location
        user_lon = user_location.longitude
        user_lat = user_location.latitude
    elif not fetch_coordinates(context.bot_data['geo_token'],
                               update.message.text):
        text = f'''
                Кажется вы неправильно ввели адрес: {update.message.text}
                Пришлите ещё раз.
                '''
        update.message.reply_text(text=textwrap.dedent(text))
        return 'WAITING_LOCATION'
    else:
        user_lon, user_lat = fetch_coordinates(context.bot_data['geo_token'],
                                               update.message.text)
    pizzerias = get_all_pizzerias(context)
    nearest_pizzeria = min(
        pizzerias,
        key=partial(get_distance_to_user, user_position=(user_lat, user_lon))
    )
    context.user_data['nearest_pizzeria'] = nearest_pizzeria
    context.user_data['user_coordinates'] = {'longitude': user_lon,
                                             'latitude': user_lat}
    distance_to_user = get_distance_to_user(nearest_pizzeria, (user_lat, user_lon))
    text = get_location_text(distance_to_user, nearest_pizzeria)
    keyboard = get_location_keyboard(distance_to_user)

    update.message.reply_text(text=text, reply_markup=keyboard, parse_mode='HTML')

    return 'HANDLE_DELIVERY'


def delivery_handler(update, context):
    query = update.callback_query
    query.answer()
    chat_id = query.message.chat_id
    message_id = query.message.message_id
    nearest_pizzeria = context.user_data['nearest_pizzeria']

    if query.data == 'self-pickup':
        text = f'''
                Ждём вас в нашей пиццерии: <i><b>{nearest_pizzeria['address']}</b></i>.
                '''
        context.bot.edit_message_text(chat_id=chat_id,
                                      text=text,
                                      message_id=message_id,
                                      parse_mode='HTML')
        return 'START'

    context.bot.edit_message_text(
        chat_id=chat_id,
        text='Для оплаты нажмите кнопку <b>Оплатить</b>',
        message_id=message_id,
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton('Оплатить', callback_data='to_payment')]]),
        parse_mode='HTML'
    )
    return 'HANDLE_PAYMENT'


def payment_handler(update, context):
    query = update.callback_query
    query.answer()
    chat_id = query.message.chat_id
    message_id = query.message.message_id
    db = context.bot_data['db']

    cart_items = get_cart_items(context.bot_data['moltin_token'],
                                context.bot_data['moltin_secret'],
                                chat_id)
    title = "Payment Example"
    description = "Payment Example using python-telegram-bot"
    payload = "Custom-Payload"
    provider_token = os.getenv('PAYMENT_TG_TOKEN')
    currency = "RUB"
    price = cart_items['meta']['display_price']['with_tax']['formatted'].replace(' ', '')
    prices = [LabeledPrice("Test", int(price)*100)]
    invoice_message = context.bot.send_invoice(
        chat_id, title, description, payload, provider_token, currency, prices
    )
    db.set(f'{chat_id}_invoice_message_id', invoice_message.message_id)
    context.bot.delete_message(chat_id=chat_id, message_id=message_id)
    return 'HANDLE_PRECHECKOUT'


def precheckout_handler(update, context):
    query = update.pre_checkout_query
    if query.invoice_payload != 'Custom-Payload':
        query.answer(ok=False, error_message="Something went wrong...")
        return 'HANDLE_PRECHECKOUT'
    query.answer(ok=True)
    return 'START'


def successful_payment_handler(update, context):
    successful_payment_text = '''
           Оплата прошла успешно!
           Ожидайте курьера в ближайший час!
           '''
    update.message.reply_text(textwrap.dedent(successful_payment_text))
    chat_id = update.message.chat_id
    del_extra_invoice(chat_id, context)


def handle_users_reply(update, context):
    db = context.bot_data['db']
    if update.message:
        user_reply = update.message.text
        chat_id = update.message.chat_id
    elif update.callback_query:
        user_reply = update.callback_query.data
        chat_id = update.callback_query.message.chat_id
    elif update.pre_checkout_query:
        user_reply = update.pre_checkout_query.invoice_payload
        chat_id = update.pre_checkout_query.from_user.id
    elif update.message.location:
        user_reply = update.message.location
        chat_id = update.message.chat_id
    else:
        return
    if user_reply == '/start':
        user_state = 'START'
    elif update.message and db.get(chat_id).decode("utf-8") != 'WAITING_LOCATION':
        return
    else:
        user_state = db.get(chat_id).decode("utf-8")

    del_extra_invoice(chat_id, context)

    states_functions = {
        'START': start,
        'HANDLE_MENU': menu_handler,
        'HANDLE_DESCRIPTION': description_handler,
        'HANDLE_CART': cart_handler,
        'WAITING_LOCATION': location_handler,
        'HANDLE_DELIVERY': delivery_handler,
        'HANDLE_PAYMENT': payment_handler,
        'HANDLE_PRECHECKOUT': precheckout_handler
    }
    state_handler = states_functions[user_state]
    next_state = state_handler(update, context)
    db.set(chat_id, next_state)


def error_handler(update, context):
    logger.exception(msg='Exception while handling an update:',
                     exc_info=context.error)


def main():
    load_dotenv()
    tg_token = os.getenv('TG_BOT_TOKEN')
    tg_chat_id = os.getenv('TG_CHAT_ID')
    tg_bot = telegram.Bot(token=tg_token)
    logger.setLevel(logging.INFO)
    logger.addHandler(TelegramLogsHandler(tg_bot, tg_chat_id))
    logger.info('ТГ бот запущен')

    updater = Updater(tg_token)
    dp = updater.dispatcher
    dp.bot_data['moltin_token'] = os.getenv('ELASTICPATH_CLIENT_ID')
    dp.bot_data['moltin_secret'] = os.getenv('ELASTICPATH_CLIENT_SECRET')
    dp.bot_data['geo_token'] = os.getenv('YANDEX_GEOCODER_API_KEY')
    dp.bot_data['db'] = get_database_connection()
    dp.add_handler(CallbackQueryHandler(handle_users_reply))
    dp.add_handler(MessageHandler(Filters.text, handle_users_reply))
    dp.add_handler(MessageHandler(Filters.location, handle_users_reply))
    dp.add_handler(CommandHandler('start', handle_users_reply))
    dp.add_handler(PreCheckoutQueryHandler(handle_users_reply))
    dp.add_handler(MessageHandler(Filters.successful_payment,
                                  successful_payment_handler))
    dp.add_error_handler(error_handler)
    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()
