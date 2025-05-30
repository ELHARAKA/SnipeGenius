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

import colorlog, json, pyfiglet, logging
from termcolor import colored
from sys import exit
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware
from wallet import get_credentials

def display_splash():
    ascii_art = pyfiglet.figlet_format("SnipeGenius")
    print(colored(ascii_art, 'white'))

    print("--------------------------------------------------------")
    print(colored("SnipeGenius 🥞 Version: 3.0", 'yellow'))
    print("--------------------------------------------------------\n")
    print("Developed by " + colored("Fahd El Haraka ©", 'red'))
    print("Telegram: " + colored("@thisiswhosthis", 'red'))
    print("Website: " + colored("https://web3dev.ma", 'red'))
    print("GitHub: " + colored("https://github.com/ELHARAKA", 'red'))
    print("--------------------------------------------------------\n")

display_splash()

# Set up a single unified logger
log_format = '[%(asctime)s] %(message)s'
date_format = '%Y-%m-%d %H:%M:%S'

# Create console handler with colored output
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

# Create file handler that always logs everything
file_handler = logging.FileHandler('trade_history.log')
file_handler.setLevel(logging.DEBUG)  # File always gets all logs
file_handler.setFormatter(logging.Formatter(log_format, datefmt=date_format))

# Set up main logger
logger = logging.getLogger('snipegenius')
logger.setLevel(logging.DEBUG)  # Logger itself can process all levels
logger.addHandler(file_handler)
logger.addHandler(stream_handler)

# Default console to INFO level initially
stream_handler.setLevel(logging.INFO)

# Make sure we don't get duplicate logs
logger.propagate = False

minimum_sleep = 3
my_address = ""
private_key = ""
bscscan_api_key = ""
WEB3_PROVIDER = "https://bsc-dataseed3.binance.org"

w3 = Web3(Web3.HTTPProvider(WEB3_PROVIDER))
w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

if w3.is_connected():
    logger.info("Connected to node.")
else:
    exit(1)

def initialize_logging(verbosity):
    if verbosity == 2:
        stream_handler.setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled.")
    else:
        stream_handler.setLevel(logging.INFO)

def update_credentials(address, key, api_key=None):
    global my_address, private_key, bscscan_api_key
    my_address = address
    private_key = key
    if api_key:
        bscscan_api_key = api_key

def load_api_key():
    global bscscan_api_key
    from wallet import get_api_key
    api_key = get_api_key()
    if api_key:
        bscscan_api_key = api_key
    return api_key

def initialize_credentials():
    global my_address, private_key, bscscan_api_key
    load_api_key()
    my_address, private_key, api_key = get_credentials()
    if api_key:
        bscscan_api_key = api_key

    if not my_address or not private_key:
        logger.error("Failed to load wallet credentials. Please check your wallet.txt file or re-import your wallet.")
    else:
        logger.info(f"Credentials loaded successfully. Wallet address: {my_address}")

    if not bscscan_api_key:
        logger.error("Failed to load BSCScan API key. Please check your api.txt file.")

    update_credentials(my_address, private_key, bscscan_api_key)

pair_created_topic = '0x0d3648bd0f6ba80134a33ba9275ac585d9d315f0ad8355cddefde31afa28d0e9'
wbnb_address = '0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c'
router_address = '0x10ED43C718714eb63d5aA57B78B54704E256024E'
factory_address = '0xcA143Ce32Fe78f1f7019d7d551a6402fC5350c73'

def load_abi_from_file(filename):
    with open(filename, 'r') as f:
        return json.load(f)

factory_abi = load_abi_from_file('abi/factory_abi.json')
router_abi = load_abi_from_file('abi/router_abi.json')
pair_abi = load_abi_from_file('abi/pair_abi.json')
wbnb_abi = load_abi_from_file('abi/wbnb_abi.json')
token_abi = load_abi_from_file('abi/token_abi.json')
router = w3.eth.contract(address=router_address, abi=router_abi)
wbnb = w3.eth.contract(address=wbnb_address, abi=wbnb_abi)

# Exit strategy configuration
EXIT_STRATEGY_ENABLED = True
INITIAL_MONITORING_DURATION = 240
DYNAMIC_PROTECTION_DURATION = 300
TRAILING_STOP_PERCENTAGE = 0.05
TIERED_EXIT_MULTIPLIERS = [1.5, 2, 3]
pair_created_event_abi = next(event_abi for event_abi in factory_abi if event_abi['type'] == 'event' and event_abi['name'] == 'PairCreated')
event_filter = w3.eth.filter({'address': factory_address, 'topics': [pair_created_topic]})