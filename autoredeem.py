import zlib
import base64
import getpass
import requests
import json
import re
from bs4 import BeautifulSoup
from datetime import datetime


from web3 import Web3
from web3.middleware import geth_poa_middleware
w3 = Web3(Web3.WebsocketProvider('wss://api.avax.network/ext/bc/C/ws'))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)

bonds = {
    'WAVAX': '0xE02B1AA2c4BE73093BE79d763fdFFC0E3cf67318',
    'AVAXLP': '0xc26850686ce755FFb8690EA156E5A6cf03DcBDE1',
    'MIMLP': '0xA184AE1A71EcAD20E822cB965b99c287590c4FFe',
    'MIM': '0x694738E0A438d90487b4a549b201142c1a97B556',
}


def hexfix(s):
    return s if s.startswith('0x') else '0x'+ s


def encode(s):
    return str(base64.b64encode(zlib.compress(bytes(s,'ascii'))), 'ascii')


def decode(s):
    return str(zlib.decompress(base64.b64decode(s)), 'ascii')


def make_account():
    with open('account','w') as out:
        addy = getpass.getpass('Paste address and press enter (not echoed on screen):')
        out.write(encode(addy))
        out.write("\n")
        key = getpass.getpass('Paste private key and press enter (not echoed on screen):')
        out.write(encode(key))
    key = hexfix(key)
    addy = hexfix(addy)
    return addy, key


def get_account():
    with open('account','r') as inp:
        addy = decode(inp.readline())
        key = decode(inp.readline())
    key = hexfix(key)
    addy = hexfix(addy)
    return addy, key


class Wallet:
    def __init__(self):
        try:
            self.address, self.private_key = get_account()
        except:
            self.address, self.private_key = make_account()
        self.nonce = w3.eth.get_transaction_count(self.address)

    def transact(self, function):
        block = w3.eth.get_block('latest')
        tx_params = dict(
            type=2,
            chainId=43114,
            maxFeePerGas=2 * block['baseFeePerGas'],
            maxPriorityFeePerGas=0,
            nonce=self.nonce,
        )
        gas = function.estimateGas(tx_params)
        tx_params.update(gas=2 * gas)
        tx = function.buildTransaction(tx_params)
        signed = w3.eth.account.sign_transaction(tx, self.private_key)
        w3.eth.send_raw_transaction(signed.rawTransaction)
        self.nonce += 1


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


def get_contract(addy):
    return w3.eth.contract(address=addy, abi=get_abi(addy))


def redeem(wallet, contract):
    wallet.transact(contract.functions.redeem(wallet.address, True))


def log(msg):
    now = datetime.now()
    date_time = now.strftime("%Y-%m-%d-%H:%M:%S")
    with open('redeem.log','a') as out:
        out.write(f"{date_time} {msg}\n")


def main():
    wallet = Wallet()
    redeemed = False
    for bond in bonds:
        depo = get_contract(bonds[bond])
        vested = depo.functions.percentVestedFor(wallet.address).call()
        if vested > 0:
            redeem(wallet, depo)
            redeemed = True
            log(f"Claiming {bond}")
    if not redeemed:
        log("No bonds to claim")


if __name__ == '__main__':
    main()
