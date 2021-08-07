import time

import requests
from slugify import slugify

EP_ACCESS_TOKEN = None
EP_TOKEN_LIFETIME = None


def get_ep_access_token(moltin_token, moltin_secret):
    now_time = time.time()
    global EP_ACCESS_TOKEN
    global EP_TOKEN_LIFETIME

    if not EP_TOKEN_LIFETIME or EP_TOKEN_LIFETIME < now_time:
        EP_ACCESS_TOKEN, EP_TOKEN_LIFETIME = create_ep_access_token(moltin_token,
                                                                    moltin_secret)

    return EP_ACCESS_TOKEN


def create_ep_access_token(moltin_token, moltin_secret):
    url = 'https://api.moltin.com/oauth/access_token'
    data = {
        'client_id': moltin_token,
        'client_secret': moltin_secret,
        'grant_type': 'client_credentials'
    }
    response = requests.post(url, data=data)
    response.raise_for_status()
    response_details = response.json()
    ep_token_lifetime = response_details['expires']
    ep_access_token = response_details['access_token']
    return ep_access_token, ep_token_lifetime


def get_all_products(moltin_token, moltin_secret):
    access_token = get_ep_access_token(moltin_token, moltin_secret)
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    response = requests.get('https://api.moltin.com/v2/products',
                            headers=headers)
    response.raise_for_status()
    return response.json()


def get_product(moltin_token, moltin_secret, product_id):
    access_token = get_ep_access_token(moltin_token, moltin_secret)
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    response = requests.get(f'https://api.moltin.com/v2/products/{product_id}',
                            headers=headers)
    response.raise_for_status()
    return response.json()


def get_image(moltin_token, moltin_secret, image_id):
    access_token = get_ep_access_token(moltin_token, moltin_secret)
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    response = requests.get(f'https://api.moltin.com/v2/files/{image_id}',
                            headers=headers)
    response.raise_for_status()
    image = response.json()['data']['link']['href']
    return image


def add_product_to_cart(moltin_token, moltin_secret, cart_id, product_id, quantity):
    url = f'https://api.moltin.com/v2/carts/{cart_id}/items'
    access_token = get_ep_access_token(moltin_token, moltin_secret)
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


def get_cart(moltin_token, moltin_secret, cart_id):
    access_token = get_ep_access_token(moltin_token, moltin_secret)
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    response = requests.get(f'https://api.moltin.com/v2/carts/{cart_id}',
                            headers=headers)
    response.raise_for_status()
    return response.json()


def get_cart_items(moltin_token, moltin_secret, cart_id):
    url = f'https://api.moltin.com/v2/carts/{cart_id}/items'
    access_token = get_ep_access_token(moltin_token, moltin_secret)
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def remove_item_in_cart(moltin_token, moltin_secret, cart_id, cart_item_id):
    url = f'https://api.moltin.com/v2/carts/{cart_id}/items/{cart_item_id}'
    access_token = get_ep_access_token(moltin_token, moltin_secret)
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    response = requests.delete(url, headers=headers)
    response.raise_for_status()
    return response.json()


def create_customer(moltin_token, moltin_secret, name, email):
    url = f'https://api.moltin.com/v2/customers'
    access_token = get_ep_access_token(moltin_token, moltin_secret)
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


def get_customer(moltin_token, moltin_secret, user_id):
    url = f'https://api.moltin.com/v2/customers/{user_id}'
    access_token = get_ep_access_token(moltin_token, moltin_secret)
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def create_product(moltin_token, moltin_secret, name, sku, description, price):
    access_token = get_ep_access_token(moltin_token, moltin_secret)
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }
    data = {'data':{
        'type': 'product',
        'name': name,
        'slug': slugify(name),
        'sku': str(sku),
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
    response.raise_for_status()
    return response.json()


def create_file(moltin_token, moltin_secret, image_url):
    access_token = get_ep_access_token(moltin_token, moltin_secret)
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    files = {
        'file_location': (None, image_url)
    }
    response = requests.post('https://api.moltin.com/v2/files',
                             headers=headers, files=files)
    response.raise_for_status()
    return response.json()


def create_image_relationship(moltin_token, moltin_secret, product_id, image_id):
    access_token = get_ep_access_token(moltin_token, moltin_secret)
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }
    data = {'data': {
        'type': 'main_image',
        'id': image_id
    }}
    response = requests.post(
        f'https://api.moltin.com/v2/products/{product_id}/relationships/main-image',
        headers=headers, json=data)
    response.raise_for_status()
    return response.json()


def create_flow(moltin_token, moltin_secret, name, description):
    access_token = get_ep_access_token(moltin_token, moltin_secret)
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }
    data = {'data': {
        'type': 'flow',
        'name': name,
        'slug': slugify(name),
        'description': description,
        'enabled': True
    }}
    response = requests.post('https://api.moltin.com/v2/flows',
                             headers=headers, json=data)
    response.raise_for_status()
    return response.json()


def create_field(moltin_token, moltin_secret, name, field_type, description,
                 flow_id):
    access_token = get_ep_access_token(moltin_token, moltin_secret)
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }
    data = {"data": {
        "type": "field",
        "name": name,
        "slug": slugify(name),
        "field_type": field_type,
        "description": description,
        "required": True,
        "enabled": True,
        "relationships": {
            "flow": {"data": {
                "type": "flow",
                "id": flow_id
            }}
        }
    }}
    response = requests.post('https://api.moltin.com/v2/fields',
                             headers=headers, json=data)
    response.raise_for_status()
    return response.json()


def create_entry(moltin_token, moltin_secret, flow_slug, fields):
    access_token = get_ep_access_token(moltin_token, moltin_secret)
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }
    data = {"data": {
        "type": "entry",
    }}
    data['data'].update(fields)
    response = requests.post(f'https://api.moltin.com/v2/flows/{flow_slug}/entries',
                             headers=headers, json=data)
    response.raise_for_status()
    return response.json()


def get_all_entries(moltin_token, moltin_secret, flow_slug):
    url = f'https://api.moltin.com/v2/flows/{flow_slug}/entries'
    access_token = get_ep_access_token(moltin_token, moltin_secret)
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def get_all_flows(moltin_token, moltin_secret):
    url = f'https://api.moltin.com/v2/flows/'
    access_token = get_ep_access_token(moltin_token, moltin_secret)
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()
