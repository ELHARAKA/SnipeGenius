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

from config import trade_logger, event_filter, minimum_sleep
from imports import logging, time
from transactions import handle_event

def main():
    # Set up logging
    trade_logger.info("Sniping Started, Fetching for new events...")
    is_processing = False

    # Main loop (Events Check & Execute Trades)
    while True:
        if not is_processing:
            try:
                events = event_filter.get_new_entries()

                if events:
                    is_processing = True  # set flag to True when event is found
                    logging.info(f"Found {len(events)} new event(s).")
                    for event in events:
                        handle_event(event)  # Handle each new event
                    is_processing = False  # reset flag to False after handling event

                sleep_duration = max(minimum_sleep, len(events))
                time.sleep(sleep_duration)

            except Exception as e:
                logging.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()
