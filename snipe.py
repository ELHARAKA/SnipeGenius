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
import config
import argparse
from config import logger, file_logger, event_filter, minimum_sleep
from transactions import handle_event
from queue import Queue

event_queue = Queue()

def recreate_event_filter():
    return config.w3.eth.filter({
        'address': config.factory_address,
        'topics': [config.pair_created_topic]
    })

def main(percentage_for_amount_in, verbosity):
    config.initialize_logging(verbosity)
    percentage_for_amount_in /= 100  # Convert percentage to decimal
    config.initialize_credentials()
    logger.info("Sniping Started...")

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
                handle_event(event_queue.get(), percentage_for_amount_in)  # Passed the parameter to handle_event
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
    parser.add_argument('--v', type=int, choices=[1, 2], default=1, help='Verbosity level. 1 for default, and 2 for showing all logs.')
    args = parser.parse_args()
    main(args.p, args.v)
