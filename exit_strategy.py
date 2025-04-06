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

def execute_sell(token_address, amount_to_sell, slippage):
    try:
        token_contract = w3.eth.contract(address=token_address, abi=token_abi)
        balance = token_contract.functions.balanceOf(my_address).call()

        if balance == 0:
            logger.warning("No tokens to sell")
            return False

        amount_to_sell = min(amount_to_sell, balance)
        amount_out_min = int(amount_to_sell * (1 - slippage))

        deadline = int(time.time()) + 120
        txn = router.functions.swapExactTokensForETH(
            amount_to_sell,
            amount_out_min,
            [token_address, wbnb],
            my_address,
            deadline
        ).buildTransaction({
            'from': my_address,
            'gas': 300000,
            'gasPrice': w3.to_wei('5', 'gwei'),
            'nonce': w3.eth.get_transaction_count(my_address),
        })

        signed_txn = w3.eth.account.sign_transaction(txn, private_key=private_key)
        txn_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
        txn_receipt = w3.eth.wait_for_transaction_receipt(txn_hash)

        if txn_receipt.status == 1:
            logger.info(f"Sold {amount_to_sell} tokens successfully")

            # If token monitor manager exists, notify it that we sold this token
            import sys
            if 'token_monitor_manager' in sys.modules and 'token_monitor_manager' in globals():
                try:
                    from snipe import token_monitor_manager, balance_manager
                    if token_monitor_manager is not None:
                        token_monitor_manager.remove_token(token_address)
                    # Update balance after selling
                    if balance_manager is not None:
                        balance_manager.update_balance()
                except Exception as e:
                    file_logger.error(f"Error updating token monitor after sell: {str(e)}")

            return True
        return False

    except Exception as e:
        logger.error(f"Sell transaction failed: {str(e)}")
        return False

def get_current_price(token_address):
    try:
        # Get the pair address for this token and WBNB
        factory_contract = w3.eth.contract(address=factory_address, abi=factory_abi)
        pair_address = factory_contract.functions.getPair(token_address, wbnb).call()

        if pair_address == '0x0000000000000000000000000000000000000000':
            logger.warning(f"No pair found for token {token_address}")
            return 0

        # Get the pair contract
        pair_contract = w3.eth.contract(address=pair_address, abi=pair_abi)

        # Get reserves
        reserves = pair_contract.functions.getReserves().call()
        token0 = pair_contract.functions.token0().call()

        # Determine which reserve is which
        if token0.lower() == token_address.lower():
            token_reserve = reserves[0]
            wbnb_reserve = reserves[1]
        else:
            token_reserve = reserves[1]
            wbnb_reserve = reserves[0]

        if token_reserve > 0:
            # Price in WBNB per token
            price = wbnb_reserve / token_reserve
            logger.debug(f"Current price for {token_address}: {price} WBNB")
            return price
        return 0
    except Exception as e:
        logger.error(f"Error getting price for {token_address}: {str(e)}")
        return 0

def initial_monitoring(token_address, buy_price, buy_amount):
    start_time = time.time()
    highest_price = buy_price

    logger.info(f"Starting initial monitoring for {token_address} with buy price {buy_price}")

    while time.time() - start_time <= INITIAL_MONITORING_DURATION:
        current_price = get_current_price(token_address)
        if current_price > 0:  # Only update if we got a valid price
            highest_price = max(highest_price, current_price)
            price_change = (current_price - buy_price) / buy_price
            price_from_peak = (current_price - highest_price) / highest_price

            # Log price updates every 15 seconds
            if int(time.time()) % 15 == 0:
                logger.info(f"Token {token_address}: Current price: {current_price}, Change: {price_change*100:.2f}%, From peak: {price_from_peak*100:.2f}%")

            # Take profit at 10% (more aggressive)
            if price_change >= 0.10:
                logger.info(f"Initial monitoring: Taking quick profit at {price_change*100:.2f}%")
                if execute_sell(token_address, buy_amount, 0.01):
                    return "SOLD"

            # Stop loss at 10% (more aggressive)
            elif price_change <= -0.10:
                logger.warning(f"Initial monitoring: Emergency stop loss at {price_change*100:.2f}%")
                if execute_sell(token_address, buy_amount, 0.05):
                    return "SOLD"

            # Trailing stop: If price drops 5% from highest point
            elif highest_price > buy_price and price_from_peak <= -0.05:
                logger.warning(f"Initial monitoring: Trailing stop triggered. Down {abs(price_from_peak)*100:.2f}% from peak")
                if execute_sell(token_address, buy_amount, 0.03):
                    return "SOLD"

        time.sleep(1)

    logger.info(f"Initial monitoring completed for {token_address}")
    return "CONTINUE"

def dynamic_protection_mode(token_address, buy_price, buy_amount):
    start_time = time.time()
    highest_price = buy_price

    logger.info(f"Starting dynamic protection mode for {token_address}")

    # Calculate profit targets
    profit_target_1 = buy_price * 1.2  # 20% profit
    profit_target_2 = buy_price * 1.5  # 50% profit

    while time.time() - start_time <= DYNAMIC_PROTECTION_DURATION:
        current_price = get_current_price(token_address)

        if current_price > 0:  # Only update if we got a valid price
            highest_price = max(highest_price, current_price)
            price_change = (current_price - buy_price) / buy_price
            price_from_peak = (current_price - highest_price) / highest_price

            # Log price updates every 30 seconds
            if int(time.time()) % 30 == 0:
                logger.info(f"Dynamic protection: Token {token_address}: Current price: {current_price}, Change: {price_change*100:.2f}%, From peak: {price_from_peak*100:.2f}%")

            # Take profit at specific targets
            if current_price >= profit_target_2:
                logger.info(f"Dynamic protection: Taking profit at 50%+ gain ({price_change*100:.2f}%)")
                if execute_sell(token_address, buy_amount, 0.02):
                    return "SOLD"
            elif current_price >= profit_target_1:
                # If we're at 20%+ profit, use a tighter trailing stop (3%)
                if price_from_peak <= -0.03:
                    logger.info(f"Dynamic protection: Taking profit with tight trailing stop at {price_change*100:.2f}% gain")
                    if execute_sell(token_address, buy_amount, 0.02):
                        return "SOLD"

            # Standard trailing stop
            elif current_price <= highest_price * (1 - TRAILING_STOP_PERCENTAGE):
                logger.info(f"Dynamic protection: Triggering trailing stop at {current_price} (down {TRAILING_STOP_PERCENTAGE*100:.1f}% from {highest_price})")
                if execute_sell(token_address, buy_amount, 0.02):
                    return "SOLD"

            # Stop loss if price drops significantly below buy price
            elif current_price <= buy_price * 0.85:  # 15% loss
                logger.warning(f"Dynamic protection: Stop loss triggered at {price_change*100:.2f}% loss")
                if execute_sell(token_address, buy_amount, 0.05):
                    return "SOLD"

        time.sleep(1)

    logger.info(f"Dynamic protection: Time-based exit for {token_address}")
    # Before time-based exit, check if we're in profit
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
    logger.info(f"Starting tiered smart exit for {token_address}")

    current_amount = buy_amount
    exit_multipliers = TIERED_EXIT_MULTIPLIERS.copy()
    current_multiplier = exit_multipliers.pop(0) if exit_multipliers else None

    if not current_multiplier:
        logger.warning("No exit multipliers defined, selling entire position")
        if execute_sell(token_address, current_amount, 0.02):
            return "SOLD"
        return "CONTINUE"

    # Track the highest price seen
    highest_price = buy_price
    start_time = time.time()
    last_log_time = 0

    # Maximum time to wait for each tier (10 minutes)
    max_tier_wait_time = 600
    tier_start_time = time.time()

    while current_multiplier and current_amount > 0:
        current_price = get_current_price(token_address)

        if current_price <= 0:
            time.sleep(1)
            continue

        highest_price = max(highest_price, current_price)
        price_change = (current_price - buy_price) / buy_price
        price_from_peak = (current_price - highest_price) / highest_price

        # Log status every minute
        current_time = time.time()
        if current_time - last_log_time >= 60:
            logger.info(f"Tiered exit: Token {token_address}: Current price: {current_price}, "
                       f"Target: {buy_price * current_multiplier} ({current_multiplier}x), "
                       f"Change: {price_change*100:.2f}%, From peak: {price_from_peak*100:.2f}%")
            last_log_time = current_time

        target_price = buy_price * current_multiplier

        # If we've reached the target price for this tier
        if current_price >= target_price:
            # Sell 25% of the current amount
            amount_to_sell = current_amount * 0.25
            logger.info(f"Tiered exit: Selling 25% at {current_multiplier}x target ({price_change*100:.2f}% profit)")

            if execute_sell(token_address, amount_to_sell, 0.02):
                current_amount -= amount_to_sell
                logger.info(f"Tiered exit: Sold successfully. Remaining: {current_amount}")

                # Move to next tier
                current_multiplier = exit_multipliers.pop(0) if exit_multipliers else None
                if current_multiplier:
                    logger.info(f"Tiered exit: Moving to next target: {current_multiplier}x")
                    tier_start_time = time.time()  # Reset the timer for the next tier
                else:
                    logger.info("Tiered exit: All targets reached, selling remaining position")
                    if current_amount > 0 and execute_sell(token_address, current_amount, 0.02):
                        return "SOLD"
            else:
                logger.warning("Tiered exit: Failed to sell at target price, will retry")

        # If price drops significantly from the peak, use trailing stop
        elif highest_price > buy_price and price_from_peak <= -0.07:  # 7% drop from peak
            logger.warning(f"Tiered exit: Trailing stop triggered. Down {abs(price_from_peak)*100:.2f}% from peak")
            if execute_sell(token_address, current_amount, 0.03):
                return "SOLD"

        # If we've waited too long for this tier, move to the next one
        elif time.time() - tier_start_time > max_tier_wait_time:
            logger.warning(f"Tiered exit: Timeout waiting for {current_multiplier}x target, moving to next tier")
            current_multiplier = exit_multipliers.pop(0) if exit_multipliers else None
            if current_multiplier:
                logger.info(f"Tiered exit: Moving to next target: {current_multiplier}x")
                tier_start_time = time.time()
            else:
                logger.info("Tiered exit: All tiers timed out, selling remaining position")
                if current_amount > 0 and execute_sell(token_address, current_amount, 0.03):
                    return "SOLD"

        # If total time exceeds 15 minutes, sell everything
        if time.time() - start_time > 900:  # 15 minutes
            logger.warning("Tiered exit: Maximum time reached (15 minutes), selling remaining position")
            if current_amount > 0 and execute_sell(token_address, current_amount, 0.03):
                return "SOLD"
            break

        time.sleep(1)

    # If we still have tokens left, sell them
    if current_amount > 0:
        logger.info("Tiered exit: Selling remaining position")
        if execute_sell(token_address, current_amount, 0.03):
            return "SOLD"

    return "CONTINUE"

def intelligent_adaptive_liquidation(token_address, buy_price, buy_amount):
    logger.info("Starting intelligent adaptive liquidation strategy")

    result = initial_monitoring(token_address, buy_price, buy_amount)
    if result == "SOLD":
        return

    result = dynamic_protection_mode(token_address, buy_price, buy_amount)
    if result == "SOLD":
        return

    result = tiered_smart_exit(token_address, buy_price, buy_amount)

    # If we reach here and the token wasn't sold, make sure we remove it from monitoring
    import sys
    if 'token_monitor_manager' in sys.modules and 'token_monitor_manager' in globals() and result != "SOLD":
        try:
            from snipe import token_monitor_manager
            if token_monitor_manager is not None:
                token_monitor_manager.remove_token(token_address)
        except Exception as e:
            file_logger.error(f"Error removing token from monitor: {str(e)}")
