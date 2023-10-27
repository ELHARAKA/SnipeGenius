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

import json
import time
import requests
from config import logger, file_logger

MAX_RETRIES = 3

def is_blacklisted(tokentobuy, w3):
    # ABI for ERC-20 owner function
    abi = [{
        "constant": True,
        "inputs": [],
        "name": "owner",
        "outputs": [{"name": "", "type": "address"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    }]
    token_contract = w3.eth.contract(address=tokentobuy, abi=abi)
    owner_address = token_contract.functions.owner().call()

    with open('blacklist.txt', 'r') as file:
        blacklist = file.read().splitlines()

    return owner_address.lower() in blacklist

def perform_safety_check(tokentobuy, chain_id):
    from config import token_sniffer_api_key

    base_url = "https://tokensniffer.com/api/v2/tokens/"
    query_params = (
        f"apikey={token_sniffer_api_key}&"
        "include_metrics=true&"
        "include_tests=true&"
        "block_until_ready=false"
    )

    tokensniffer_url = f"{base_url}{chain_id}/{tokentobuy}?{query_params}"

    first_iteration = True
    retries = 0
    while retries < MAX_RETRIES:
        if first_iteration:
            logger.debug(f"New Token Found: {tokentobuy}")
            logger.info("Performing Safety Checks...")
            first_iteration = False
        try:
            response = requests.get(tokensniffer_url)
            response.raise_for_status()
            data = json.loads(response.text)

            if data.get('status') == 'ready':
                score = data.get('score', 'N/A')
                try:
                    float_score = float(score)
                except ValueError:
                    logger.error(f"Score conversion failed: {score}")
                    return False

                is_safe = float_score == 100
                logger.info(f"Token Safety Score: {score}")
                return is_safe

            else:
                logger.info("Token data is pending. Retrying in 10 seconds.")
                retries += 1
                time.sleep(10)

        except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
            logger.error(f"Request error: {e}. Retrying.")
            retries += 1
            time.sleep(10)

    logger.error("Max retries reached. Aborting.")
    return False

def check_token_safety(tokentobuy, chain_id, w3):  # Add w3 as an argument
    try:
        # Check if the owner of the token is blacklisted
        if is_blacklisted(tokentobuy, w3):
            logger.warning(f"The owner of Token {tokentobuy} is blacklisted.")
            return False, 'Owner Blacklisted'

        time.sleep(10)
        is_safety_valid, score = perform_safety_check(tokentobuy, chain_id)

        if is_safety_valid:
            return True, score

        return False, score

    except Exception as e:
        return False, 'N/A'
