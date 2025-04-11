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

import time, sys
from config import *
from snipegenius import check_token_safety
from exit_strategy import intelligent_adaptive_liquidation

def get_and_increment_nonce(w3, address):
    nonce = w3.eth.get_transaction_count(address)
    logger.debug(f"Current nonce: {nonce}")
    return nonce

def execute_buy(amount_out_min, pair_address, wbnb_address, router, w3, bnb_reserve, min_safety_score, amount_in, sell_time=None):
    from config import private_key, my_address
    if 'balance_manager' in sys.modules and 'balance_manager' in globals():
        try:
            from snipe import balance_manager
            if balance_manager is not None and not balance_manager.can_purchase():
                logger.warning(f"Purchase skipped for pair {pair_address}: Balance below minimum threshold")
                return
        except Exception as e:
            logger.error(f"Error checking balance manager: {str(e)}")
    if not all(isinstance(x, int) for x in [amount_out_min, bnb_reserve]):
        raise ValueError("All numerical arguments must be of type int.")

    my_address = my_address.strip()
    pair_address = pair_address.strip()
    wbnb_address = wbnb_address.strip()
    pair_contract = w3.eth.contract(address=pair_address, abi=pair_abi)

    token0_address = pair_contract.functions.token0().call()
    token1_address = pair_contract.functions.token1().call()

    logger.debug(f"Token 0 address: {token0_address}")
    logger.debug(f"Token 1 address: {token1_address}")

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

    from coinOps import get_bnb_balance
    bnb_balance = get_bnb_balance()
    human_readable_bnb = Web3.from_wei(bnb_balance, 'ether')
    logger.debug(f"BNB balance: {human_readable_bnb} BNB")
    bnb_amount_needed = amount_in

    if bnb_amount_needed > 0:
        logger.debug(f"Amount needed for swap: {Web3.from_wei(bnb_amount_needed, 'ether')} BNB")
        if bnb_balance < bnb_amount_needed:
            logger.error(f"Insufficient BNB balance. Need {Web3.from_wei(bnb_amount_needed, 'ether')} BNB but only have {human_readable_bnb} BNB")
            return
    else:
        logger.error("Amount to swap is zero. Check your wallet balance and percentage settings.")
        return

    try:
        from coinOps import get_token_info
        token_info = get_token_info(tokentobuy)
        logger.debug(f"Token info: Name: {token_info['name']}, Symbol: {token_info['symbol']}, Decimals: {token_info['decimals']}")
        logger.info(f"Attempting to swap {Web3.from_wei(bnb_amount_needed, 'ether')} BNB for {token_info['symbol']} tokens")
        logger.debug(f"Minimum amount out: {Web3.from_wei(amount_out_min, 'ether') * (10 ** (18 - token_info['decimals']))} {token_info['symbol']}")

        try:
            gas_estimate = router.functions.swapExactETHForTokens(
                amount_out_min,
                [wbnb_address, tokentobuy],
                my_address,
                int(time.time()) + 120
            ).estimate_gas({
                'from': my_address,
                'value': bnb_amount_needed
            })

            logger.debug(f"Gas estimate successful: {gas_estimate}")
        except Exception as gas_error:
            logger.error(f"Gas estimation failed: {str(gas_error)}")
            gas_estimate = 500000
            logger.info(f"Using fallback gas limit: {gas_estimate}")

        estimated_gas_price = w3.eth.gas_price
        logger.debug(f"Estimated gas price: {estimated_gas_price}")

        nonce = get_and_increment_nonce(w3, my_address)
        txn = {
            'from': my_address,
            'value': bnb_amount_needed,
            'gas': gas_estimate,
            'gasPrice': estimated_gas_price,
            'nonce': nonce,
            'chainId': 56
        }

        swap_txn = router.functions.swapExactETHForTokens(
            amount_out_min,
            [wbnb_address, tokentobuy],
            my_address,
            int(time.time()) + 120
        ).build_transaction(txn)

        logger.debug(f"Transaction details: Gas: {swap_txn['gas']}, Gas Price: {swap_txn['gasPrice']}, Nonce: {swap_txn['nonce']}, Value: {swap_txn['value']}")

        for attempt in range(3):
            try:
                signed_swap_txn = w3.eth.account.sign_transaction(swap_txn, private_key)
                txn_hash = w3.eth.send_raw_transaction(signed_swap_txn.raw_transaction)
                logger.info(f"Transaction sent with hash: {txn_hash.hex()}")
                logger.debug(f"Waiting for transaction receipt...")
                txn_receipt = w3.eth.wait_for_transaction_receipt(txn_hash)

                if txn_receipt.status == 0:
                    logger.error(f"Transaction reverted on-chain with hash: {txn_hash.hex()} retrying after 3 seconds...")
                    time.sleep(3)
                    nonce = w3.eth.get_transaction_count(my_address)
                    logger.info(f"Fetched fresh nonce: {nonce}")
                    swap_txn['nonce'] = nonce
                    continue

                if txn_receipt.status == 1:
                    logger.debug(f"Transaction successful with hash: {txn_hash.hex()}\n")
                    token_contract = w3.eth.contract(address=tokentobuy, abi=token_abi)
                    token_balance = token_contract.functions.balanceOf(my_address).call()

                    if token_balance > 0:
                        human_readable_balance = token_balance / (10 ** token_info['decimals'])
                        logger.info(f"Successfully purchased {human_readable_balance} {token_info['symbol']} tokens")
                        buy_price = bnb_amount_needed / token_balance

                        if sell_time is not None:
                            logger.info(f"Token will be sold after {sell_time} minutes")

                        token_monitor_instance = None
                        found_method = None

                        try:
                            from snipe import token_monitor_manager
                            if token_monitor_manager is not None:
                                token_monitor_instance = token_monitor_manager
                                found_method = "direct import"
                        except (ImportError, AttributeError) as e:
                            logger.debug(f"Could not import token_monitor_manager directly: {str(e)}")

                        if token_monitor_instance is None:
                            try:
                                import builtins
                                if hasattr(builtins, 'token_monitor_manager'):
                                    token_monitor_instance = builtins.token_monitor_manager
                                    found_method = "builtins"
                            except Exception as e:
                                logger.debug(f"Could not access token_monitor_manager from builtins: {str(e)}")

                        if token_monitor_instance is None and 'token_monitor_manager' in globals():
                            token_monitor_instance = globals()['token_monitor_manager']
                            found_method = "globals"

                        if token_monitor_instance is not None:
                            logger.debug(f"Found token_monitor_manager via {found_method}")

                            try:
                                token_monitor_instance.add_token(tokentobuy, buy_price, token_balance, sell_time)
                                logger.info(f"Added token {tokentobuy} to monitoring")

                                time.sleep(2)
                                logger.debug(f"Added delay after token purchase to ensure monitoring is active")

                                active_tokens = token_monitor_instance.get_active_tokens()
                                if tokentobuy in active_tokens:
                                    logger.debug(f"Confirmed token {tokentobuy} is in active monitoring list")
                                else:
                                    logger.warning(f"Token {tokentobuy} was not found in active monitoring list")
                            except Exception as e:
                                logger.error(f"Error adding token to monitor: {str(e)}")
                                intelligent_adaptive_liquidation(tokentobuy, buy_price, token_balance, sell_time)
                        else:
                            logger.warning("Could not access token_monitor_manager, falling back to direct liquidation")
                            intelligent_adaptive_liquidation(tokentobuy, buy_price, token_balance, sell_time)
                    else:
                        logger.warning(f"Transaction succeeded but no tokens were received. This could be due to high fees or other token mechanics.")

                    break

            except Exception as e:
                logger.error(f"Error sending transaction: {str(e)}")
                # Wait 3 seconds before fetching a fresh nonce for any transaction error
                logger.info("Waiting 3 seconds before fetching a fresh nonce...")
                time.sleep(3)

                if 'nonce too low' in str(e) or 'replacement transaction underpriced' in str(e):
                    logger.warning("Nonce issue detected, fetching fresh nonce...")
                    nonce = w3.eth.get_transaction_count(my_address)
                    logger.info(f"Fetched fresh nonce: {nonce}")
                    swap_txn['nonce'] = nonce
                elif 'already known' in str(e):
                    logger.warning("Transaction already in the mempool, waiting for confirmation...")
                    try:
                        # Wait for the transaction that's already in the mempool
                        txn_receipt = w3.eth.wait_for_transaction_receipt(txn_hash)
                        if txn_receipt.status == 0:
                            logger.error(f"Previously submitted transaction reverted with hash: {txn_hash.hex()}")
                            # Fetch fresh nonce after transaction was processed
                            nonce = w3.eth.get_transaction_count(my_address)
                            logger.info(f"Fetched fresh nonce: {nonce}")
                            swap_txn['nonce'] = nonce
                    except Exception as wait_error:
                        logger.error(f"Error waiting for transaction: {str(wait_error)}")
                        # Fetch fresh nonce
                        nonce = w3.eth.get_transaction_count(my_address)
                        logger.info(f"Fetched fresh nonce: {nonce}")
                        swap_txn['nonce'] = nonce
                else:
                    # For other errors, attempt one retry with a fresh nonce
                    logger.warning(f"Unknown error: {str(e)}, fetching fresh nonce")
                    nonce = w3.eth.get_transaction_count(my_address)
                    logger.info(f"Fetched fresh nonce: {nonce}")
                    swap_txn['nonce'] = nonce
        else:
            logger.error(f"Transaction failed with status: {txn_receipt.status}")

    except ValueError as e:
        if 'revert' in str(e):
            logger.error(f"Transaction reverted. Raw Error: {e}")

            try:
                tx = e.args[0]['transaction']
                receipt = w3.eth.get_transaction_receipt(tx)
                if receipt and 'logs' in receipt and len(receipt['logs']) > 0:
                    revert_reason = w3.to_text(receipt['logs'][0]['data'])
                    logger.error(f"Revert Reason: {revert_reason}")
                else:
                    logger.error("Could not extract revert reason from receipt")
            except Exception as receipt_error:
                logger.error(f"Error extracting revert reason: {str(receipt_error)}")

            from coinOps import get_bnb_balance
            bnb_balance = get_bnb_balance()
            logger.debug(f"Current BNB balance: {Web3.from_wei(bnb_balance, 'ether')} BNB")

        else:
            logger.error(f"Execution reverted, Check Log File")
            logger.debug(f"Execution reverted: {e}")

    except Exception as e:
        logger.error(f"An error occurred, Check Log file")
        logger.debug(f"An error occurred: {str(e)}")

pair_created_event_abi = [event_abi for event_abi in factory_abi if event_abi['type'] == 'event' and event_abi['name'] == 'PairCreated'][0]

def check_liquidity(pair_address, wbnb_address, w3):
    pair_contract = w3.eth.contract(address=pair_address, abi=pair_abi)
    reserves = pair_contract.functions.getReserves().call()
    reserve0, reserve1 = reserves[0], reserves[1]
    token0_address = pair_contract.functions.token0().call()
    token1_address = pair_contract.functions.token1().call()
    minimum_liquidity = Web3.to_wei(2, 'ether')
    bnb_reserve = None
    if token0_address.lower() == wbnb_address.lower():
        if reserve0 >= minimum_liquidity:
            bnb_reserve = reserve0
    elif token1_address.lower() == wbnb_address.lower():
        if reserve1 >= minimum_liquidity:
            bnb_reserve = reserve1

    if bnb_reserve is not None:
        return True, bnb_reserve
    else:
        return False, bnb_reserve

def handle_event(event, percentage_for_amount_in, min_safety_score, mode=1, sell_time=None):
    try:
        if mode == 2:
            token_monitor_instance = None

            try:
                from snipe import token_monitor_manager
                if token_monitor_manager is not None:
                    token_monitor_instance = token_monitor_manager
                    logger.debug("Mode 2: Found token_monitor_manager via direct import")
            except (ImportError, AttributeError) as e:
                logger.debug(f"Mode 2: Could not import token_monitor_manager directly: {str(e)}")

            if token_monitor_instance is None:
                try:
                    import builtins
                    if hasattr(builtins, 'token_monitor_manager'):
                        token_monitor_instance = builtins.token_monitor_manager
                        logger.debug("Mode 2: Found token_monitor_manager via builtins")
                except Exception as e:
                    logger.debug(f"Mode 2: Could not access token_monitor_manager from builtins: {str(e)}")

            if token_monitor_instance is not None:
                try:
                    active_tokens = token_monitor_instance.get_active_tokens()

                    if active_tokens and len(active_tokens) > 0:
                        logger.info(f"Mode 2: Already monitoring {len(active_tokens)} tokens. Skipping new pair.")
                        return
                    else:
                        logger.debug("Mode 2: No active tokens being monitored. Proceeding with pair evaluation.")

                except Exception as e:
                    logger.warning("Mode 2: Error checking active tokens. Skipping new pair as a precaution.")
                    return
            else:
                logger.warning("Mode 2: Token monitor manager not initialized. This is unexpected.")
                return

        if 'balance_manager' in sys.modules and 'balance_manager' in globals():
            try:
                from snipe import balance_manager
                if balance_manager is not None and not balance_manager.can_purchase():
                    logger.debug("Skipping event processing: Balance below minimum threshold")
                    return
            except Exception as e:
                logger.error(f"Error checking balance manager: {str(e)}")

        decoded_data = w3.eth.contract(abi=[pair_created_event_abi]).events.PairCreated().process_log(event)
        pair_address = decoded_data['args']['pair']
        pair_address = Web3.to_checksum_address(pair_address.strip())
        liquidity_status, bnb_reserve = check_liquidity(pair_address, wbnb_address, w3)

        if bnb_reserve is None:
            logger.debug(f"Insufficient BNB Reserve for {pair_address}")
            return

        bnb_reserve = int(bnb_reserve)
        from coinOps import get_bnb_balance
        if 'balance_manager' in sys.modules and 'balance_manager' in globals():
            try:
                from snipe import balance_manager
                if balance_manager is not None:
                    balance = balance_manager.get_balance()
                else:
                    balance = get_bnb_balance()
            except Exception as e:
                logger.error(f"Error getting balance from manager: {str(e)}")
                balance = get_bnb_balance()
        else:
            balance = get_bnb_balance()

        if liquidity_status:
            amount_in = int(balance * percentage_for_amount_in)
            slippage_levels = [0.01, 0.05, 0.10]

            for slippage in slippage_levels:
                try:
                    amount_out_min = int(amount_in * (1 - slippage))
                    execute_buy(amount_out_min, pair_address, wbnb_address, router, w3, bnb_reserve, min_safety_score, amount_in, sell_time)
                    break
                except Exception as e:
                    logger.error(f"Failed with slippage {slippage * 100}%. Retrying... Error: {e}")

        else:
            logger.debug(f"Insufficient liquidity. Checking for new Tokens")
    except Exception as e:
        logger.error(f"Error processing event: {e}")
