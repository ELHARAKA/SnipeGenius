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
from config import *
from snipegenius import check_token_safety
from exit_strategy import intelligent_adaptive_liquidation

def get_and_increment_nonce(w3, address):
    """Get current nonce and increment it for next transaction"""
    nonce = w3.eth.get_transaction_count(address)
    file_logger.info(f"Current nonce: {nonce}")
    return nonce

def execute_buy(amount_out_min, pair_address, wbnb_address, router, wbnb, w3, wbnb_reserve, min_safety_score, amount_in):
    from config import private_key, my_address
    import sys

    if 'balance_manager' in sys.modules and 'balance_manager' in globals():
        try:
            from snipe import balance_manager
            if balance_manager is not None and not balance_manager.can_purchase():
                logger.warning("Purchase skipped: Balance below minimum threshold")
                file_logger.warning(f"Purchase skipped for pair {pair_address}: Balance below minimum threshold")
                return
        except Exception as e:
            file_logger.error(f"Error checking balance manager: {str(e)}")
    if not all(isinstance(x, int) for x in [amount_out_min, wbnb_reserve]):
        raise ValueError("All numerical arguments must be of type int.")

    my_address = my_address.strip()
    pair_address = pair_address.strip()
    wbnb_address = wbnb_address.strip()

    for address in [my_address, pair_address, wbnb_address]:
        if '"' in address:
            error_message = f'Addresses should not contain double quotes: {address}'
            logger.error(error_message)
            raise ValueError(error_message)

    pair_contract = w3.eth.contract(address=pair_address, abi=pair_abi)
    token0_address = pair_contract.functions.token0().call()
    token1_address = pair_contract.functions.token1().call()
    file_logger.info(f"Token 0 address: {token0_address}")
    file_logger.info(f"Token 1 address: {token1_address}")

    if token0_address.lower() == wbnb_address.lower():
        tokentobuy = token1_address
    elif token1_address.lower() == wbnb_address.lower():
        tokentobuy = token0_address
    else:
        logger.error("Neither of the tokens in the pair is WBNB. Aborting.")
        return

    chain_id = 56
    is_safe, score = check_token_safety(tokentobuy, chain_id, min_safety_score)
    if is_safe:
        logger.debug(f"Safe Token, score: {score}%. Proceeding.")
    else:
        logger.warning(f"Scam risk, score: {score}%. Aborting.")
        return

    file_logger.info(f"WBNB address: {wbnb_address}")
    file_logger.info(f"My address: {my_address}")
    file_logger.info(f"Router address: {router.address}")

    # Get WBNB balance instead of native BNB balance
    from coinOps import get_wbnb_balance, ensure_wbnb_balance
    wbnb_balance = get_wbnb_balance()
    human_readable_wbnb = Web3.from_wei(wbnb_balance, 'ether')
    file_logger.info(f"WBNB balance: {human_readable_wbnb} WBNB")

    # Use the pre-calculated amount_in directly
    allowance_needed = amount_in

    # Ensure we have enough WBNB tokens
    if allowance_needed > 0:
        file_logger.info(f"Amount needed for swap: {Web3.from_wei(allowance_needed, 'ether')} WBNB")
        if not ensure_wbnb_balance(allowance_needed):
            logger.error("Insufficient WBNB balance for swap. Please convert BNB to WBNB first.")
            return
    else:
        logger.error("Amount to swap is zero. Check your wallet balance and percentage settings.")
        return

    file_logger.info("Checking allowance.")
    allowance = wbnb.functions.allowance(my_address, router.address).call()

    current_block = w3.eth.get_block('latest')['number']
    file_logger.info(f"Current block: {current_block}")

    if allowance < allowance_needed:
        nonce = get_and_increment_nonce(w3, my_address)
        logger.info("Insufficient allowance. Approving more tokens...")

        gas_estimate = wbnb.functions.approve(router.address, allowance_needed).estimate_gas({
            'from': my_address,
        })

        estimated_gas_price = w3.eth.gas_price
        approve_txn = wbnb.functions.approve(router.address, allowance_needed).build_transaction({
            'from': my_address,
            'gas': gas_estimate,
            'gasPrice': estimated_gas_price,
            'nonce': nonce,
            'chainId': 56
        })

        signed_approve_txn = w3.eth.account.sign_transaction(approve_txn, private_key)

        file_logger.info("Approval transaction details:")
        file_logger.info(f"Nonce: {approve_txn['nonce']}")
        file_logger.info(f"Gas Price: {approve_txn['gasPrice']}")
        file_logger.info(f"Gas Limit: {approve_txn['gas']}")
        file_logger.info(f"To: {approve_txn['to']}")
        file_logger.info(f"Value: {approve_txn['value']}")
        file_logger.info(f"Data: {approve_txn['data']}")

        txn_hash = w3.eth.send_raw_transaction(signed_approve_txn.raw_transaction)
        logger.info(f"Approval successful. Hash: {txn_hash.hex()}")
        # Wait for approval to complete before proceeding
        time.sleep(5)

    try:
        # Get token info for better diagnostics
        from coinOps import get_token_info
        token_info = get_token_info(tokentobuy)
        file_logger.info(f"Token info: Name: {token_info['name']}, Symbol: {token_info['symbol']}, Decimals: {token_info['decimals']}")

        # Double-check WBNB balance before proceeding
        from coinOps import get_wbnb_balance
        current_wbnb_balance = get_wbnb_balance()
        if current_wbnb_balance < allowance_needed:
            logger.error(f"Insufficient WBNB balance. Need {Web3.from_wei(allowance_needed, 'ether')} WBNB but only have {Web3.from_wei(current_wbnb_balance, 'ether')} WBNB")
            return

        # Log the swap details
        file_logger.info(f"Attempting to swap {Web3.from_wei(allowance_needed, 'ether')} WBNB for {token_info['symbol']} tokens")
        file_logger.info(f"Minimum amount out: {Web3.from_wei(amount_out_min, 'ether') * (10 ** (18 - token_info['decimals']))} {token_info['symbol']}")

        try:
            gas_estimate = router.functions.swapExactTokensForTokensSupportingFeeOnTransferTokens(
                allowance_needed,
                amount_out_min,
                [wbnb_address, tokentobuy],
                my_address,
                int(time.time()) + 120
            ).estimate_gas({'from': my_address})

            file_logger.info(f"Gas estimate successful: {gas_estimate}")
        except Exception as gas_error:
            logger.error(f"Gas estimation failed: {str(gas_error)}")
            file_logger.error(f"Gas estimation failed: {str(gas_error)}")

            # Try with higher gas limit as fallback
            gas_estimate = 500000
            file_logger.info(f"Using fallback gas limit: {gas_estimate}")

        estimated_gas_price = w3.eth.gas_price
        file_logger.info(f"Estimated gas price: {estimated_gas_price}")
        # Get fresh nonce after approval delay
        nonce = get_and_increment_nonce(w3, my_address)
        txn = {
            'from': my_address,
            'gas': gas_estimate,
            'gasPrice': estimated_gas_price,
            'nonce': nonce,
            'chainId': 56
        }

        swap_txn = router.functions.swapExactTokensForTokensSupportingFeeOnTransferTokens(
            allowance_needed,
            amount_out_min,
            [wbnb_address, tokentobuy],
            my_address,
            int(time.time()) + 120
        ).build_transaction(txn)

        file_logger.info(f"Swap transaction built successfully")
        file_logger.info(f"Transaction details: Gas: {swap_txn['gas']}, Gas Price: {swap_txn['gasPrice']}, Nonce: {swap_txn['nonce']}")

        # Retry logic for nonce issues
        for attempt in range(3):
            try:
                signed_swap_txn = w3.eth.account.sign_transaction(swap_txn, private_key)
                file_logger.info(f"Transaction signed successfully")

                txn_hash = w3.eth.send_raw_transaction(signed_swap_txn.raw_transaction)
                file_logger.info(f"Transaction sent with hash: {txn_hash.hex()}")

                logger.info(f"Waiting for transaction receipt...")
                txn_receipt = w3.eth.wait_for_transaction_receipt(txn_hash)

                if current_block == txn_receipt['blockNumber']:
                    file_logger.info("Transaction occurred in the current block.")
                else:
                    file_logger.warning("Block differed between the creation and execution of the transaction.")

                if txn_receipt.status == 1:
                    logger.info(
                        f"Transaction successful with hash: {txn_hash.hex()}\n"
                        f"Status: {txn_receipt.status}\n"
                        f"Gas Used: {txn_receipt.gasUsed}"
                    )
                    break  # Exit the retry loop if successful
            except Exception as e:
                logger.error(f"Error sending transaction: {str(e)}")
                file_logger.error(f"Error sending transaction: {str(e)}")
                if 'nonce too low' in str(e) or 'replacement transaction underpriced' in str(e):
                    logger.warning("Nonce issue detected, updating nonce...")
                    # Get fresh nonce and retry
                    nonce = get_and_increment_nonce(w3, my_address)
                    swap_txn['nonce'] = nonce
                else:
                    raise  # Reraise if it's not a nonce issue

            # Check token balance after swap
            token_contract = w3.eth.contract(address=tokentobuy, abi=token_abi)
            token_balance = token_contract.functions.balanceOf(my_address).call()

            if token_balance > 0:
                human_readable_balance = token_balance / (10 ** token_info['decimals'])
                logger.info(f"Successfully purchased {human_readable_balance} {token_info['symbol']} tokens")
                file_logger.info(f"Successfully purchased {human_readable_balance} {token_info['symbol']} tokens")

                buy_price = allowance_needed / token_balance

                import sys
                if 'token_monitor_manager' in sys.modules and 'token_monitor_manager' in globals():
                    try:
                        from snipe import token_monitor_manager
                        if token_monitor_manager is not None:
                            token_monitor_manager.add_token(tokentobuy, buy_price, token_balance)
                        else:
                            intelligent_adaptive_liquidation(tokentobuy, buy_price, token_balance)
                    except Exception as e:
                        file_logger.error(f"Error adding token to monitor: {str(e)}")
                        intelligent_adaptive_liquidation(tokentobuy, buy_price, token_balance)
                else:
                    intelligent_adaptive_liquidation(tokentobuy, buy_price, token_balance)
            else:
                logger.warning(f"Transaction succeeded but no tokens were received")
                file_logger.warning(f"Transaction succeeded but no tokens were received. This could be due to high fees or other token mechanics.")
        else:
            logger.error(f"Transaction failed with status: {txn_receipt.status}")
            file_logger.error(f"Transaction failed with status: {txn_receipt.status}")

    except ValueError as e:
        if 'revert' in str(e):
            logger.error(f"Transaction reverted. Raw Error: {e}")
            file_logger.error(f"Transaction reverted. Raw Error: {e}")

            try:
                tx = e.args[0]['transaction']
                receipt = w3.eth.get_transaction_receipt(tx)
                if receipt and 'logs' in receipt and len(receipt['logs']) > 0:
                    revert_reason = w3.to_text(receipt['logs'][0]['data'])
                    logger.error(f"Revert Reason: {revert_reason}")
                    file_logger.error(f"Revert Reason: {revert_reason}")
                else:
                    logger.error("Could not extract revert reason from receipt")
                    file_logger.error("Could not extract revert reason from receipt")
            except Exception as receipt_error:
                logger.error(f"Error extracting revert reason: {str(receipt_error)}")
                file_logger.error(f"Error extracting revert reason: {str(receipt_error)}")

            # Check if this is a TRANSFER_FROM_FAILED error
            if "TRANSFER_FROM_FAILED" in str(e):
                logger.error("TRANSFER_FROM_FAILED error detected. This usually means you don't have enough WBNB tokens.")
                file_logger.error("TRANSFER_FROM_FAILED error detected. This usually means you don't have enough WBNB tokens.")

                # Check BNB and WBNB balances
                from coinOps import get_bnb_balance, get_wbnb_balance
                bnb_balance = get_bnb_balance()
                wbnb_balance = get_wbnb_balance()

                logger.info(f"Current BNB balance: {Web3.from_wei(bnb_balance, 'ether')} BNB")
                logger.info(f"Current WBNB balance: {Web3.from_wei(wbnb_balance, 'ether')} WBNB")
                file_logger.info(f"Current BNB balance: {Web3.from_wei(bnb_balance, 'ether')} BNB")
                file_logger.info(f"Current WBNB balance: {Web3.from_wei(wbnb_balance, 'ether')} WBNB")

                if bnb_balance > Web3.to_wei(0.01, 'ether') and wbnb_balance < allowance_needed:
                    logger.info("You have BNB but not enough WBNB. Try converting BNB to WBNB first.")
                    file_logger.info("You have BNB but not enough WBNB. Try converting BNB to WBNB first.")
        else:
            logger.error(f"Execution reverted, Check Log File")
            file_logger.error(f"Execution reverted: {e}")

    except Exception as e:
        logger.error(f"An error occurred, Check Log file")
        file_logger.error(f"An error occurred: {str(e)}")

pair_created_event_abi = [event_abi for event_abi in factory_abi if event_abi['type'] == 'event' and event_abi['name'] == 'PairCreated'][0]

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

def handle_event(event, percentage_for_amount_in, min_safety_score):
    try:
        # Check if we're paused due to low balance
        import sys
        if 'balance_manager' in sys.modules and 'balance_manager' in globals():
            try:
                from snipe import balance_manager
                if balance_manager is not None and not balance_manager.can_purchase():
                    file_logger.info("Skipping event processing: Balance below minimum threshold")
                    return
            except Exception as e:
                file_logger.error(f"Error checking balance manager: {str(e)}")

        decoded_data = w3.eth.contract(abi=[pair_created_event_abi]).events.PairCreated().process_log(event)
        pair_address = decoded_data['args']['pair']
        pair_address = Web3.to_checksum_address(pair_address.strip())

        liquidity_status, wbnb_reserve = check_liquidity(pair_address, wbnb_address, w3)

        if wbnb_reserve is None:
            file_logger.info(f"Insufficient WBNB Reserve for {pair_address}")
            return

        wbnb_reserve = int(wbnb_reserve)

        # Get both BNB and WBNB balances
        import sys
        from coinOps import get_wbnb_balance, get_bnb_balance

        # Use balance manager if available
        if 'balance_manager' in sys.modules and 'balance_manager' in globals():
            try:
                from snipe import balance_manager
                if balance_manager is not None:
                    balance = balance_manager.get_balance()
                else:
                    balance = get_wbnb_balance()
            except Exception as e:
                file_logger.error(f"Error getting balance from manager: {str(e)}")
                balance = get_wbnb_balance()
        else:
            balance = get_wbnb_balance()

        # Display both balances for clarity
        wbnb_balance = get_wbnb_balance()
        bnb_balance = get_bnb_balance()
        human_readable_wbnb = Web3.from_wei(wbnb_balance, 'ether')
        human_readable_bnb = Web3.from_wei(bnb_balance, 'ether')
        file_logger.info(f"Your Wallet WBNB Balance: {human_readable_wbnb} WBNB")
        file_logger.info(f"Your Wallet BNB Balance: {human_readable_bnb} BNB")

        if liquidity_status:
            amount_in = int(balance * percentage_for_amount_in)
            slippage_levels = [0.07, 0.12, 0.20]

            for slippage in slippage_levels:
                try:
                    amount_out_min = int(amount_in * (1 - slippage))
                    logger.info(f"Setting slippage to {slippage * 100}%")
                    execute_buy(amount_out_min, pair_address, wbnb_address, router, wbnb, w3, wbnb_reserve, min_safety_score, amount_in)
                    break
                except Exception as e:
                    logger.error(f"Failed with slippage {slippage * 100}%. Retrying... Error: {e}")

        else:
            logger.info(f"Insufficient liquidity. Checking for new Tokens")
    except Exception as e:
        logger.error(f"Error processing event, please check Log File")
        file_logger.error(f"Error processing event: {e}")
