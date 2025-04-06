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

from config import logger, file_logger, event_filter, minimum_sleep, w3, Web3
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

def main(percentage_for_amount_in, verbosity, min_safety_score, min_balance=0.002, resume_balance=0.004):
    config.initialize_logging(verbosity)
    percentage_for_amount_in /= 100
    config.initialize_credentials()

    global balance_manager, token_monitor_manager
    balance_manager = BalanceManager(w3, min_balance_threshold=min_balance, resume_balance_threshold=resume_balance)
    token_monitor_manager = TokenMonitorManager(w3, balance_manager)

    logger.info("Sniping Started...")
    logger.info(f"Balance management enabled: Pause at {min_balance} WBNB, Resume at {resume_balance} WBNB")

    balance_wei = balance_manager.get_balance()
    balance_eth = Web3.from_wei(balance_wei, 'ether')
    logger.info(f"Initial balance: {balance_eth} WBNB")

    global event_filter
    event_filter = config.event_filter

    while True:
        try:
            events = event_filter.get_new_entries()

            if events:
                for event in events:
                    event_queue.put(event)
                file_logger.info(f"Queue size: {event_queue.qsize()}")

            while not event_queue.empty():
                file_logger.debug("Processing an event...")
                handle_event(event_queue.get(), percentage_for_amount_in, min_safety_score)
                file_logger.debug("Event processed.")

            sleep_duration = max(minimum_sleep, event_queue.qsize())
            time.sleep(sleep_duration)

        except Exception as e:
            logger.error(f"An error occurred, Check Log File")
            file_logger.error(f"An error occurred: {str(e)}")
            if 'filter not found' in str(e):
                file_logger.info("Recreating event filter...")
                event_filter = recreate_event_filter()

        except KeyboardInterrupt:
            logger.info(f"Sniping Ended @ {time.strftime('%H:%M:%S /%Y-%m-%d/', time.localtime())}")
            exit(0)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--p', type=float, required=True, help='Percentage of wallet balance to use for token purchase (e.g., 1 for 1%)')
    parser.add_argument('--score', type=float, required=False, default=100, help='Minimum safety score to proceed with a token (e.g., 100 for 100%).')
    parser.add_argument('--v', type=int, choices=[1, 2], default=1, help='Verbosity level. 1 for default, and 2 for showing all logs.')
    parser.add_argument('--min-balance', type=float, required=False, default=0.002, help='Minimum balance in WBNB to continue operations (default 0.002 WBNB)')
    parser.add_argument('--resume-balance', type=float, required=False, default=0.004, help='Balance in WBNB to resume operations (default 0.004 WBNB)')
    args = parser.parse_args()
    main(args.p, args.v, args.score, args.min_balance, args.resume_balance)
