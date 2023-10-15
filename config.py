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

import sys
import json
import logging
from web3 import Web3
from web3.middleware import geth_poa_middleware

# Configure logging for trade history to a file.
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

trade_logger = logging.getLogger('trade_logger')
trade_handler = logging.FileHandler('trade_history.log')
trade_handler.setLevel(logging.INFO)
trade_logger.addHandler(trade_handler)

# Initialize and connect to the Binance Smart Chain node using Web3.
w3 = Web3(Web3.HTTPProvider('https://bsc-dataseed2.binance.org'))
if w3.is_connected():
    logging.info("Connected to node.")
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)
else:
    logging.error("Node connection failed.")
    sys.exit(1)

MY_ADDRESS = '0xYour_Wallet_Address'
PRIVATE_KEY = '0xYour_Private_Key'
WBNB_ADDRESS = '0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c'
ROUTER_ADDRESS = '0x10ED43C718714eb63d5aA57B78B54704E256024E'
FACTORY_ADDRESS = '0xcA143Ce32Fe78f1f7019d7d551a6402fC5350c73'
PAIR_CREATED_TOPIC = '0x0d3648bd0f6ba80134a33ba9275ac585d9d315f0ad8355cddefde31afa28d0e9'
MINIMUM_SLEEP = 3

# BSCSCAN API
BSCSCAN_API_KEY = "YOUR_API_KEY" # Obtain it from https://bscscan.com/myapikey

def load_abi_from_file(filename):
    """Load ABI (Application Binary Interface) from a JSON file."""
    with open(filename, 'r', encoding='utf-8') as f:
        return json.load(f)

# ABI Files
factory_abi = load_abi_from_file('factory_abi.json')
router_abi = load_abi_from_file('router_abi.json')
pair_abi = load_abi_from_file('pair_abi.json')
wbnb_abi = load_abi_from_file('wbnb_abi.json')

# Create Instances
router = w3.eth.contract(address=ROUTER_ADDRESS, abi=router_abi)
wbnb = w3.eth.contract(address=WBNB_ADDRESS, abi=wbnb_abi)

# Create filter for 'PairCreated' events
event_filter = w3.eth.filter({
    'address': FACTORY_ADDRESS,
    'topics': [PAIR_CREATED_TOPIC]
})
