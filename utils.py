import json
import re
import requests
from bs4 import BeautifulSoup

def get_abi(addy):
    cache = f'{addy}.json'
    try:
        with open(cache) as inp:
            abi = json.loads(inp.read())
    except Exception as e:
        print(e)
        resp = requests.get(f'https://api.snowtrace.io/api?module=contract&action=getabi&address={addy}')
        abi = resp.json()['result']
        with open(cache, 'w') as out:
            out.write(json.dumps(abi, indent=True))
    return abi

def get_contract(w3, addy):
    return w3.eth.contract(address=addy, abi=get_abi2(addy))

