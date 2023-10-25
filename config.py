# SnipeGenius 🥞 (PancakeSwap)
# Version: 1.5.0_Stable
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

import logging
import pyfiglet
import colorlog
from termcolor import colored
import json
from sys import exit
from web3 import Web3
from web3.middleware import geth_poa_middleware
from wallet import get_credentials, get_google_details

def display_splash():
    ascii_art = pyfiglet.figlet_format("SnipeGenius")
    print(colored(ascii_art, 'white'))

    print("--------------------------------------------------------")
    print(colored("SnipeGenius 🥞 Version: 1.5.0_Stable", 'yellow'))
    print("--------------------------------------------------------\n")
    print("Developed by " + colored("Fahd El Haraka ©", 'red'))
    print("Telegram: " + colored("@thisiswhosthis", 'red'))
    print("Website: " + colored("https://web3dev.ma", 'red'))
    print("GitHub: " + colored("https://github.com/ELHARAKA", 'red'))
    print("--------------------------------------------------------\n")

display_splash()

# Common logging format and date format
log_format = '[%(asctime)s] %(message)s'
date_format = '%Y-%m-%d %H:%M:%S'

# Shared stream handler for logging to terminal with color
stream_handler = colorlog.StreamHandler()
stream_handler.setFormatter(colorlog.ColoredFormatter(
    '%(log_color)s' + log_format,
    datefmt=date_format,
    log_colors={
        'DEBUG': 'cyan',
        'INFO': 'green',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'red,bg_white'
    }
))
stream_handler.setLevel(logging.INFO)  # default level

# Set up logger for logging to both file and terminal
logger = logging.getLogger('logger')
logger.setLevel(logging.INFO)  # default level

# File handler for logging to file
file_handler = logging.FileHandler('trade_history.log')
file_handler.setLevel(logging.INFO)  # default level
file_handler.setFormatter(logging.Formatter(log_format, datefmt=date_format))
logger.addHandler(file_handler)
logger.addHandler(stream_handler)  # add shared stream handler

# Set up file_logger for logging to file only (by default)
file_logger = logging.getLogger('file_logger')
file_logger.setLevel(logging.INFO)  # default level
file_file_handler = logging.FileHandler('trade_history.log')
file_file_handler.setLevel(logging.INFO)  # default level
file_file_handler.setFormatter(logging.Formatter(log_format, datefmt=date_format))
file_logger.addHandler(file_file_handler)

def initialize_logging(verbosity):
    log_level = logging.INFO  # default level

    if verbosity == 2:
        log_level = logging.DEBUG  # enabling debug logs for both logger and file_logger
        file_logger.addHandler(stream_handler)  # add shared stream handler to file_logger

    logger.setLevel(log_level)
    file_logger.setLevel(log_level)
    stream_handler.setLevel(log_level)  # adjust level of shared stream handler

# Initialize and connect to the Binance Smart Chain node using Web3.
w3 = Web3(Web3.HTTPProvider('https://bsc-dataseed2.binance.org')) # Better use a private node.
if w3.is_connected():
    logger.info("Connected to node.")
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)
else:
    logger.error("Node connection failed.")
    exit(1)

my_address = ""
private_key = ""
google_api_key = ""
google_cse_id = ""

def update_credentials(address, key, g_api_key, g_cse_id):
    global my_address, private_key, google_api_key, google_cse_id
    my_address = address
    private_key = key
    google_api_key = g_api_key
    google_cse_id = g_cse_id

def initialize_credentials():
    global my_address, private_key, google_api_key, google_cse_id
    my_address, private_key = get_credentials()
    google_api_key, google_cse_id = get_google_details()
    update_credentials(my_address, private_key, google_api_key, google_cse_id)

wbnb_address = '0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c'
router_address = '0x10ED43C718714eb63d5aA57B78B54704E256024E'
factory_address = '0xcA143Ce32Fe78f1f7019d7d551a6402fC5350c73'
minimum_sleep = 3

#Event Topic for "CreatedPair"
pair_created_topic = '0x0d3648bd0f6ba80134a33ba9275ac585d9d315f0ad8355cddefde31afa28d0e9'

# Load ABI (Application Binary Interface) from a JSON file
def load_abi_from_file(filename):
    with open(filename, 'r') as f:
        return json.load(f)

# ABI Files
factory_abi = load_abi_from_file('factory_abi.json')
router_abi = load_abi_from_file('router_abi.json')
pair_abi = load_abi_from_file('pair_abi.json')
wbnb_abi = load_abi_from_file('wbnb_abi.json')

# Create Instances
router = w3.eth.contract(address=router_address, abi=router_abi)
wbnb = w3.eth.contract(address=wbnb_address, abi=wbnb_abi)

# Create filter for 'PairCreated' events
event_filter = w3.eth.filter({
    'address': factory_address,
    'topics': [pair_created_topic]
})
