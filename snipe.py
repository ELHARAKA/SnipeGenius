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

from config import logger, event_filter, minimum_sleep, w3, Web3
from transactions import handle_event
import time, config, argparse
from queue import Queue
from balance_manager import BalanceManager, TokenMonitorManager

event_queue = Queue()

def recreate_event_filter():
    return config.w3.eth.filter({
        'address': config.factory_address,
        'topics': [config.pair_created_topic]
    })

balance_manager = None
token_monitor_manager = None
__all__ = ['token_monitor_manager', 'balance_manager']

def main(percentage_for_amount_in, verbosity, min_safety_score, min_balance=0.002, resume_balance=0.004, mode=1, sell_time=None):
    config.initialize_logging(verbosity)
    percentage_for_amount_in /= 100
    config.initialize_credentials()
    global balance_manager, token_monitor_manager
    balance_manager = BalanceManager(w3, min_balance_threshold=min_balance, resume_balance_threshold=resume_balance)
    token_monitor_manager = TokenMonitorManager(w3, balance_manager)

    import builtins
    setattr(builtins, 'token_monitor_manager', token_monitor_manager)
    setattr(builtins, 'balance_manager', balance_manager)

    logger.debug("Balance manager and token monitor manager initialized successfully")
    logger.info("Sniping Started...")
    logger.debug(f"Balance management enabled: Pause at {min_balance} BNB, Resume at {resume_balance} BNB")

    if mode == 2:
        logger.info("Trading Mode 2: Will pause buying new tokens until current token is sold")

    if sell_time is not None:
        logger.info(f"Time-based selling enabled: Will sell tokens after {sell_time} minutes")

    balance_wei = balance_manager.get_balance()
    balance_eth = Web3.from_wei(balance_wei, 'ether')
    logger.info(f"Initial balance: {balance_eth} BNB")
    global event_filter
    event_filter = config.event_filter

    last_mode2_log_time = 0
    last_token_count = 0
    mode2_log_interval = 60

    while True:
        try:
            if mode == 2:
                active_tokens = token_monitor_manager.get_active_tokens()
                current_token_count = len(active_tokens) if active_tokens else 0
                current_time = time.time()

                if (current_time - last_mode2_log_time >= mode2_log_interval or
                    current_token_count != last_token_count):

                    if active_tokens and current_token_count > 0:
                        token_addresses = ", ".join(active_tokens[:3])
                        if current_token_count > 3:
                            token_addresses += f" and {current_token_count - 3} more"

                        logger.info(f"Mode 2: Currently monitoring {current_token_count} tokens [{token_addresses}]. Pausing new pair discovery.")
                    elif last_token_count > 0:
                        logger.info("Mode 2: No more tokens being monitored. Resuming new pair discovery.")

                    last_mode2_log_time = current_time
                    last_token_count = current_token_count

                if active_tokens and current_token_count > 0:
                    queue_size = event_queue.qsize()
                    if queue_size > 0:
                        logger.info(f"Mode 2: Clearing event queue with {queue_size} pending events")
                        while not event_queue.empty():
                            event_queue.get()

                    time.sleep(minimum_sleep)
                    continue

            events = event_filter.get_new_entries()

            if events:
                for event in events:
                    event_queue.put(event)

            while not event_queue.empty():
                logger.debug("Processing an event...")
                if mode == 2:
                    active_tokens = token_monitor_manager.get_active_tokens()
                    current_token_count = len(active_tokens) if active_tokens else 0

                    if active_tokens and current_token_count > 0:
                        current_time = time.time()
                        if current_time - last_mode2_log_time >= mode2_log_interval:
                            token_addresses = ", ".join(active_tokens[:3])
                            if current_token_count > 3:
                                token_addresses += f" and {current_token_count - 3} more"
                            logger.info(f"Mode 2: Currently monitoring {current_token_count} tokens [{token_addresses}]. Skipping event processing.")
                            last_mode2_log_time = current_time

                        queue_size = event_queue.qsize()
                        if queue_size > 0:
                            logger.info(f"Mode 2: Clearing event queue with {queue_size} pending events")
                            while not event_queue.empty():
                                event_queue.get()
                        break

                handle_event(event_queue.get(), percentage_for_amount_in, min_safety_score, mode, sell_time)
                logger.debug("Event processed.")

            sleep_duration = max(minimum_sleep, event_queue.qsize())
            time.sleep(sleep_duration)

        except Exception as e:
            logger.error(f"An error occurred: {str(e)}")
            if 'filter not found' in str(e):
                logger.info("Recreating event filter...")
                event_filter = recreate_event_filter()

        except KeyboardInterrupt:
            logger.info(f"Sniping Ended @ {time.strftime('%H:%M:%S /%Y-%m-%d/', time.localtime())}")
            exit(0)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--p', type=float, required=True, help='Percentage of wallet balance to use for token purchase (e.g., 1 for 1%)')
    parser.add_argument('--score', type=float, required=False, default=100, help='Minimum safety score to proceed with a token (e.g., 100 for 100%).')
    parser.add_argument('--v', type=int, choices=[1, 2], default=1, help='Verbosity level. 1 for default, and 2 for showing all logs.')
    parser.add_argument('--min-balance', type=float, required=False, default=0.002, help='Minimum balance in BNB to continue operations (default 0.002 BNB)')
    parser.add_argument('--resume-balance', type=float, required=False, default=0.004, help='Balance in BNB to resume operations (default 0.004 BNB)')
    parser.add_argument('--mode', type=int, choices=[1, 2], default=1, help='Trading mode: 1 for default behavior, 2 to pause listening for new pairs after buying until token is sold')
    parser.add_argument('--sell-time', type=float, required=False, help='Override default selling logic with time-based exit (in minutes)')
    args = parser.parse_args()
    main(args.p, args.v, args.score, args.min_balance, args.resume_balance, args.mode, args.sell_time)
