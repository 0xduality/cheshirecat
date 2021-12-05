import json
import requests
import os

def get_abi(addy):
    home = os.path.expanduser("~")
    cache_dir = os.path.join(home, '.abicache')
    cache = os.path.join(cache_dir, f'{addy}.json')
    try:
        with open(cache) as inp:
            abi = json.loads(inp.read())
    except Exception as e:
        print(e)
        resp = requests.get(f'https://api.snowtrace.io/api?module=contract&action=getabi&address={addy}')
        abi = json.loads(resp.json()['result'])
        os.makedirs(cache_dir, exist_ok=True)
        with open(cache, 'w') as out:
            out.write(json.dumps(abi, indent=True))
    return abi


def get_contract(w3, addy):
    return w3.eth.contract(address=addy, abi=get_abi(addy))

