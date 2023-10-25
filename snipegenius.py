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

import json
import time
import requests
from googleapiclient.discovery import build
from coinOps import get_token_balance
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

def perform_safety_check(tokentobuy, pair_address, chain_id):
    honeypot_url = f"https://api.honeypot.is/v2/IsHoneypot?address={tokentobuy}&pair={pair_address}&chainID={chain_id}"

    safety_checks = {
        'anti_whale_modifiable': '0',
        'buy_tax': '0',
        'can_take_back_ownership': '0',
        'cannot_buy': '0',
        'cannot_sell_all': '0',
        'creator_percent': lambda x: float(x) < 5.0,
        'hidden_owner': '0',
        'honeypot_with_same_creator': '0',
        'is_anti_whale': '0',
        'is_blacklisted': '0',
        'is_honeypot': '0',
        'is_open_source': '1',
        'is_proxy': '0',
        'is_whitelisted': '0',
        'personal_slippage_modifiable': '0',
        'selfdestruct': '0',
        'sell_tax': '0',
        'slippage_modifiable': '0',
        'trading_cooldown': '0',
        'transfer_pausable': '0',
    }

    total_checks = len(safety_checks)
    passed_checks = 0

    try:
        honeypot_response = requests.get(honeypot_url)
        honeypot_response.raise_for_status()
        honeypot_data = json.loads(honeypot_response.text)

        token_data = honeypot_data.get('honeypotResult', {}).get(tokentobuy.lower(), {})

        for key, expected_value in safety_checks.items():
            actual_value = token_data.get(key, 'N/A')
            if callable(expected_value):
                try:
                    float_actual_value = float(actual_value)
                except ValueError:
                    file_logger.debug(f"Check failed for {key}: {actual_value}")
                    continue
                if expected_value(float_actual_value):
                    passed_checks += 1
            elif actual_value == expected_value:
                passed_checks += 1
            else:
                file_logger.debug(f"Check failed for {key}: {actual_value}")

    except requests.exceptions.RequestException as e:
        file_logger.error(f"Request error: {e}")

    except json.JSONDecodeError as e:
        file_logger.error(f"JSON decoding error: {e}")

    return passed_checks == total_checks


def google_search(tokentobuy):
    from config import google_api_key, google_cse_id
    service = build("customsearch", "v1", developerKey=google_api_key)
    results = service.cse().list(q=f'"{tokentobuy}"', cx=google_cse_id).execute()
    return int(results['searchInformation']['totalResults'])

def check_google_results(tokentobuy):
    num_results = google_search(tokentobuy)
    return num_results >= 1

# Simulate Transactions to inspect any issues during buy/sell
def simulate_transactions(tokentobuy, router, wbnb, w3):
    from config import private_key, my_address
    amount_to_buy = w3.to_wei('0.00001', 'ether')  # 0.00001 WBNB in Wei

    # Simulate Buy
    buy_txn = router.functions.swapExactETHForTokens(
        0,  # set to 0 to accept any amount of tokens
        [wbnb.address, tokentobuy],
        my_address,
        int(time.time()) + 120
    ).build_transaction({
        'from': my_address,
        'value': amount_to_buy,
        'gas': 250000,
        'gasPrice': w3.eth.gas_price,
        'nonce': w3.eth.get_transaction_count(my_address),
        'chainId': 56
    })

    signed_buy_txn = w3.eth.account.sign_transaction(buy_txn, private_key)
    buy_txn_hash = w3.eth.send_raw_transaction(signed_buy_txn.rawTransaction)
    buy_txn_receipt = w3.eth.wait_for_transaction_receipt(buy_txn_hash)

    if buy_txn_receipt.status != 1:
        file_logger.error(f"Buy simulation failed. TX HASH {buy_txn_hash.hex()}")
        return False
    else:
        file_logger.info(f"Buy Simulation Passed: TX HASH {buy_txn_hash.hex()}")

    time.sleep(15)  # Wait for TX to get confirmed

    token_balance = get_token_balance(tokentobuy) # Get Token Balance
    if token_balance == 0:
        logger.error('Balance is Zero')
        return False
    else:
        file_logger.info(f'Token balance = {token_balance}')

    # Simulate Approve
    token_contract = w3.eth.contract(address=tokentobuy, abi=[{
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    }])
    approve_txn = token_contract.functions.approve(router.address, token_balance).build_transaction({
        'from': my_address,
        'gas': 100000,
        'gasPrice': w3.eth.gas_price,
        'nonce': w3.eth.get_transaction_count(my_address),
        'chainId': 56
    })
    signed_approve_txn = w3.eth.account.sign_transaction(approve_txn, private_key)
    approve_txn_hash = w3.eth.send_raw_transaction(signed_approve_txn.rawTransaction)
    w3.eth.wait_for_transaction_receipt(approve_txn_hash)
    approve_txn_receipt = w3.eth.wait_for_transaction_receipt(approve_txn_hash)
    if approve_txn_receipt.status == 1:
        file_logger.info('Approval Simulation successful.')
    else:
        file_logger.error('Approval Simulation failed.')

    time.sleep(15)

    sell_txn = router.functions.swapExactTokensForETHSupportingFeeOnTransferTokens(
        token_balance,
        0,  # set to 0 to accept any amount of WBNB
        [tokentobuy, wbnb.address],
        my_address,
        int(time.time()) + 120
    ).build_transaction({
        'from': my_address,
        'gas': 250000,
        'gasPrice': w3.eth.gas_price,
        'nonce': w3.eth.get_transaction_count(my_address),
        'chainId': 56
    })

    signed_sell_txn = w3.eth.account.sign_transaction(sell_txn, private_key)
    sell_txn_hash = w3.eth.send_raw_transaction(signed_sell_txn.rawTransaction)
    sell_txn_receipt = w3.eth.wait_for_transaction_receipt(sell_txn_hash)

    time.sleep(15)

    if sell_txn_receipt.status != 1:
        file_logger.error(f"Sell Simulation Failed, TX hash: {sell_txn_hash.hex()} and Run the fuck away.")
        return False
    else:
        file_logger.info(f"Sell Simulation Passed: TX HASH {sell_txn_hash.hex()}")

def check_token_safety(tokentobuy, pair_address, chain_id, w3, router, wbnb):
    try:
        time.sleep(15)
        is_safety_valid = perform_safety_check(tokentobuy, pair_address, chain_id)

        if is_safety_valid:
            google_safe = check_google_results(tokentobuy)

            if google_safe:
                simulation_result = simulate_transactions(tokentobuy, router, wbnb, w3)
                return bool(simulation_result)

        return False

    except Exception as e:
        return False
