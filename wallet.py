import getpass
import zlib
import base64

def hexfix(s):
    return s if s.startswith('0x') else '0x'+ s


def encode(s):
    return str(base64.b64encode(zlib.compress(bytes(s,'ascii'))), 'ascii')


def decode(s):
    return str(zlib.decompress(base64.b64decode(s)), 'ascii')


def make_account():
    addy = getpass.getpass('Paste address and press enter (not echoed on screen):')
    key = getpass.getpass('Paste private key and press enter (not echoed on screen):')
    with open('account','w') as out:
        out.write(encode(addy))
        out.write("\n")
        out.write(encode(key))
    key = hexfix(key)
    addy = hexfix(addy)
    return addy, key


def get_account(fn=None):
    if fn is None:
        fn = 'account'
    with open(fn,'r') as inp:
        addy = decode(inp.readline())
        key = decode(inp.readline())
    key = hexfix(key)
    addy = hexfix(addy)
    return addy, key


class Wallet:
    def __init__(self, web3, fn=None):
        self.w3 = web3
        self.fn = fn
        try:
            self.address, self.private_key = get_account(self.fn)
        except Exception as e:
            print(e)
            self.address, self.private_key = make_account()

    def _prep(self, function, **kwds):
        block = self.w3.eth.get_block('latest')
        tx_params = dict(
            type=2,
            chainId=43114,
            maxFeePerGas=2 * block['baseFeePerGas'],
            maxPriorityFeePerGas=0,
            nonce=self.w3.eth.get_transaction_count(self.address),
        )
        tx_params['from'] = self.address
        tx_params.update(**kwds)
        if 'gas' not in tx_params:
            gas = function.estimateGas(tx_params)
            tx_params.update(gas=2 * gas)
        return tx_params

    def transact(self, function, **kwds):
        tx_params = self._prep(function, **kwds)
        tx = function.buildTransaction(tx_params)
        signed = self.w3.eth.account.sign_transaction(tx, self.private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed.rawTransaction)
        rcpt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        print('tx successful' if rcpt.status==1 else 'tx failed')
    
    def call(self, function, **kwargs):
        tx_params = self._prep(function, **kwargs)
        return function.call(tx_params)