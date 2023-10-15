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

from imports import *
from api import get_token_abi, get_token_balance

def is_blacklisted(tokentobuy, w3):
    token_abi = get_token_abi(tokentobuy)
    token_contract = w3.eth.contract(address=tokentobuy, abi=token_abi)
    owner_address = token_contract.functions.owner().call()

    with open('blacklist.txt', 'r') as file:
        blacklist = file.read().splitlines()

    return owner_address.lower() in blacklist

def perform_safety_check(tokentobuy, pair_address, chain_id):
    honeypot_url = (
        f"https://api.honeypot.is/v2/IsHoneypot?address={tokentobuy}"
        f"&pair={pair_address}&chainID={chain_id}"
    )
    goplus_url = (
        f"https://api.gopluslabs.io/api/v1/token_security/56?"
        f"contract_addresses={tokentobuy}"
    )

    safety_checks = {
        'anti_whale_modifiable': '0',
        'buy_tax': '0',
        'can_take_back_ownership': '0',
        'cannot_buy': '0',
        'cannot_sell_all': '0',
        'creator_percent': lambda x: float(x) < 5.0,
        'external_call': '0',
        'hidden_owner': '0',
        'honeypot_with_same_creator': '0',
        'is_anti_whale': '0',
        'is_blacklisted': '0',
        'is_honeypot': '0',
        'is_mintable': '0',
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

        safety_checks['is_honeypot'] = honeypot_data.get('honeypotResult', {}).get(tokentobuy.lower(), {}).get('isHoneypot', '0')

        goplus_response = requests.get(goplus_url)
        goplus_response.raise_for_status()
        goplus_data = json.loads(goplus_response.text)

        token_data = goplus_data.get('result', {}).get(tokentobuy.lower(), {})

        for key, expected_value in safety_checks.items():
            actual_value = token_data.get(key, 'N/A')
            if callable(expected_value):  # handle special case for creator_percent
                try:
                    float_actual_value = float(actual_value)  # Attempt to convert actual_value to float
                except ValueError:
                    logging.warning(f"Check failed for {key}: {actual_value}")
                    continue  # Skip to the next iteration if conversion fails
                if expected_value(float_actual_value):  # Pass the float value to expected_value
                    passed_checks += 1
            elif actual_value == expected_value:
                passed_checks += 1
            else:
                logging.warning(f"Check failed for {key}: {actual_value}")

    except requests.exceptions.RequestException as e:
        logging.error(f"Request error: {e}")

    except json.JSONDecodeError as e:
        logging.error(f"JSON decoding error: {e}")

    return passed_checks == total_checks  # Return True if safety rate is 90% or higher, False otherwise

# Simulate Transactions to inspect any issues during buy/sell
def simulate_transactions(my_address, tokentobuy, router, wbnb, private_key, w3):
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
        logging.error('Buy simulation failed.')
        return False  # Simulation failed at buy step
    else:
        logging.info(f"Buy Simulation Passed: TX HASH {buy_txn_hash.hex()}")
    
    time.sleep(15)  # Wait for TX to get confirmed
    
    token_balance = get_token_balance(tokentobuy, my_address) # Get Token Balance
    if token_balance == 0:
        logging.error('Balance is Zero')
        return False 
    else:
        logging.info(f'Token balance = {token_balance}')

    # Simulate Approve
    token_abi = get_token_abi(tokentobuy)
    token_contract = w3.eth.contract(address=tokentobuy, abi=token_abi)
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
        logging.info('Approval Simulation successful.')
    else:
        logging.error('Approval Simulation failed.')
    
    time.sleep(15) # Wait for TX to get confirmed

    # Simulate Sell
    sell_txn = router.functions.swapExactTokensForETHSupportingFeeOnTransferTokens(
        token_balance,
        0,  # set to 0 to accept any amount of ETH
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

    time.sleep(15) # Wait for Simulate Sell TX to get confirmed

    if sell_txn_receipt.status != 1:
        logging.error('Sell Simulation Failed, Run the fuck away.')
        return False 
    else:
        logging.info(f"Sell Simulation Passed: TX HASH {sell_txn_hash.hex()}")

def check_token_safety(tokentobuy, pair_address, chain_id, my_address, private_key, w3, router, wbnb):
    time.sleep(30)  # Wait for 30 seconds before the first check
    first_check = perform_safety_check(tokentobuy, pair_address, chain_id)

    if first_check:
        simulation_result = simulate_transactions(my_address, tokentobuy, router, wbnb, private_key, w3)
        return simulation_result

    return False
