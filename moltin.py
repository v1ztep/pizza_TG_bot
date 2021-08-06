import os
import time
import json
import requests
from dotenv import load_dotenv
from slugify import slugify

EP_ACCESS_TOKEN = None
EP_TOKEN_LIFETIME = None


def get_ep_access_token(moltin_token):
    now_time = time.time()
    global EP_ACCESS_TOKEN
    global EP_TOKEN_LIFETIME

    if not EP_TOKEN_LIFETIME or EP_TOKEN_LIFETIME < now_time:
        EP_ACCESS_TOKEN, EP_TOKEN_LIFETIME = create_ep_access_token(moltin_token)

    return EP_ACCESS_TOKEN


def create_ep_access_token(moltin_token):
    url = 'https://api.moltin.com/oauth/access_token'
    data = {
        'client_id': moltin_token,
        'grant_type': 'implicit'
    }
    response = requests.post(url, data=data)
    response.raise_for_status()
    response_details = response.json()
    ep_token_lifetime = response_details['expires']
    ep_access_token = response_details['access_token']
    return ep_access_token, ep_token_lifetime


def get_all_products(moltin_token):
    access_token = get_ep_access_token(moltin_token)
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    response = requests.get('https://api.moltin.com/v2/products',
                            headers=headers)
    response.raise_for_status()
    return response.json()


def get_product(moltin_token, product_id):
    access_token = get_ep_access_token(moltin_token)
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    response = requests.get(f'https://api.moltin.com/v2/products/{product_id}',
                            headers=headers)
    response.raise_for_status()
    return response.json()


def get_image(moltin_token, image_id):
    access_token = get_ep_access_token(moltin_token)
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    response = requests.get(f'https://api.moltin.com/v2/files/{image_id}',
                            headers=headers)
    response.raise_for_status()
    image = response.json()['data']['link']['href']
    return image


def add_product_to_cart(moltin_token, cart_id, product_id, quantity):
    url = f'https://api.moltin.com/v2/carts/{cart_id}/items'
    access_token = get_ep_access_token(moltin_token)
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }
    data = {'data':
                 { 'id': product_id,
                   'type': 'cart_item',
                   'quantity': quantity}
             }
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()


def get_cart(moltin_token, cart_id):
    access_token = get_ep_access_token(moltin_token)
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    response = requests.get(f'https://api.moltin.com/v2/carts/{cart_id}',
                            headers=headers)
    response.raise_for_status()
    return response.json()


def get_cart_items(moltin_token, cart_id):
    url = f'https://api.moltin.com/v2/carts/{cart_id}/items'
    access_token = get_ep_access_token(moltin_token)
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def remove_item_in_cart(moltin_token, cart_id, cart_item_id):
    url = f'https://api.moltin.com/v2/carts/{cart_id}/items/{cart_item_id}'
    access_token = get_ep_access_token(moltin_token)
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    response = requests.delete(url, headers=headers)
    response.raise_for_status()
    return response.json()


def create_customer(moltin_token, name, email):
    url = f'https://api.moltin.com/v2/customers'
    access_token = get_ep_access_token(moltin_token)
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }
    data = {'data':
                {'type': 'customer',
                 'name': name,
                 'email': email}
            }
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()


def get_customer(moltin_token, user_id):
    url = f'https://api.moltin.com/v2/customers/{user_id}'
    access_token = get_ep_access_token(moltin_token)
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def create_product(moltin_token, name, sku, description, price):
    access_token = get_ep_access_token(moltin_token)
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }
    data = {'data':{
        'type': 'pizza',
        'name': name,
        'slug': slugify(name),
        'sku': sku,
        'description': description,
        'manage_stock': False,
        'price': [{
            'amount': price,
            'currency': 'RUB',
            'includes_tax': True
        }],
        'status': 'live',
        'commodity_type': 'physical'
    }}
    response = requests.post('https://api.moltin.com/v2/products',
                            headers=headers, json=data)
    print(response.text)
    response.raise_for_status()
    return response.json()


def create_file(moltin_token, image_url):
    access_token = get_ep_access_token(moltin_token)
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    files = {
        'file-location': (None, image_url),
    }
    response = requests.post('https://api.moltin.com/v2/files',
                             headers=headers, files=files)
    print(response.text)
    response.raise_for_status()
    return response.json()


def create_image_relationship(moltin_token, product_id, image_id):
    access_token = get_ep_access_token(moltin_token)
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }
    data = {"data": {
        'type': 'main_image',
        'id': image_id
    }}
    response = requests.post(
        f'https://api.moltin.com/v2/products/{product_id}/relationships/main-image',
        headers=headers, data=data)
    print(response.text)
    response.raise_for_status()
    return response.json()


def main():
    load_dotenv()
    moltin_token = os.getenv('ELASTICPATH_CLIENT_ID')

    with open("menu.json", "r", encoding="utf8") as file:
        menu_json = file.read()
    menu = json.loads(menu_json)

    for pizza in menu:
        name = pizza['name']
        sku = pizza['id']
        description = pizza['description']
        price = pizza['price']
        image_url = pizza['product_image']['url']
        product = create_product(moltin_token, name, sku, description, price)
        product_id = product['data']['id']
        image = create_file(moltin_token, image_url)
        image_id = image['data']['id']
        create_image_relationship(moltin_token, product_id, image_id)
        break



if __name__ == '__main__':
    main()
