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

import time, json, requests, os
from bs4 import BeautifulSoup
from goplus.token import Token
from config import logger

MAX_RETRIES = 3

def get_bscscan_api_key():
    if os.path.exists("api.txt"):
        try:
            with open("api.txt", "r") as file:
                api_key = file.read().strip()
            return api_key
        except Exception as e:
            logger.error(f"Error reading API key: {e}")
            return ""
    return ""

def perform_pre_check_step_1(contract_address):
    """
    Check if a token is safe based on contract verification and ABI analysis.

    A token is considered NOT SAFE if:
    1. The contract is not verified on BSCScan
    2. The contract ABI contains a function named "isOwner"

    Returns:
        bool: True if the token is safe, False otherwise
    """
    api_key = get_bscscan_api_key()
    url = f"https://api.bscscan.com/api?module=contract&action=getabi&address={contract_address}&apikey={api_key}"

    try:
        for _ in range(3):
            response = requests.get(url)
            data = response.json()
            if data["status"] == "1" and data["message"] == "OK":
                break
            time.sleep(10)
        else:
            logger.debug(f"Pre-check for {contract_address}: Token not verified.")
            return False

        try:
            abi = json.loads(data["result"])
            for item in abi:
                if item.get("type") == "function" and item.get("name") == "isOwner":
                    logger.debug(f"Pre-check for {contract_address}: Token not safe.")
                    return False

            logger.debug(f"Pre-check for {contract_address}: Token is safe.")
            return True
        except Exception as e:
            logger.error(f"Pre-check for {contract_address}: Error parsing ABI: {e}")
            return False
    except Exception as e:
        logger.error(f"Pre-check for {contract_address}: Error during contract verification check: {e}")
        return False


def perform_pre_check_step_2(contract_address):
    """
    Check if a token is safe based on similar contracts on BSCScan.
    A token is considered NOT SAFE if similar contracts are found.

    Returns:
        bool: True if the token is safe, False otherwise
    """
    url = f"https://bscscan.com/find-similar-contracts?a={contract_address}&m=exact&ps=10&mt=56"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            logger.error(f"Pre-check for {contract_address}: Failed to retrieve similar contracts data from BscScan.")
            return False

        soup = BeautifulSoup(response.content, 'html.parser')

        if "There are no matching entries" in response.text:
            logger.debug(f"Pre-check for {contract_address}: Token is safe.")
            return True

        table = soup.find('table', {'class': 'table'})
        if not table:
            logger.debug(f"Pre-check for {contract_address}: Token is safe.")
            return True

        rows = table.find_all('tr')[1:]
        if rows:
            logger.debug(f"Pre-check for {contract_address}: Token is not safe.")
            return False
        else:
            logger.debug(f"Pre-check for {contract_address}: Token is safe.")
            return True

    except Exception as e:
        logger.error(f"Pre-check: Error during similar contracts check: {e}")
        return False

def calculate_security_score(token_data):
    score = 100

    if token_data.get('is_honeypot') == '1':
        score -= 100
        return score

    if token_data.get('cannot_sell_all') == '1':
        score -= 90

    if token_data.get('cannot_buy') == '1':
        score -= 80

    if token_data.get('is_blacklisted') == '1':
        score -= 70

    if token_data.get('hidden_owner') == '1':
        score -= 60

    if token_data.get('can_take_back_ownership') == '1':
        score -= 50

    if token_data.get('selfdestruct') == '1':
        score -= 50

    try:
        buy_tax_value = token_data.get('buy_tax')
        sell_tax_value = token_data.get('sell_tax')
        buy_tax = float(buy_tax_value if buy_tax_value is not None else '0')
        sell_tax = float(sell_tax_value if sell_tax_value is not None else '0')
        if buy_tax > 10 or sell_tax > 10:
            score -= 40
        elif buy_tax > 5 or sell_tax > 5:
            score -= 20
        elif buy_tax > 0 or sell_tax > 0:
            score -= 10
    except (ValueError, TypeError):
        score -= 20

    if token_data.get('is_mintable') == '1':
        score -= 30

    if token_data.get('is_proxy') == '1':
        score -= 25

    if token_data.get('transfer_pausable') == '1':
        score -= 30

    if token_data.get('trading_cooldown') == '1':
        score -= 20

    if token_data.get('slippage_modifiable') == '1':
        score -= 40

    if token_data.get('personal_slippage_modifiable') == '1':
        score -= 30

    if token_data.get('is_open_source') != '1':
        score -= 20

    if token_data.get('is_in_dex') != '1':
        score -= 15

    if token_data.get('trust_list') == '1':
        score += 10

    return max(0, min(100, score))

def perform_safety_check(tokentobuy, chain_id, min_safety_score):
    token_api = Token()
    first_iteration = True
    retries = 0

    while retries < MAX_RETRIES:
        if first_iteration:
            logger.debug(f"Performing Safety Checks for Token: {tokentobuy}")
            first_iteration = False

        try:
            response = token_api.token_security(chain_id=chain_id, addresses=[tokentobuy])

            response_dict = response.to_dict()
            result = response_dict.get('result', {})
            token_data = result.get(tokentobuy.lower(), {})

            if token_data:
                security_score = calculate_security_score(token_data)

                logger.debug(f"Token Security Score: {security_score}%")
                logger.debug(f"Honeypot: {token_data.get('is_honeypot', 'N/A')}")
                logger.debug(f"Buy Tax: {token_data.get('buy_tax', 'N/A')}")
                logger.debug(f"Sell Tax: {token_data.get('sell_tax', 'N/A')}")

                is_safe = security_score >= min_safety_score

                if is_safe:
                    logger.debug(f"Token passed safety check with score: {security_score}%")
                    return is_safe, security_score

                return is_safe, security_score
            else:
                logger.debug("Token security data not available. Retrying in 30 seconds.")
                retries += 1
                time.sleep(30)

        except Exception as e:
            logger.warning(f"Request error: {str(e)}. Retrying.")
            retries += 1
            time.sleep(10)

    logger.warning("Max retry limit hit; operation aborted. If this issue persists, please submit an issue request on GitHub.")
    return False, 0

def check_token_safety(tokentobuy, chain_id, min_safety_score):
    score = 'N/A'
    try:
        # Step 1: Perform pre-check for contract verification and isOwner function
        logger.debug(f"Performing pre-check Step 1 for token {tokentobuy}")
        is_pre_check_1_safe = perform_pre_check_step_1(tokentobuy)

        if not is_pre_check_1_safe:
            logger.warning(f"Token failed pre-check Step 1. Skipping further checks.")
            return False, 0

        # Temporarily commenting out Step 2 checks
        # Step 2: Perform pre-check for similar contracts
        # logger.debug(f"Performing pre-check Step 2 for token {tokentobuy} in 30 seconds")
        # is_pre_check_2_safe = perform_pre_check_step_2(tokentobuy)
        #
        # if not is_pre_check_2_safe:
        #     logger.warning(f"Token failed pre-check Step 2. Skipping further checks.")
        #     return False, 0

        # If token passed both pre-check steps, proceed with goplus security checks
        logger.debug(f"Token passed pre-checks. Proceeding with goplus security check in 30 seconds...")
        time.sleep(30)
        is_safety_valid, score = perform_safety_check(tokentobuy, chain_id, min_safety_score)

        if is_safety_valid:
            logger.info(f"Token passed all security checks with score: {score}%")
            return True, score

        return False, score

    except Exception as e:
        logger.error(f"Error in check_token_safety: {e}")
        return False, score
