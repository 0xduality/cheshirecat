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
        r = requests.get(f'https://cchain.explorer.avax.network/address/{addy}/contracts')
        soup = BeautifulSoup(r.text)
        buttons = soup.find_all('button', string=re.compile("\s*Copy ABI\s*"))
        assert len(buttons)==1
        text = buttons[0]['data-clipboard-text']
        abi = json.loads(text)
        with open(cache, 'w') as out:
            out.write(json.dumps(abi))
    return abi


def get_contract(w3, addy):
    return w3.eth.contract(address=addy, abi=get_abi(addy))