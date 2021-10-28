from datetime import datetime
from wallet import Wallet
from utils import get_contract

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


def redeem(wallet, contract):
    wallet.transact(contract.functions.redeem(wallet.address, True))


def log(msg):
    now = datetime.now()
    date_time = now.strftime("%Y-%m-%d-%H:%M:%S")
    with open('redeem.log','a') as out:
        out.write(f"{date_time} {msg}\n")


def main():
    wallet = Wallet(w3)
    redeemed = False
    for bond in bonds:
        depo = get_contract(w3, bonds[bond])
        vested = depo.functions.percentVestedFor(wallet.address).call()
        if vested > 0:
            redeem(wallet, depo)
            redeemed = True
            log(f"Claiming {bond}")
    if not redeemed:
        log("No bonds to claim")


if __name__ == '__main__':
    main()
