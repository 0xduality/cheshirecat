import time
import decimal
from wallet import Wallet
from utils import get_contract

from web3 import Web3
from web3.middleware import geth_poa_middleware
w3 = Web3(Web3.WebsocketProvider('wss://api.avax.network/ext/bc/C/ws'))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)

autobond_address = '0x73cDbB40fd311D290cc0B6b222f2d51D447a3d56'

autobond_abi = [
    {
      "inputs": [],
      "stateMutability": "nonpayable",
      "type": "constructor"
    },
    {
      "inputs": [
        {
          "internalType": "address",
          "name": "_token",
          "type": "address"
        },
        {
          "internalType": "uint256",
          "name": "_minimum",
          "type": "uint256"
        }
      ],
      "name": "mintWithERC20",
      "outputs": [],
      "stateMutability": "nonpayable",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "address",
          "name": "_token",
          "type": "address"
        },
        {
          "internalType": "uint256",
          "name": "_minimum",
          "type": "uint256"
        }
      ],
      "name": "mintWithLP",
      "outputs": [],
      "stateMutability": "nonpayable",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "address",
          "name": "_token",
          "type": "address"
        }
      ],
      "name": "payoutForERC20",
      "outputs": [
        {
          "internalType": "uint256",
          "name": "",
          "type": "uint256"
        }
      ],
      "stateMutability": "nonpayable",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "address",
          "name": "_token",
          "type": "address"
        }
      ],
      "name": "payoutForLP",
      "outputs": [
        {
          "internalType": "uint256",
          "name": "",
          "type": "uint256"
        }
      ],
      "stateMutability": "nonpayable",
      "type": "function"
    }
  ]

autobond = w3.eth.contract(address=autobond_address, abi=autobond_abi)

addys = {
    'MEMO': '0x136Acd46C134E8269052c62A67042D6bDeDde3C9',
    'MIMLP': '0x113f413371fC4CC4C9d6416cf1DE9dFd7BF747Df',
    'STAKE': '0x4456B87Af11e87E329AB7d7C7A246ed1aC2168B9',
    'MIM': '0x130966628846BFd36ff31a822705796e8cb8C18D',
    'WAVAX': '0xB31f66AA3C1e785363F0875A1B74E27b85FD66c7',
#    'TIME': '0xb54f16fB19478766A268F172C9480f8da1a7c9C3',
#    'WAVAXLP': '0xf64e1c5B6E17031f5504481Ac8145F4c3eab4917',
#    'JOEROUTER': '0x60aE616a2155Ee3d9A68541Ba4544862310933d4', 
}

bonds = {
    'WAVAX': '0xE02B1AA2c4BE73093BE79d763fdFFC0E3cf67318',
    'WAVAXLP': '0xc26850686ce755FFb8690EA156E5A6cf03DcBDE1',
    'MIMLP': '0xA184AE1A71EcAD20E822cB965b99c287590c4FFe',
    'MIM': '0x694738E0A438d90487b4a549b201142c1a97B556',
}


def get_rebase():
    memo = get_contract(w3, addys['MEMO'])
    stake = get_contract(w3, addys['STAKE'])
    circ = memo.functions.circulatingSupply().call()
    epoch = stake.functions.epoch().call()
    return epoch[1]/circ


def best_roi(wallet):
    memo = get_contract(w3, addys['MEMO'])
    initial_amount = memo.functions.balanceOf(wallet.address).call()
    payouts = dict()
    for k in 'MIM', 'WAVAX':
        payouts[k] = wallet.call(autobond.functions.payoutForERC20(addys[k]))
        payouts[k+'LP'] = wallet.call(autobond.functions.payoutForLP(addys[k]))

    best_amount, best_bond = max((payout, bond) for bond, payout in payouts.items())
    initial_roi = best_amount / initial_amount
    rebase = get_rebase()
    claim_and_stake_roi = ((1+rebase)**16-1-rebase)/(15*rebase)
    final_roi = initial_roi * claim_and_stake_roi
    stake_roi = (1 + rebase)**15
    print(f'{stake_roi:.4f} {final_roi:.4f} {initial_roi:.4f} {best_bond}')
    if stake_roi > final_roi:
        return stake_roi, stake_roi, 1.0, None
    else:
        return stake_roi, final_roi, initial_roi, best_bond


def approve(token, wallet, spender):
    infinite = 2**256 - 1
    contract = get_contract(w3, token)
    allowance = contract.functions.allowance(wallet.address, spender).call()
    if allowance < infinite//2:
        approval = contract.functions.approve(spender, infinite)
        wallet.transact(approval, gas=50000)


def get_minimum(w3, wallet, initial_roi):
    memo = get_contract(w3, addys['MEMO'])
    balance = memo.functions.balanceOf(wallet.address).call()
    print('balance', balance)
    context = decimal.Context(prec=5, rounding=decimal.ROUND_DOWN)
    num, denom = context.create_decimal_from_float(initial_roi).as_integer_ratio() 
    minimum = (balance * num * 99) // (100 * denom)
    print('minimum', minimum)
    print('roi >=', minimum/balance)
    return minimum


def main(argv):
    dry_run = False
    account = argv[1] if len(argv) > 1 else 'account'
    wallet = Wallet(w3, account)
    approve(addys['MEMO'], wallet, autobond_address)

    print(wallet.address)
    initial_roi = 1
    stake_roi = 10.
    discount = 0.995
    while initial_roi < discount * stake_roi:
        stake_roi, final_roi, initial_roi, collateral = best_roi(wallet)
        print(f'{initial_roi:.4f} {(discount * stake_roi):.4f}')
        time.sleep(5)

    if collateral is None:
        return
    depo = get_contract(w3, bonds[collateral])
    vested = depo.functions.percentVestedFor(wallet.address).call()
    x, y, z, vesting = depo.functions.bondInfo(wallet.address).call()
    print(vested)
    print(x,y,z,vesting)
    if vesting > 8 * 3600:
        print(f'existing {collateral} bond not close to vested')
        return
    minimum = get_minimum(w3, wallet, initial_roi)
    if dry_run:
        return
    if collateral.endswith('LP'):
        tx = autobond.functions.mintWithLP(addys[collateral[:-2]], minimum)
        wallet.transact(tx)
    else:
        tx = autobond.functions.mintWithERC20(addys[collateral], minimum)
        wallet.transact(tx)
    

if __name__ == '__main__':
    import sys
    main(sys.argv) 
