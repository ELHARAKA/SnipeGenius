# SnipeGenius 🥞 (PancakeSwap)
# Version: 1.5.2
# Developed by Fahd El Haraka ©
# Email: fahd@web3dev.ma
# Telegram: @thisiswhosthis
# Website: https://web3dev.ma
# GitHub: https://github.com/ELHARAKA

"""
© Copyright 2023
Proprietary Software by Fahd El Haraka, 2023.
Unauthorized use, duplication, modification, or distribution is strictly prohibited.
Contact fahd@web3dev.ma for permissions and inquiries.
"""

from config import w3, wbnb

# Get Token balance
def get_token_balance(tokentobuy):
    from config import my_address
    # ABI for BEP-20 balanceOf function
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

# Get WBNB balance function
def get_wbnb_balance():
    from config import my_address
    balance = wbnb.functions.balanceOf(my_address).call()
    return balance