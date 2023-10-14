# SnipeGenius 🥞 (PancakeSwap)
# Version: 1.0.1
# Developed by Fahd El Haraka ©
# Email: fahd@web3dev.ma
# Telegram: @thisiswhosthis
# Website: https://web3dev.ma
# GitHub: https://github.com/ELHARAKA

"""
© Copyright 2023
Proprietary Software by Fahd El Haraka, 2023. Unauthorized use, duplication, modification, or distribution is strictly prohibited. Contact fahd@web3dev.ma for permissions and inquiries.
"""

from config import factory_abi, pair_abi, wbnb_address, router, wbnb, private_key, my_address, w3
from api import get_wbnb_balance
from imports import time, logging, sys
from web3 import Web3
from datetime import datetime
from snipegenius import check_token_safety

# Execute a buy transaction
def execute_buy(my_address, amount_out_min, pair_address, wbnb_address, router, wbnb, private_key, w3, wbnb_reserve):
    # Check numerical arguments are of type int
    if not all(isinstance(x, int) for x in [amount_out_min, wbnb_reserve]):
        raise ValueError("All numerical arguments must be of type int.")

    # Remove leading and trailing spaces from addresses
    #my_address = my_address.strip()
    pair_address = pair_address.strip()
    wbnb_address = wbnb_address.strip()

    # Check for double quotes in addresses
    for address in [my_address, pair_address, wbnb_address]:
        if '"' in address:
            raise ValueError('Addresses should not contain double quotes.')

    pair_contract = w3.eth.contract(address=pair_address, abi=pair_abi)

    # Get token addresses
    token0_address = pair_contract.functions.token0().call()
    token1_address = pair_contract.functions.token1().call()

    # Log the retrieved token addresses
    logging.info(f"Token 0 address: {token0_address}")
    logging.info(f"Token 1 address: {token1_address}")

    # Identify WBNB and the token to buy
    if token0_address.lower() == wbnb_address.lower():
        tokentobuy = token1_address
    elif token1_address.lower() == wbnb_address.lower():
        tokentobuy = token0_address
    else:
        logging.error("Neither of the tokens in the pair is WBNB. Aborting.")
        return

    chain_id = 56  # BSC Chain ID
    is_safe = check_token_safety(tokentobuy, pair_address, chain_id, my_address, private_key, w3, router, wbnb)
    if is_safe is not None:
        if is_safe:
            logging.info("Token is considered safe. Proceeding.")
        else:
            logging.warning("Token is not considered safe. Aborting.")
            return
    else:
        logging.warning("Could not determine the safety of the token. Aborting.")
        return

    logging.info(f"WBNB address: {wbnb_address}")
    logging.info(f"My address: {my_address}")
    logging.info(f"Router address: {router.address}")
    logging.info("Checking allowance.")

    percentage_for_allowance = 0.02
    balance = w3.eth.get_balance(my_address)
    allowance_needed = int(balance * percentage_for_allowance)
    allowance = wbnb.functions.allowance(my_address, router.address).call()

    current_block = w3.eth.get_block('latest')['number']
    logging.info(f"Current block: {current_block}")

    if allowance < allowance_needed:
        current_nonce = w3.eth.get_transaction_count(my_address)
        logging.info(f"Current nonce: {current_nonce}")
        logging.info("Insufficient allowance. Approving more tokens before proceeding.")

        gas_estimate = wbnb.functions.approve(router.address, allowance_needed).estimate_gas({
            'from': my_address,
        })
        
        estimated_gas_price = w3.eth.gas_price  # Only work for Web3.py v5.0.0-beta.0 onwards
        approve_txn = wbnb.functions.approve(router.address, allowance_needed).build_transaction({
            'from': my_address,
            'gas': gas_estimate,
            'gasPrice': estimated_gas_price,
            'nonce': w3.eth.get_transaction_count(my_address),
            'chainId': 56
        })

        signed_approve_txn = w3.eth.account.sign_transaction(approve_txn, private_key)

         # Inspect the transaction object
        logging.info("Approval transaction details:")
        logging.info(f"Nonce: {approve_txn['nonce']}")
        logging.info(f"Gas Price: {approve_txn['gasPrice']}")
        logging.info(f"Gas Limit: {approve_txn['gas']}")
        logging.info(f"To: {approve_txn['to']}")
        logging.info(f"Value: {approve_txn['value']}")
        logging.info(f"Data: {approve_txn['data']}")

        # You can send the transaction whenever you're ready
        w3.eth.send_raw_transaction(signed_approve_txn.rawTransaction)
        logging.info("Approval successful.")

    try:
        # Estimate gas for the swap transaction
        gas_estimate_swap = router.functions.swapExactTokensForTokensSupportingFeeOnTransferTokens(
            allowance_needed,
            amount_out_min,
            [wbnb_address, tokentobuy],
            my_address,
            int(time.time()) + 120
        ).estimate_gas({'from': my_address})

        logging.info(f"Estimated gas cost for the swap transaction: {gas_estimate_swap}")

        # Perform a dry run of the swap transaction to get results
        dry_run_result = router.functions.swapExactTokensForTokensSupportingFeeOnTransferTokens(
            allowance_needed,
            amount_out_min,
            [wbnb_address, tokentobuy],
            my_address,
            int(time.time()) + 120
        ).call({'from': my_address})

        logging.info(f"Dry run result: {dry_run_result}")

        # Estimate gas for the swap transaction
        gas_estimate = router.functions.swapExactTokensForTokensSupportingFeeOnTransferTokens(
            allowance_needed,
            amount_out_min,
            [wbnb_address, tokentobuy],
            my_address,
            int(time.time()) + 120
        ).estimate_gas({'from': my_address})

        # Build the transaction with the estimated gas
        estimated_gas_price = w3.eth.gas_price  # Only work for Web3.py v5.0.0-beta.0 onwards
        logging.info(f"Estimated gas price: {estimated_gas_price}")
        txn = {
            'from': my_address,
            'gas': gas_estimate,
            'gasPrice': estimated_gas_price,
            'nonce': w3.eth.get_transaction_count(my_address),
            'chainId': 56
        }

        # Build the swap transaction
        swap_txn = router.functions.swapExactTokensForTokensSupportingFeeOnTransferTokens(
            allowance_needed,
            amount_out_min,
            [wbnb_address, tokentobuy],
            my_address,
            int(time.time()) + 120
        ).build_transaction(txn)

        # Sign the transaction
        signed_swap_txn = w3.eth.account.sign_transaction(swap_txn, private_key)

        # Send the raw transaction
        txn_hash = w3.eth.send_raw_transaction(signed_swap_txn.rawTransaction)

        txn_receipt = w3.eth.wait_for_transaction_receipt(txn_hash)

        if current_block == txn_receipt['blockNumber']:
            logging.info("Dry run and actual transaction occurred in the same block.")
        else:
            logging.warning("Blocks differed between dry run and actual transaction.")

        logging.info(f"Transaction successful with hash: {txn_hash.hex()}")
        logging.info(f"Transaction Status: {txn_receipt.status}, Gas Used: {txn_receipt.gasUsed}")

    except ValueError as e:
        if 'revert' in str(e):
            # Decode the revert reason if it's an EVM revert
            logging.error(f"Transaction reverted. Raw Error: {e}")
            tx = e.args[0]['transaction']
            receipt = w3.eth.getTransactionReceipt(tx)
            revert_reason = w3.toText(receipt['logs'][0]['data'])
            logging.error(f"Revert Reason: {revert_reason}")
        else:
            logging.error(f"Execution reverted: {e}")

    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")

# Extract the ABI for the PairCreated event from the factory ABI
pair_created_event_abi = [event_abi for event_abi in factory_abi if event_abi['type'] == 'event' and event_abi['name'] == 'PairCreated'][0]

# Check for SUFFICIENT LIQUIDITY and return reserves
def check_liquidity(pair_address, wbnb_address, w3):
    pair_contract = w3.eth.contract(address=pair_address, abi=pair_abi)
    reserves = pair_contract.functions.getReserves().call()
    reserve0, reserve1 = reserves[0], reserves[1]
    token0_address = pair_contract.functions.token0().call()
    token1_address = pair_contract.functions.token1().call()
    minimum_liquidity = Web3.to_wei(5, 'ether')

    wbnb_reserve = None

    if token0_address.lower() == wbnb_address.lower():
        if reserve0 >= minimum_liquidity:
            wbnb_reserve = reserve0
    elif token1_address.lower() == wbnb_address.lower():
        if reserve1 >= minimum_liquidity:
            wbnb_reserve = reserve1

    if wbnb_reserve is not None:
        return True, wbnb_reserve
    else:
        return False, wbnb_reserve

# Handle events and execute buys
def handle_event(event):

    # Remove leading and trailing spaces from pair_address
    decoded_data = w3.eth.contract(abi=[pair_created_event_abi]).events.PairCreated().process_log(event)
    pair_address = decoded_data['args']['pair']
    pair_address = Web3.to_checksum_address(pair_address.strip())

    # Check for double quotes in pair_address
    if '"' in pair_address:
        raise ValueError('pair_address should not contain double quotes.')

    logging.info(f"Extracted pair address: {pair_address}")

    retries = 0
    max_retries = 3

    while retries < max_retries:
        liquidity_status, wbnb_reserve = check_liquidity(pair_address, wbnb_address, w3)

        if wbnb_reserve is None:
            current_time = datetime.now().strftime('[%Y-%m-%d %H:%M:%S]')
            for i in range(30, 0, -1):
                sys.stdout.write(f"\r{current_time} WBNB Reserve is 0 Retrying in {i} sec" + ' ' * 1)
                sys.stdout.flush()
                time.sleep(1)
            retries += 1
            print()
            continue

        wbnb_reserve = int(wbnb_reserve)
        percentage_for_amount_in = 0.01  # Adjust this percentage as needed
        balance = get_wbnb_balance(wbnb_address, my_address)
        logging.info(f"Your Wallet Balance: {balance } WBNB")

        if liquidity_status:
            amount_in = int(balance * percentage_for_amount_in)
            acceptable_slippage = 0.03
            amount_out_min = int(amount_in * (1 - acceptable_slippage))

            logging.info(f"Sufficient (WBNB) liquidity found, performing some safety checks then executing buy.")
            execute_buy(my_address, amount_out_min, pair_address, wbnb_address, router, wbnb, private_key, w3, wbnb_reserve)
            return
        else:
            logging.info(f"Insufficient (WBNB) liquidity, retrying in 30 seconds.")
            retries += 1
            time.sleep(30)

    if retries >= max_retries:
        print(f"{datetime.now().strftime('[%Y-%m-%d %H:%M:%S]')} No (WBNB) liquidity found after 3 attempts. Checking for more events...")