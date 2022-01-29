from wallet import Wallet
from utils import get_contract
from contextlib import ContextDecorator

from web3 import Web3
from web3.middleware import geth_poa_middleware

#w3 = Web3(Web3.WebsocketProvider('ws://localhost:8545'))
w3 = Web3(Web3.HTTPProvider('https://api.avax.network/ext/bc/C/rpc'))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)
autobond_address = '0xE1fbbC84Ce1c37EBDBb6CC3be1Be68CdfD484716'
autobond_abi = autobond_abi = [
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
          "name": "_amount",
          "type": "uint256"
        },
        {
          "internalType": "uint256",
          "name": "_minimum",
          "type": "uint256"
        }
      ],
      "name": "mintWithAVAXLP",
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
          "name": "_amount",
          "type": "uint256"
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
          "name": "_amount",
          "type": "uint256"
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
        },
        {
          "internalType": "uint256",
          "name": "_amount",
          "type": "uint256"
        }
      ],
      "name": "payoutForAVAXLP",
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
        },
        {
          "internalType": "uint256",
          "name": "_amount",
          "type": "uint256"
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
      "name": "getAmountERC20",
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
        },
        {
          "internalType": "uint256",
          "name": "_amount",
          "type": "uint256"
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

addys = {'DAI': '0xd586E7F844cEa2F87f50152665BCbc2C279D8d70',
         'sMAXI': '0xEcE4D1b3C2020A312Ec41A7271608326894076b4',
         'MAXI': '0x7C08413cbf02202a1c13643dB173f2694e0F73f0',
         'WAVAX': '0xB31f66AA3C1e785363F0875A1B74E27b85FD66c7',
         'DAILP': '0xfBDC4aa69114AA11Fae65E858e92DC5D013b2EA9',
         'STAKE': '0x6d7AD602Ec2EFdF4B7d34A9A53f92F06d27b82B1',
         'HELPER': '0x93c375fDA3158b18889437D30049F2ABeFA34275',
         'PNG': '0x60781C2586D68229fde47564546784ab3fACA982',
        }
bonds = {'WAVAX': '0xA4D6757E6F313eA8857F50547F0CE4946fF1EB84',
         'DAILP': '0xA4EbD64423a6FF9baE958Bd0A38Fc216F41b3ef6',
         'DAI': '0x103F6bd55C192b86aD576C0c36Be7AB0945Ebe48',
         'WAVAXLP': '0x03F40AC35171E2ab7451B1410cF4e00f1D1915ce',
         'PNGLPW': '0x20F91e4b39f405EFa821a11543a8C03265045b84',
        }


class pinned_block(ContextDecorator):
    def __enter__(self):
        block = w3.eth.get_block('latest')
        w3.eth.default_block = block.number
        return self

    def __exit__(self, *exc):
        w3.eth.default_block = 'latest' 
        return False


@pinned_block()
def determine_amount(wallet, func, asset):
    smaxi = get_contract(w3, addys['sMAXI'])
    with pinned_block() as blk:
        hi = smaxi.functions.balanceOf(wallet.address).call()
        lo = 1000000
        try:
            wallet.call(func(addys[asset], hi))
        except Exception as e:
            stre = str(e)
            if not 'Bond too large' in stre:
                raise
        else:
            return hi
        while 100 * lo < 99 * hi:
            mid = (hi + lo)//2
            try:
                wallet.call(func(addys[asset], mid))
            except Exception as e:
                stre = str(e)
                if 'Bond too large' in stre:
                    hi = mid
                else:
                    raise
            else:
                lo = mid
        return lo


def contract_state():
    for addy in addys:
        try:
            amount = get_contract(w3, addys[addy]).functions.balanceOf(autobond).call()
            if amount > 0:
                print('contract', addy, amount)
        except:
            pass


def wallet_state(wallet):
    for addy in addys:
        try:
            amount = get_contract(w3, addys[addy]).functions.balanceOf(wallet.address).call()
            if amount > 0:
                print('wallet', addy, amount)
        except:
            pass


def bond_state(wallet):
    for addy in bonds:
        print('bond', addy, get_contract(w3, bonds[addy]).functions.bondInfo(wallet.address).call())


def get_rebase():
    memo = get_contract(w3, addys['sMAXI'])
    stake = get_contract(w3, addys['STAKE'])
    circ = memo.functions.circulatingSupply().call()
    epoch = stake.functions.epoch().call()
    return epoch[1]/circ


def best_bond(wallet):
    smaxi = get_contract(w3, addys['sMAXI'])
    rebase = get_rebase()
    stake_roi = (1+rebase)**15
    claim_roi = ((1+rebase)**16-1-rebase)/(15*rebase)
    best = None, 1.01 * stake_roi, 0, 0
    balance = smaxi.functions.balanceOf(wallet.address).call()
    print(f'sMAXI balance {balance}')
    if balance < 10000000:
        print(f'insufficient maxi balance {balance}. bailing')
        return best
    for bond in bonds:
        depo = get_contract(w3, bonds[bond])
        maxi_remaining_to_be_paid, _, _, seconds_left_to_vest = depo.functions.bondInfo(wallet.address).call()
        last_epoch = seconds_left_to_vest < 8 * 3600
        first_epoch = seconds_left_to_vest == 5 * 24 * 3600
        if first_epoch or last_epoch: 
            continue
        if maxi_remaining_to_be_paid > 0:
            print(f'bond {bond} has {maxi_remaining_to_be_paid} maxi to be vested. bailing')
            return best
    for bond in bonds:
        depo = get_contract(w3, bonds[bond])
        _, _, _, seconds_left_to_vest = depo.functions.bondInfo(wallet.address).call()
        last_epoch = seconds_left_to_vest < 8 * 3600
        first_epoch = seconds_left_to_vest == 5 * 24 * 3600 # seconds_left_to_vest updates to a smaller value when we claim, i.e. at first rebase 
        if not (first_epoch or last_epoch):
            continue
        if bond.endswith('LP'):
            asset = bond[:-2]
            amt =  determine_amount(wallet, autobond.functions.payoutForLP, asset)
            payout = wallet.call(autobond.functions.payoutForLP(addys[asset], amt))
        elif bond.endswith('LPW'):
            asset = bond[:-3]
            try:
                amt =  determine_amount(wallet, autobond.functions.payoutForAVAXLP, asset)
            except Exception as e:
                if 'Max deposit limit reached' in str(e):
                    continue
                else:
                    raise
            payout = wallet.call(autobond.functions.payoutForAVAXLP(addys[asset], amt))
        else:
            asset = bond
            amt =  determine_amount(wallet, autobond.functions.payoutForERC20, asset)
            payout = wallet.call(autobond.functions.payoutForERC20(addys[asset], amt))
        initial_roi = payout / amt
        roi = initial_roi * claim_roi
        if roi > best[1]:
            best = bond, roi, amt, payout
    return best


def summarize_bonds(wallet):
    print('='*20)
    for bond in bonds:
        depo = get_contract(w3, bonds[bond])
        vested = depo.functions.percentVestedFor(wallet.address).call()
        maxi_remaining_to_be_paid, price_paid, last_interaction, seconds_left_to_vest = depo.functions.bondInfo(wallet.address).call()
        print(bond, vested, maxi_remaining_to_be_paid/1e9, price_paid/1e18, last_interaction, seconds_left_to_vest)
    print('='*20)


def purchase(wallet):
    best_asset, roi, amt, payout = best_bond(wallet)
    payout_with_slippage = 99 * payout // 100
    errors = 0
    while best_asset is not None and errors < 10:
        print(best_asset, roi, amt, payout)
        try:
            if best_asset.endswith('LP'):
                asset = best_asset[:-2]
                wallet.transact(autobond.functions.mintWithLP(addys[asset], amt, payout_with_slippage))
            elif best_asset.endswith('LPW'):
                asset = best_asset[:-3]
                wallet.transact(autobond.functions.mintWithAVAXLP(addys[asset], amt, payout_with_slippage))
            else:
                asset = best_asset
                wallet.transact(autobond.functions.mintWithERC20(addys[asset], amt, payout_with_slippage))
            summarize_bonds(wallet)
        except Exception as e:
            if not 'insufficient profit' in str(e):
                raise
            else:
                errors += 1
        best_asset, roi, amt, payout = best_bond(wallet)
        payout_with_slippage = 99 * payout // 100


def approve(token, wallet, spender):
    infinite = 2**256 - 1
    contract = get_contract(w3, token)
    allowance = contract.functions.allowance(wallet.address, spender).call()
    if allowance < infinite//2:
        approval = contract.functions.approve(spender, infinite)
        wallet.transact(approval, gas=50000)


def main(argv):
    dry_run = False
    account = argv[1] if len(argv) > 1 else 'account'
    wallet = Wallet(w3, account)

    approve(addys['sMAXI'], wallet, autobond_address)
    print(wallet.address)

    if dry_run:
        best_asset, roi, amt, payout = best_bond(wallet)
        print(best_asset, roi, payout, amt, payout/amt if amt > 0 else roi)
    else:
        purchase(wallet)
    contract_state()
    wallet_state(wallet)
    bond_state(wallet)

if __name__ == '__main__':
    import sys
    main(sys.argv) 


