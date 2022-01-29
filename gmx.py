from wallet import Wallet
from utils import get_contract
from contextlib import ContextDecorator

from web3 import Web3
from web3.middleware import geth_poa_middleware

#w3 = Web3(Web3.WebsocketProvider('ws://localhost:8545'))
w3 = Web3(Web3.HTTPProvider('https://api.avax.network/ext/bc/C/rpc'))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)


def compound(wallet):
    address = '0x82147C5A7E850eA4E28155DF107F2590fD4ba327'
    wavax = '0xB31f66AA3C1e785363F0875A1B74E27b85FD66c7'
    router = get_contract(w3, address)
    f, t = False, True 
    wallet.transact(router.functions.handleRewards(f, f, t, t, t, t, f))
    balance = get_contract(w3, wavax).functions.balanceOf(wallet.address).call()
    print(balance)
    wallet.transact(router.functions.mintAndStakeGlp(wavax, balance, 0, 0))


def main(argv):
    account = argv[1] if len(argv) > 1 else 'account'
    wallet = Wallet(w3, account)
    compound(wallet)

if __name__ == '__main__':
    import sys
    main(sys.argv) 


