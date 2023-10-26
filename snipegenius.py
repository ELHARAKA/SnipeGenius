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
    base_url = "https://tokensniffer.com/api/v2/tokens"
    query_params = {
        "apikey": token_sniffer_api_key,
        "include_metrics": "true",
        "include_tests": "true",
        "block_until_ready": "false"
    }
    query_string = "&".join(f"{k}={v}" for k, v in query_params.items())
    tokensniffer_url = f"{base_url}/{chain_id}/{tokentobuy}?{query_string}"

    safety_checks = {
        'score': lambda x: x == 100
    }

    total_checks = len(safety_checks)
    passed_checks = 0

    while True:
        try:
            logger.debug(f"New Token Found: {tokentobuy}")
            logger.info("Performing Safety Checks...")
            # Token Sniffer check
            tokensniffer_response = requests.get(tokensniffer_url)
            tokensniffer_response.raise_for_status()
            tokensniffer_data = json.loads(tokensniffer_response.text)
            file_logger.debug(f"{tokensniffer_data}")

            if tokensniffer_data.get('status') == 'ready':
                for key, expected_value in safety_checks.items():
                    actual_value = tokensniffer_data.get(key, 'N/A')
                    if callable(expected_value):
                        try:
                            float_actual_value = float(actual_value)
                        except ValueError:
                            file_logger.debug(f"Check failed for {key}: {actual_value}")
                            continue

                        if expected_value(float_actual_value):
                            passed_checks += 1

                logger.info(f"Token Safety Score: {tokensniffer_data.get('score', 'N/A')}")
                break  # exit the while loop

            elif tokensniffer_data.get('status') == 'pending':
                logger.info("Token data is pending. Retrying in 7 seconds.")
                time.sleep(7)

        except requests.exceptions.RequestException as e:
            file_logger.error(f"Request error: {e}")

        except json.JSONDecodeError as e:
            file_logger.error(f"JSON decoding error: {e}")

    return passed_checks == total_checks

def check_token_safety(tokentobuy, chain_id):
    try:
        time.sleep(7)
        is_safety_valid, score = perform_safety_check(tokentobuy, chain_id)

        if is_safety_valid:
            return True, score

        return False, score

    except Exception as e:
        return False, 'N/A'
