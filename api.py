# SnipeGenius 🥞 (PancakeSwap)
# Version: 1.0.1
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

from imports import requests, json
from config import BSCSCAN_API_KEY

def get_token_abi(tokentobuy):
    url = (
        f"https://api.bscscan.com/api?"
        f"module=contract&action=getabi&address={tokentobuy}"
    )
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    abi = json.loads(data['result'])
    return abi

def get_token_balance(tokentobuy, my_address):
    url = (
        f"https://api.bscscan.com/api?"
        f"module=account&action=tokenbalance&contractaddress={tokentobuy}"
        f"&address={my_address}&tag=latest&apikey={BSCSCAN_API_KEY}"
    )
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    balance = int(data['result'])
    return balance

def get_wbnb_balance(wbnb_address, my_address):
    url = (
        f"https://api.bscscan.com/api?"
        f"module=account&action=tokenbalance&contractaddress={wbnb_address}"
        f"&address={my_address}&tag=latest&apikey={BSCSCAN_API_KEY}"
    )
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    balance = int(data['result'])
    return balance
