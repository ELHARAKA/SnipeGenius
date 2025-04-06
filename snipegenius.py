# SnipeGenius 🥞 (PancakeSwap)
# Version: 2.6
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

import time
from goplus.token import Token
from config import logger, file_logger

MAX_RETRIES = 3

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
            logger.info(f"Token Address: {tokentobuy}")
            logger.info("Performing Safety Checks...")
            first_iteration = False

        try:
            response = token_api.token_security(chain_id=chain_id, addresses=[tokentobuy])

            response_dict = response.to_dict()
            result = response_dict.get('result', {})
            token_data = result.get(tokentobuy.lower(), {})

            if token_data:
                security_score = calculate_security_score(token_data)

                file_logger.info(f"Token Security Score: {security_score}%")
                file_logger.info(f"Honeypot: {token_data.get('is_honeypot', 'N/A')}")
                file_logger.info(f"Buy Tax: {token_data.get('buy_tax', 'N/A')}")
                file_logger.info(f"Sell Tax: {token_data.get('sell_tax', 'N/A')}")

                is_safe = security_score >= min_safety_score

                if is_safe:
                    logger.info(f"Token passed safety check with score: {security_score}%")
                    return is_safe, security_score

                return is_safe, security_score
            else:
                file_logger.info("Token security data not available. Retrying in 30 seconds.")
                retries += 1
                time.sleep(60)

        except Exception as e:
            file_logger.error(f"Request error: {str(e)}. Retrying.")
            retries += 1
            time.sleep(10)

    logger.error("Max retry limit hit; operation aborted. If this issue persists, please submit an issue request on GitHub.")
    return False, 0

def check_token_safety(tokentobuy, chain_id, min_safety_score):
    score = 'N/A'
    try:
        time.sleep(30)
        is_safety_valid, score = perform_safety_check(tokentobuy, chain_id, min_safety_score)

        if is_safety_valid:
            return True, score

        return False, score

    except Exception as e:
        logger.error(f"Error in check_token_safety: {e}")
        return False, score