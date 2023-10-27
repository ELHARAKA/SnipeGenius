# SnipeGenius 🥞 (PancakeSwap)
# Version: 1.5.3
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

def perform_safety_check(tokentobuy, chain_id):
    from config import token_sniffer_api_key

    base_url = "https://tokensniffer.com/api/v2/tokens/"
    query_params = (
        f"apikey={token_sniffer_api_key}&"
        "include_metrics=true&"
        "include_tests=false&"
        "block_until_ready=true"
    )

    tokensniffer_url = f"{base_url}{chain_id}/{tokentobuy}?{query_params}"

    first_iteration = True
    retries = 0
    while retries < MAX_RETRIES:
        if first_iteration:
            logger.info(f"Token Address: {tokentobuy}")
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
                    logger.error(f"Score conversion failed: {score}%")
                    return False

                is_safe = float_score == 100
                logger.debug(f"Token Safety Score: {score}%")
                return is_safe, score

            else:
                file_logger.info("Token data is pending. Retrying in 10 seconds.")
                retries += 1
                time.sleep(10)

        except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
            sanitized_error = str(e).replace(token_sniffer_api_key, 'HIDDEN')
            file_logger.error(f"Request error: {sanitized_error}. Retrying.")
            retries += 1
            time.sleep(10)

    logger.error("Max retry limit hit; operation aborted. If this issue persists, please submit an issue request on GitHub.")
    return False

def check_token_safety(tokentobuy, chain_id, w3):
    score = 'N/A'
    try:
        time.sleep(10)
        is_safety_valid, score = perform_safety_check(tokentobuy, chain_id)

        if is_safety_valid:
            return True, score

        return False, score

    except Exception as e:
        logger.error(f"Error in check_token_safety: {e}")
        return False, score
