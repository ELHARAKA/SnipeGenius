# SnipeGenius 🥞 (PancakeSwap)
# Version: 3.0
# Developed by Fahd El Haraka ©
# Email: fahd@web3dev.ma
# Telegram: @thisiswhosthis
# Website: https://web3dev.ma
# GitHub: https://github.com/ELHARAKA

"""
© Copyright 2023-2025
Proprietary Software by Fahd El Haraka,
Unauthorized use, selling, or distribution is strictly prohibited.
Contact fahd@web3dev.ma for permissions and inquiries.
"""

from config import my_address, w3, token_abi, logger
import sys

def get_token_balance(tokentobuy):
    abi = [{
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    }]

    token_contract = w3.eth.contract(address=tokentobuy, abi=abi)
    balance = token_contract.functions.balanceOf(my_address).call()
    return balance

def get_token_info(token_address):
    try:
        token_contract = w3.eth.contract(address=token_address, abi=token_abi)
        name = token_contract.functions.name().call()
        symbol = token_contract.functions.symbol().call()
        decimals = token_contract.functions.decimals().call()
        total_supply = token_contract.functions.totalSupply().call()

        return {
            "name": name,
            "symbol": symbol,
            "decimals": decimals,
            "total_supply": total_supply
        }
    except Exception as e:
        logger.error(f"Error getting token info: {str(e)}")
        return {
            "name": "Unknown",
            "symbol": "Unknown",
            "decimals": 18,
            "total_supply": 0
        }

def get_bnb_balance():
    balance = w3.eth.get_balance(my_address)
    if 'balance_manager' in sys.modules and 'balance_manager' in globals():
        try:
            from snipe import balance_manager
            if balance_manager is not None:
                balance_manager.update_balance()
        except Exception as e:
            logger.error(f"Error updating balance manager: {str(e)}")

    return balance
