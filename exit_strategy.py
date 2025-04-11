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

def execute_sell(token_address, amount_to_sell, slippage):
    from config import my_address, private_key, initialize_credentials
    if not my_address:
        initialize_credentials()
        from config import my_address, private_key
        if not my_address:
            logger.error("Failed to initialize wallet address in execute_sell. Cannot proceed.")
            return False

    try:
        token_contract = w3.eth.contract(address=token_address, abi=token_abi)
        balance = token_contract.functions.balanceOf(my_address).call()

        if balance == 0:
            logger.warning(f"No tokens to sell for {token_address}: balance is 0")
            return False

        amount_to_sell = min(amount_to_sell, balance)
        current_price = get_current_price(token_address)
        amount_out_min = 1

        if current_price > 0:
            expected_bnb_output = amount_to_sell * current_price
            logger.debug(f"Expected BNB output based on current price: {expected_bnb_output}")
        else:
            logger.warning(f"Unable to get valid price for {token_address}, using fallback minimum output")

        logger.info(f"Selling {amount_to_sell} tokens of {token_address} with {slippage*100:.1f}% slippage")

        current_allowance = token_contract.functions.allowance(my_address, router.address).call()
        if current_allowance < amount_to_sell:
            logger.info(f"Approving router to spend {amount_to_sell} tokens of {token_address}")
            nonce = w3.eth.get_transaction_count(my_address)
            approve_txn = token_contract.functions.approve(
                router.address,
                amount_to_sell
            ).build_transaction({
                'from': my_address,
                'gas': 100000,
                'gasPrice': w3.to_wei('5', 'gwei'),
                'nonce': nonce,
                'chainId': 56
            })

            signed_approve_txn = w3.eth.account.sign_transaction(approve_txn, private_key=private_key)
            approve_txn_hash = w3.eth.send_raw_transaction(signed_approve_txn.raw_transaction)
            logger.info(f"Approval transaction sent with hash: {approve_txn_hash.hex()}")
            approve_receipt = w3.eth.wait_for_transaction_receipt(approve_txn_hash)
            if approve_receipt.status != 1:
                logger.error(f"Token approval failed with status {approve_receipt.status}")
                return False

            logger.debug(f"Token approval successful, proceeding with sell")
        else:
            logger.debug(f"Router already has sufficient allowance ({current_allowance}) for selling {amount_to_sell} tokens")

        nonce = w3.eth.get_transaction_count(my_address)
        deadline = int(time.time()) + 120
        txn = router.functions.swapExactTokensForETH(
            amount_to_sell,
            amount_out_min,
            [token_address, wbnb_address],
            my_address,
            deadline
        ).build_transaction({
            'from': my_address,
            'gas': 300000,
            'gasPrice': w3.to_wei('5', 'gwei'),
            'nonce': nonce,
            'chainId': 56
        })

        signed_txn = w3.eth.account.sign_transaction(txn, private_key=private_key)
        txn_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
        logger.info(f"Sell transaction sent with hash: {txn_hash.hex()}")
        txn_receipt = w3.eth.wait_for_transaction_receipt(txn_hash)

        if txn_receipt.status == 1:
            logger.info(f"Sold {amount_to_sell} tokens of {token_address} successfully")
            token_monitor_instance = None
            found_method = None

            # Method 1: Try importing directly from snipe
            try:
                from snipe import token_monitor_manager as tmm1
                if tmm1 is not None:
                    token_monitor_instance = tmm1
                    found_method = "Direct import"
            except (ImportError, AttributeError) as e:
                logger.debug(f"Could not import token_monitor_manager from snipe: {str(e)}")

            # Method 2: Try using builtins
            if token_monitor_instance is None:
                try:
                    import builtins
                    if hasattr(builtins, 'token_monitor_manager'):
                        token_monitor_instance = builtins.token_monitor_manager
                        found_method = "Builtins"
                except Exception as e:
                    logger.debug(f"Could not access token_monitor_manager from builtins: {str(e)}")

            # Method 3: Check if it's in globals
            if token_monitor_instance is None and 'token_monitor_manager' in globals():
                token_monitor_instance = globals()['token_monitor_manager']
                found_method = "Globals"

            # Method 4: Check if it's in sys.modules
            if token_monitor_instance is None:
                try:
                    if 'snipe' in sys.modules:
                        module = sys.modules['snipe']
                        if hasattr(module, 'token_monitor_manager'):
                            token_monitor_instance = getattr(module, 'token_monitor_manager')
                            found_method = "Sys modules"
                except Exception as e:
                    logger.debug(f"Could not access token_monitor_manager from sys.modules: {str(e)}")

            if token_monitor_instance is not None:
                logger.debug(f"Found token_monitor_manager via {found_method}")

                try:
                    active_monitors = getattr(token_monitor_instance, 'active_monitors', {})
                    if token_address in active_monitors:
                        monitor = active_monitors[token_address]
                        monitor.sold = True
                        logger.debug(f"Token {token_address} marked as sold in token monitor")

                    if token_address in active_monitors and hasattr(active_monitors[token_address], 'sold'):
                        if active_monitors[token_address].sold:
                            logger.debug(f"Confirmed token {token_address} is marked as sold")
                        else:
                            logger.warning(f"Token {token_address} still not marked as sold, forcing it")
                            active_monitors[token_address].sold = True

                    token_monitor_instance.remove_token(token_address)
                    logger.debug(f"Token {token_address} removed from monitoring")

                    try:
                        balance_manager = None

                        try:
                            from snipe import balance_manager as bm
                            balance_manager = bm
                        except (ImportError, AttributeError):
                            pass

                        if balance_manager is None:
                            try:
                                import builtins
                                if hasattr(builtins, 'balance_manager'):
                                    balance_manager = builtins.balance_manager
                            except Exception:
                                pass

                        if balance_manager is not None:
                            balance_manager.update_balance()
                            logger.debug("Balance updated after sell")
                    except Exception as e:
                        logger.debug(f"Could not update balance manager: {str(e)}")
                except Exception as e:
                    logger.error(f"Error updating token monitor after sell: {str(e)}")
            else:
                logger.warning("Could not find token_monitor_manager to update token status")

            return True
        else:
            logger.error(f"Sell transaction failed with status {txn_receipt.status}")
            return False

    except Exception as e:
        logger.error(f"Sell transaction failed for {token_address}: {str(e)}")
        return False

def get_current_price(token_address):
    if not token_address:
        logger.error("Invalid token address provided to get_current_price")
        return 0

    try:
        if not Web3.is_address(token_address):
            logger.error(f"Invalid token address format: {token_address}")
            return 0

        factory_contract = w3.eth.contract(address=factory_address, abi=factory_abi)
        pair_address = factory_contract.functions.getPair(token_address, wbnb_address).call()

        if pair_address == '0x0000000000000000000000000000000000000000':
            logger.warning(f"No pair found for token {token_address}")
            return 0

        pair_contract = w3.eth.contract(address=pair_address, abi=pair_abi)
        reserves = pair_contract.functions.getReserves().call()
        token0 = pair_contract.functions.token0().call()

        if token0.lower() == token_address.lower():
            token_reserve = reserves[0]
            bnb_reserve = reserves[1]
        else:
            token_reserve = reserves[1]
            bnb_reserve = reserves[0]

        if token_reserve > 0:
            price = bnb_reserve / token_reserve
            logger.debug(f"Current price for {token_address}: {price} BNB")
            return price
        return 0
    except Exception as e:
        logger.error(f"Error getting price for {token_address}: {str(e)}")
        return 0

def initial_monitoring(token_address, buy_price, buy_amount):
    from config import my_address, initialize_credentials
    if not my_address:
        logger.debug("Wallet address not initialized in initial_monitoring. Initializing credentials...")
        initialize_credentials()
        from config import my_address
        if not my_address:
            logger.error("Failed to initialize wallet address in initial_monitoring. Cannot proceed.")
            return "FAILED"
        logger.debug(f"Wallet address initialized in initial_monitoring: {my_address}")

    start_time = time.time()
    highest_price = buy_price
    logger.info(f"Starting initial monitoring for {token_address} with buy price {buy_price}")

    while time.time() - start_time <= INITIAL_MONITORING_DURATION:
        current_price = get_current_price(token_address)
        if current_price > 0:
            highest_price = max(highest_price, current_price)
            price_change = (current_price - buy_price) / buy_price
            price_from_peak = (current_price - highest_price) / highest_price

            if int(time.time()) % 15 == 0:
                logger.debug(f"Token {token_address}: Current price: {current_price}, Change: {price_change*100:.2f}%, From peak: {price_from_peak*100:.2f}%")

            if price_change >= 0.10:
                logger.info(f"Initial monitoring: Taking quick profit at {price_change*100:.2f}%")
                if execute_sell(token_address, buy_amount, 0.01):
                    return "SOLD"

            elif price_change <= -0.10:
                logger.warning(f"Initial monitoring: Emergency stop loss at {price_change*100:.2f}%")
                if execute_sell(token_address, buy_amount, 0.05):
                    return "SOLD"

            elif highest_price > buy_price and price_from_peak <= -0.05:
                logger.warning(f"Initial monitoring: Trailing stop triggered. Down {abs(price_from_peak)*100:.2f}% from peak")
                if execute_sell(token_address, buy_amount, 0.03):
                    return "SOLD"

        time.sleep(1)

    logger.debug(f"Initial monitoring completed for {token_address}")
    return "CONTINUE"

def dynamic_protection_mode(token_address, buy_price, buy_amount):
    from config import my_address, initialize_credentials
    if not my_address:
        logger.debug("Wallet address not initialized in dynamic_protection_mode. Initializing credentials...")
        initialize_credentials()
        from config import my_address
        if not my_address:
            logger.error("Failed to initialize wallet address in dynamic_protection_mode. Cannot proceed.")
            return "FAILED"
        logger.debug(f"Wallet address initialized in dynamic_protection_mode: {my_address}")

    start_time = time.time()
    highest_price = buy_price

    logger.info(f"Starting dynamic protection mode for {token_address}")

    profit_target_1 = buy_price * 1.2
    profit_target_2 = buy_price * 1.5

    while time.time() - start_time <= DYNAMIC_PROTECTION_DURATION:
        current_price = get_current_price(token_address)

        if current_price > 0:
            highest_price = max(highest_price, current_price)
            price_change = (current_price - buy_price) / buy_price
            price_from_peak = (current_price - highest_price) / highest_price

            if int(time.time()) % 30 == 0:
                logger.debug(f"Dynamic protection: Token {token_address}: Current price: {current_price}, Change: {price_change*100:.2f}%, From peak: {price_from_peak*100:.2f}%")

            if current_price >= profit_target_2:
                logger.info(f"Dynamic protection: Taking profit at 50%+ gain ({price_change*100:.2f}%)")
                if execute_sell(token_address, buy_amount, 0.02):
                    return "SOLD"
            elif current_price >= profit_target_1:
                if price_from_peak <= -0.03:
                    logger.info(f"Dynamic protection: Taking profit with tight trailing stop at {price_change*100:.2f}% gain")
                    if execute_sell(token_address, buy_amount, 0.02):
                        return "SOLD"

            elif current_price <= highest_price * (1 - TRAILING_STOP_PERCENTAGE):
                logger.info(f"Dynamic protection: Triggering trailing stop at {current_price} (down {TRAILING_STOP_PERCENTAGE*100:.1f}% from {highest_price})")
                if execute_sell(token_address, buy_amount, 0.02):
                    return "SOLD"

            elif current_price <= buy_price * 0.85:
                logger.warning(f"Dynamic protection: Stop loss triggered at {price_change*100:.2f}% loss")
                if execute_sell(token_address, buy_amount, 0.05):
                    return "SOLD"

        time.sleep(1)

    logger.info(f"Dynamic protection: Time-based exit for {token_address}")
    if current_price > buy_price:
        logger.info(f"Dynamic protection: Time-based exit with profit of {price_change*100:.2f}%")
        if execute_sell(token_address, buy_amount, 0.02):
            return "SOLD"
    else:
        logger.warning(f"Dynamic protection: Time-based exit with loss of {price_change*100:.2f}%")
        if execute_sell(token_address, buy_amount, 0.03):
            return "SOLD"
    return "CONTINUE"

def tiered_smart_exit(token_address, buy_price, buy_amount):
    from config import my_address, initialize_credentials
    if not my_address:
        logger.debug("Wallet address not initialized in tiered_smart_exit. Initializing credentials...")
        initialize_credentials()
        from config import my_address
        if not my_address:
            logger.error("Failed to initialize wallet address in tiered_smart_exit. Cannot proceed.")
            return "FAILED"
        logger.debug(f"Wallet address initialized in tiered_smart_exit: {my_address}")

    logger.info(f"Starting tiered smart exit for {token_address}")

    current_amount = buy_amount
    exit_multipliers = TIERED_EXIT_MULTIPLIERS.copy()
    current_multiplier = exit_multipliers.pop(0) if exit_multipliers else None

    if not current_multiplier:
        logger.warning("No exit multipliers defined, selling entire position")
        if execute_sell(token_address, current_amount, 0.02):
            return "SOLD"
        return "CONTINUE"

    highest_price = buy_price
    start_time = time.time()
    last_log_time = 0
    max_tier_wait_time = 150
    tier_start_time = time.time()

    while current_multiplier and current_amount > 0:
        current_price = get_current_price(token_address)

        if current_price <= 0:
            time.sleep(1)
            continue

        highest_price = max(highest_price, current_price)
        price_change = (current_price - buy_price) / buy_price
        price_from_peak = (current_price - highest_price) / highest_price
        current_time = time.time()

        if current_time - last_log_time >= 60:
            logger.debug(f"Tiered exit: Token {token_address}: Current price: {current_price}, "
                       f"Target: {buy_price * current_multiplier} ({current_multiplier}x), "
                       f"Change: {price_change*100:.2f}%, From peak: {price_from_peak*100:.2f}%")
            last_log_time = current_time

        target_price = buy_price * current_multiplier

        if current_price >= target_price:
            amount_to_sell = current_amount * 0.25
            logger.info(f"Tiered exit: Selling 25% at {current_multiplier}x target ({price_change*100:.2f}% profit)")

            if execute_sell(token_address, amount_to_sell, 0.02):
                current_amount -= amount_to_sell
                logger.info(f"Tiered exit: Sold successfully. Remaining: {current_amount}")

                current_multiplier = exit_multipliers.pop(0) if exit_multipliers else None
                if current_multiplier:
                    logger.debug(f"Tiered exit: Moving to next target: {current_multiplier}x")
                    tier_start_time = time.time()
                else:
                    logger.info("Tiered exit: All targets reached, selling remaining position")
                    if current_amount > 0 and execute_sell(token_address, current_amount, 0.02):
                        return "SOLD"
            else:
                logger.warning("Tiered exit: Failed to sell at target price, will retry")

        elif highest_price > buy_price and price_from_peak <= -0.07:
            logger.warning(f"Tiered exit: Trailing stop triggered. Down {abs(price_from_peak)*100:.2f}% from peak")
            if execute_sell(token_address, current_amount, 0.03):
                return "SOLD"

        elif time.time() - tier_start_time > max_tier_wait_time:
            logger.warning(f"Tiered exit: Timeout waiting for {current_multiplier}x target, moving to next tier")
            current_multiplier = exit_multipliers.pop(0) if exit_multipliers else None
            if current_multiplier:
                logger.debug(f"Tiered exit: Moving to next target: {current_multiplier}x")
                tier_start_time = time.time()
            else:
                logger.debug("Tiered exit: All tiers timed out, selling remaining position")
                if current_amount > 0 and execute_sell(token_address, current_amount, 0.03):
                    return "SOLD"

        if time.time() - start_time > 600:
            logger.warning("Tiered exit: Maximum time reached (15 minutes), selling remaining position")
            if current_amount > 0 and execute_sell(token_address, current_amount, 0.03):
                return "SOLD"
            break

        time.sleep(1)

    if current_amount > 0:
        logger.info("Tiered exit: Selling remaining position")
        if execute_sell(token_address, current_amount, 0.03):
            return "SOLD"

    return "CONTINUE"

def time_based_exit(token_address, buy_price, buy_amount, sell_time_minutes):
    logger.info(f"Starting time-based exit for {token_address} after {sell_time_minutes} minutes")

    from config import my_address, initialize_credentials
    if not my_address:
        logger.debug("Wallet address not initialized in time_based_exit. Initializing credentials...")
        initialize_credentials()
        from config import my_address
        if not my_address:
            logger.error("Failed to initialize wallet address in time_based_exit. Cannot proceed.")
            return "FAILED"
        logger.debug(f"Wallet address initialized in time_based_exit: {my_address}")

    sell_time_seconds = sell_time_minutes * 60
    start_time = time.time()
    highest_price = buy_price
    last_log_time = 0

    import builtins
    token_monitor_instance = getattr(builtins, 'token_monitor_manager', None)
    if token_monitor_instance is not None:
        logger.debug(f"Time-based exit: Found token_monitor_manager via builtins")
    else:
        logger.warning(f"Time-based exit: token_monitor_manager not available via builtins")

    expected_sell_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time + sell_time_seconds))
    logger.debug(f"Time-based exit: Will sell token {token_address} at approximately {expected_sell_time}")
    token_contract = w3.eth.contract(address=token_address, abi=token_abi)
    initial_balance = token_contract.functions.balanceOf(my_address).call()

    if initial_balance == 0:
        logger.warning(f"Time-based exit: No tokens to sell for {token_address}, balance is 0")

        if token_monitor_instance is not None:
            try:
                active_monitors = getattr(token_monitor_instance, 'active_monitors', {})
                if token_address in active_monitors:
                    monitor = active_monitors[token_address]
                    monitor.sold = True
                    monitor.sold_event.set()
                    logger.debug(f"Time-based exit: Marked token {token_address} as sold in TokenMonitor (zero balance)")
            except Exception as e:
                logger.debug(f"Time-based exit: Error marking zero-balance token as sold: {str(e)}")

        return "SOLD"

    logger.debug(f"Time-based exit: Initial token balance is {initial_balance}")

    while time.time() - start_time <= sell_time_seconds:
        current_time = time.time()
        current_price = get_current_price(token_address)
        if current_price > 0:
            highest_price = max(highest_price, current_price)
            price_change = (current_price - buy_price) / buy_price

            if current_time - last_log_time >= 30:
                time_remaining = sell_time_seconds - (current_time - start_time)
                logger.debug(f"Time-based exit: {int(time_remaining)} seconds remaining. Current price: {current_price}, Change: {price_change*100:.2f}%")
                last_log_time = current_time
                current_balance = token_contract.functions.balanceOf(my_address).call()
                if current_balance == 0:
                    logger.warning(f"Time-based exit: Token balance is now 0, token may have already been sold or transferred")
                    if token_monitor_instance is not None:
                        try:
                            active_monitors = getattr(token_monitor_instance, 'active_monitors', {})
                            if token_address in active_monitors:
                                monitor = active_monitors[token_address]
                                monitor.sold = True
                                monitor.sold_event.set()
                                logger.debug(f"Time-based exit: Marked token {token_address} as sold in TokenMonitor (mid-wait)")
                        except Exception as e:
                            logger.debug(f"Time-based exit: Error marking mid-wait token as sold: {str(e)}")

                    return "SOLD"

        time.sleep(1)

    logger.info(f"Time-based exit: {sell_time_minutes} minutes elapsed, selling token {token_address}")
    final_balance = token_contract.functions.balanceOf(my_address).call()
    if final_balance == 0:
        logger.warning(f"Time-based exit: No tokens to sell, balance is 0")
        if token_monitor_instance is not None:
            try:
                active_monitors = getattr(token_monitor_instance, 'active_monitors', {})
                if token_address in active_monitors:
                    monitor = active_monitors[token_address]
                    monitor.sold = True
                    monitor.sold_event.set()
                    logger.debug(f"Time-based exit: Marked token {token_address} as sold in TokenMonitor (end of wait)")

            except Exception as e:
                logger.debug(f"Time-based exit: Error marking end-of-wait token as sold: {str(e)}")

        return "SOLD"

    current_price = get_current_price(token_address)
    if current_price > 0:
        price_change = (current_price - buy_price) / buy_price
        logger.debug(f"Time-based exit: Final price: {current_price}, Change: {price_change*100:.2f}%")
    else:
        logger.warning(f"Time-based exit: Unable to get current price for {token_address}")

    retry_count = 0
    for slippage in [0.01, 0.03, 0.05, 0.10]:
        retry_count += 1
        logger.debug(f"Time-based exit: Sell attempt #{retry_count} with {slippage*100:.1f}% slippage")
        logger.info(f"Time-based exit: Executing sell for {token_address} with {slippage*100:.1f}% slippage, balance: {final_balance}")

        if execute_sell(token_address, final_balance, slippage):
            logger.info(f"Time-based exit: Successfully sold token {token_address}")

            if token_monitor_instance is not None:
                try:
                    active_monitors = getattr(token_monitor_instance, 'active_monitors', {})
                    if token_address in active_monitors:
                        monitor = active_monitors[token_address]
                        monitor.sold = True
                        monitor.sold_event.set()
                        logger.debug(f"Time-based exit: Double-checking token {token_address} is marked as sold")
                except Exception as e:
                    logger.debug(f"Time-based exit: Error in double-check marking token as sold: {str(e)}")

            return "SOLD"
        else:
            logger.warning(f"Time-based exit: Sell attempt #{retry_count} failed, will retry with higher slippage")
            time.sleep(2)

    logger.warning(f"Time-based exit: Failed to sell token {token_address} after multiple attempts")
    return "CONTINUE"

def intelligent_adaptive_liquidation(token_address, buy_price, buy_amount, sell_time=None):
    logger.info("Starting intelligent adaptive liquidation strategy")

    from config import my_address, initialize_credentials
    if not my_address:
        logger.debug("Wallet address not initialized in intelligent_adaptive_liquidation. Initializing credentials...")
        initialize_credentials()
        from config import my_address
        if not my_address:
            logger.error("Failed to initialize wallet address in intelligent_adaptive_liquidation. Cannot proceed.")
            return "FAILED"
        logger.debug(f"Wallet address initialized in intelligent_adaptive_liquidation: {my_address}")

    if sell_time is not None:
        logger.info(f"Using time-based exit strategy with {sell_time} minute(s) timeout for token {token_address}")
        result = time_based_exit(token_address, buy_price, buy_amount, sell_time)
        if result == "SOLD":
            logger.info(f"Token {token_address} sold after {sell_time} minutes via time-based exit")
            return "SOLD"
    else:
        result = initial_monitoring(token_address, buy_price, buy_amount)
        if result == "SOLD":
            return "SOLD"

        result = dynamic_protection_mode(token_address, buy_price, buy_amount)
        if result == "SOLD":
            return "SOLD"

        result = tiered_smart_exit(token_address, buy_price, buy_amount)

    import sys
    if 'token_monitor_manager' in sys.modules and 'token_monitor_manager' in globals() and result != "SOLD":
        try:
            from snipe import token_monitor_manager
            if token_monitor_manager is not None:
                token_monitor_manager.remove_token(token_address)
                logger.debug(f"Removed token {token_address} from monitoring")
        except Exception as e:
            logger.error(f"Error removing token from monitor: {str(e)}")

    return result
