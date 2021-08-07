import json
import os

from dotenv import load_dotenv

from moltin import create_flow

load_dotenv()


moltin_token = os.getenv('ELASTICPATH_CLIENT_ID')
moltin_secret = os.getenv('ELASTICPATH_CLIENT_SECRET')

create_flow(moltin_token, moltin_secret, 'Addresses', 'pizzeria addresses')

# with open("addresses.json", "r", encoding="utf8") as file:
#     addresses_json = file.read()
# addresses = json.loads(addresses_json)

