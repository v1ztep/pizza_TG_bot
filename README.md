# Чатбот по продаже пиццы в [Telegram](https://telegram.org/) интегрированный с CMS [Moltin/ElasticPath](https://www.elasticpath.com/)

Чатбот для [Telegram](https://telegram.org/) с возможностью выбирать, добавлять и
удалять товар в корзине, оформлять и оплачивать покупку картой, подгружая 
информацию и дополняя новыми контактами клиентов в [CMS Moltin/ElasticPath](https://www.elasticpath.com/).

![gif](media/pizza_bot.gif)

## Настройки

* Необходимо зарегистрироваться в [Redislabs](https://redislabs.com/) - забрать 
адрес базы данных вида `redis-13965.f18.us-east-4-9.wc1.cloud.redislabs.com:16635` 
и его пароль.
* Создать бота в Telegram через специального бота:
[@BotFather](https://telegram.me/BotFather), забрать API ключ и написать 
созданному боту. В разделе `Payments` создать ключ для оплаты картой.
* Забрать свой `chat_id` через [@userinfobot](https://telegram.me/userinfobot) - 
  необходим для получения логов (ошибки будут идти именно этому пользователю).
* Зарегистрироваться в [API Яндекс-геокодера](https://developer.tech.yandex.ru/),
и получите `JavaScript API и HTTP Геокодер`.
* Зарегистрироваться в CMS [Moltin](https://www.elasticpath.com/), забрать 
`Client ID` и `Client secret`. Заполнить товары в 
[CMS Catalog](https://dashboard.elasticpath.com/app/catalog/products) (либо 
воспользоваться [`menu_upload.py`](#Загрузка-пицц)), cоздать Flows c адресами пиццерий в 
[CMS Flows](https://dashboard.elasticpath.com/app/flows) `Pizzeria` (либо 
воспользоваться [`address_upload.py`](#Загрузка-адресов)) и `сustomer-address` 
куда будут внесены успешные заказы (необходимые поля: `name`, `date`, `longitude`, 
`latitude`, `order`).

### Переменные окружения

Создайте файл `.env` в корневой папке с кодом и запишите туда:
```
REDISLABS_ENDPOINT=АДРЕС_БД
REDIS_DB_PASS=ПАРОЛЬ_ВАШЕЙ_БД
TG_BOT_TOKEN=ВАШ_TELEGRAM_API_КЛЮЧ
TG_CHAT_ID=ВАШ_CHAT_ID
ELASTICPATH_CLIENT_ID=ВАШ_API_КЛЮЧ_MOLTIN
ELASTICPATH_CLIENT_SECRET=ВАШ_API_SECRET_КЛЮЧ_MOLTIN
YANDEX_GEOCODER_API_KEY=ВАШ_YANDEX_GEOCODER_API_КЛЮЧ
PAYMENT_TG_TOKEN=ВАШ_PAYMENT_TG_API_КЛЮЧ
```

## Загрузка информации в CMS Moltin/ElasticPath

### Загрузка пицц
Необходимо создать файл `menu.json` в корневой папке в формате:

```
{
  {
  'name': 'Чизбургер-пицца',
  'id': 20,
  'description': 'мясной соус болоньезе, моцарелла, лук, соленые огурчики, томаты, соус бургер',
  'price': 395,
  'product_image': {'url': 'https://dodopizza-a.akamaihd.net/static/Img/Products/Pizza/ru-RU/1626f452-b56a-46a7-ba6e-c2c2c9707466.jpg'}
  },
  {
  ...
  },
}
```
После создания подгрузить все пиццы командой `python menu_upload.py`.

### Загрузка адресов
Необходимо создать файл `addresses.json` в корневой папке в формате:

```
{
  {
  'address': {'full': 'Москва, набережная Пресненская дом 2'},
  'alias': 'Афимолл',
  'coordinates': {
                  'lon': '55.749299',
                  'lat': '37.539644'
                 }
  },
  {
  ...
  },
}
```
После создания подгрузить все адреса командой `python address_upload.py`.
Также необходимо добавить поле `deliveryman-tg-id` и заполнить его, для каждой 
пиццерии "chat_id telegram" курьера, коему будут приходить заказы после успешной 
оплаты.


## Запуск

Для запуска у вас уже должен быть установлен [Python 3](https://www.python.org/downloads/release/python-379/).

- Скачайте код.
- Установите зависимости командой:
```
pip install -r requirements.txt
```
- Запустите скрипт командой: 
```
python tg_bot.py
```
