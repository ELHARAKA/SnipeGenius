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

import time
from web3 import Web3
from config import factory_abi, pair_abi, wbnb_address, router, wbnb, w3, logger, file_logger
from coinOps import get_wbnb_balance
from snipegenius import check_token_safety

# Execute a buy transaction
def execute_buy(amount_out_min, pair_address, wbnb_address, router, wbnb, w3, wbnb_reserve):
    from config import private_key, my_address
    # Check numerical arguments are of type int
    if not all(isinstance(x, int) for x in [amount_out_min, wbnb_reserve]):
        raise ValueError("All numerical arguments must be of type int.")

    my_address = my_address.strip()
    pair_address = pair_address.strip()
    wbnb_address = wbnb_address.strip()

    # Check for double quotes in addresses
    for address in [my_address, pair_address, wbnb_address]:
        if '"' in address:
            error_message = f'Addresses should not contain double quotes: {address}'
            logger.error(error_message)
            raise ValueError(error_message)

    pair_contract = w3.eth.contract(address=pair_address, abi=pair_abi)

    # Get token addresses
    token0_address = pair_contract.functions.token0().call()
    token1_address = pair_contract.functions.token1().call()
    file_logger.info(f"Token 0 address: {token0_address}")
    file_logger.info(f"Token 1 address: {token1_address}")

    # Identify WBNB and the token to buy
    if token0_address.lower() == wbnb_address.lower():
        tokentobuy = token1_address
    elif token1_address.lower() == wbnb_address.lower():
        tokentobuy = token0_address
    else:
        logger.error("Neither of the tokens in the pair is WBNB. Aborting.")
        return

    chain_id = 56
    is_safe, score = check_token_safety(tokentobuy, chain_id, w3)
    if is_safe:
        logger.debug(f"Safe Token, score: {score}%. Proceeding.")
    else:
        logger.warning(f"Scam risk, score: {score}%. Aborting.")
        return

    file_logger.info(f"WBNB address: {wbnb_address}")
    file_logger.info(f"My address: {my_address}")
    file_logger.info(f"Router address: {router.address}")
    file_logger.info("Checking allowance.")

    percentage_for_allowance = 1.0  # 100%
    balance = w3.eth.get_balance(my_address)
    allowance_needed = int(balance * percentage_for_allowance)
    allowance = wbnb.functions.allowance(my_address, router.address).call()

    current_block = w3.eth.get_block('latest')['number']
    file_logger.info(f"Current block: {current_block}")

    if allowance < allowance_needed:
        current_nonce = w3.eth.get_transaction_count(my_address)
        file_logger.info(f"Current nonce: {current_nonce}")
        logger.info("Insufficient allowance. Approving more tokens...")

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
        file_logger.info("Approval transaction details:")
        file_logger.info(f"Nonce: {approve_txn['nonce']}")
        file_logger.info(f"Gas Price: {approve_txn['gasPrice']}")
        file_logger.info(f"Gas Limit: {approve_txn['gas']}")
        file_logger.info(f"To: {approve_txn['to']}")
        file_logger.info(f"Value: {approve_txn['value']}")
        file_logger.info(f"Data: {approve_txn['data']}")

        # You can send the transaction whenever you're ready
        w3.eth.send_raw_transaction(signed_approve_txn.rawTransaction)
        logger.info("Approval successful.")

    try:
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
        file_logger.info(f"Estimated gas price: {estimated_gas_price}")
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
            file_logger.info("Transaction occurred in the current block.")
        else:
            file_logger.warning("Block differed between the creation and execution of the transaction.")

        logger.info(
            f"Transaction successful with hash: {txn_hash.hex()}\n"
            f"Status: {txn_receipt.status}\n"
            f"Gas Used: {txn_receipt.gasUsed}"
        )

    except ValueError as e:
        if 'revert' in str(e):
            logger.error(f"Transaction reverted. Raw Error: {e}")
            tx = e.args[0]['transaction']
            receipt = w3.eth.getTransactionReceipt(tx)
            revert_reason = w3.toText(receipt['logs'][0]['data'])
            logger.error(f"Revert Reason: {revert_reason}")
        else:
            logger.error(f"Execution reverted, Check Log File")
            file_logger.error(f"Execution reverted: {e}")

    except Exception as e:
        logger.error(f"An error occurred, Check Log file")
        file_logger.error(f"An error occurred: {str(e)}")

# Extract the ABI for the PairCreated event from the factory ABI
pair_created_event_abi = [event_abi for event_abi in factory_abi if event_abi['type'] == 'event' and event_abi['name'] == 'PairCreated'][0]

# Check for LIQUIDITY and return reserves
def check_liquidity(pair_address, wbnb_address, w3):
    pair_contract = w3.eth.contract(address=pair_address, abi=pair_abi)
    reserves = pair_contract.functions.getReserves().call()
    reserve0, reserve1 = reserves[0], reserves[1]
    token0_address = pair_contract.functions.token0().call()
    token1_address = pair_contract.functions.token1().call()
    minimum_liquidity = Web3.to_wei(2, 'ether')

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

# Handle events and Execute Buy
def handle_event(event, percentage_for_amount_in):
    try:
        decoded_data = w3.eth.contract(abi=[pair_created_event_abi]).events.PairCreated().process_log(event)
        pair_address = decoded_data['args']['pair']
        pair_address = Web3.to_checksum_address(pair_address.strip())

        liquidity_status, wbnb_reserve = check_liquidity(pair_address, wbnb_address, w3)

        if wbnb_reserve is None:
            file_logger.info(f"Insufficient WBNB Reserve for {pair_address}")
            return

        wbnb_reserve = int(wbnb_reserve)
        balance = get_wbnb_balance()
        human_readable_balance = Web3.from_wei(balance, 'ether')
        file_logger.info(f"Your Wallet Balance: {human_readable_balance} WBNB")

        if liquidity_status:
            amount_in = int(balance * percentage_for_amount_in)
            acceptable_slippage = 0.05
            amount_out_min = int(amount_in * (1 - acceptable_slippage))
            logger.info(f"New Pair Address: {pair_address}")
            execute_buy(amount_out_min, pair_address, wbnb_address, router, wbnb, w3, wbnb_reserve)
        else:
            logger.info(f"Insufficient liquidity. Checking for new Tokens")
    except Exception as e:
        logger.error(f"Error processing event, please check Log File")
        file_logger.error(f"Error processing event: {e}")
