from wallet import Wallet
from utils import get_contract

from web3 import Web3
from web3.middleware import geth_poa_middleware
w3 = Web3(Web3.WebsocketProvider('wss://api.avax.network/ext/bc/C/ws'))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)

autobond = '0x64457da2701dD638D9fc451F9FbE88B4485Aa6C8'
abi = [
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
        }
      ],
      "name": "mintWithLP",
      "outputs": [],
      "stateMutability": "nonpayable",
      "type": "function"
    }
  ]

autobond_contract = w3.eth.contract(address=autobond, abi=abi)

addys = {
    'MIM': '0x130966628846BFd36ff31a822705796e8cb8C18D',
    'MEMO': '0x136Acd46C134E8269052c62A67042D6bDeDde3C9',
    'TIME': '0xb54f16fB19478766A268F172C9480f8da1a7c9C3',
    'WAVAX': '0xB31f66AA3C1e785363F0875A1B74E27b85FD66c7',
    'MIMLP': '0x113f413371fC4CC4C9d6416cf1DE9dFd7BF747Df',
    'WAVAXLP': '0xf64e1c5B6E17031f5504481Ac8145F4c3eab4917',
    'STAKE': '0x4456B87Af11e87E329AB7d7C7A246ed1aC2168B9',
    'JOEROUTER': '0x60aE616a2155Ee3d9A68541Ba4544862310933d4', 
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


def get_time_price():
    lp = get_contract(w3, addys['MIMLP'])
    rmim, rtime, _ = lp.functions.getReserves().call()
    return (rmim/1e9)/rtime


def best_roi():
    prices = dict() 
    avax_price = None
    for k in bonds:
        depo = get_contract(w3, bonds[k])
        prices[k] = depo.functions.bondPriceInUSD().call()/1e18
        if k == 'WAVAX':
            avax_price = depo.functions.assetPrice().call() / 1e8
    prices['WAVAXLP'] *= avax_price
    best_price, best_bond = min((price, bond) for bond, price in prices.items())
    time_price = get_time_price()
    initial_roi = time_price / best_price
    rebase = get_rebase()
    claim_and_stake_roi = ((1+rebase)**16-1-rebase)/(15*rebase)
    final_roi = initial_roi * claim_and_stake_roi
    stake_roi = (1 + rebase)**15 
    print(stake_roi, final_roi, best_bond)
    if stake_roi > final_roi:
        return stake_roi, None
    else:
        return final_roi, best_bond


def approve(token, wallet, spender):
    infinite = 2**256 - 1
    contract = get_contract(w3, token)
    allowance = contract.functions.allowance(wallet.address, spender).call()
    if allowance < infinite//2:
        approval = contract.functions.approve(spender, infinite)
        wallet.transact(approval, gas=50000)
    

def main():
    dry_run = True
    wallet = Wallet(w3)
    approve(addys['MEMO'], wallet, autobond)
    roi, collateral = best_roi()
    if collateral is None:
        return
    if dry_run:
        return
    if collateral.endswith('LP'):
        tx = autobond_contract.functions.mintWithLP(addys[collateral[:-2]], 0)
        wallet.transact(tx)
    else:
        tx = autobond_contract.functions.mintWithERC20(addys[collateral], 0)
        wallet.transact(tx)
    

if __name__ == '__main__':
    main() 
