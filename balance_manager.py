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

from web3 import Web3
from config import logger
import threading
import time

class BalanceManager:
    def __init__(self, w3, min_balance_threshold=0.002, resume_balance_threshold=0.004):
        self.w3 = w3
        self.min_balance_threshold = Web3.to_wei(min_balance_threshold, 'ether')
        self.resume_balance_threshold = Web3.to_wei(resume_balance_threshold, 'ether')
        self.is_paused = False
        self.current_balance_wei = 0
        self.lock = threading.Lock()
        self.update_balance()

    def update_balance(self):
        from coinOps import get_bnb_balance

        with self.lock:
            self.current_balance_wei = get_bnb_balance()

            if not self.is_paused and self.current_balance_wei < self.min_balance_threshold:
                self.is_paused = True
                min_balance_eth = Web3.from_wei(self.min_balance_threshold, 'ether')
                current_balance_eth = Web3.from_wei(self.current_balance_wei, 'ether')
                logger.warning(f"BNB Balance below {min_balance_eth} BNB ({current_balance_eth} BNB). Pausing new purchases.")

            elif self.is_paused and self.current_balance_wei >= self.resume_balance_threshold:
                self.is_paused = False
                resume_balance_eth = Web3.from_wei(self.resume_balance_threshold, 'ether')
                current_balance_eth = Web3.from_wei(self.current_balance_wei, 'ether')
                logger.info(f"BNB Balance above {resume_balance_eth} BNB ({current_balance_eth} BNB). Resuming operations.")

        return self.current_balance_wei

    def can_purchase(self):
        self.update_balance()
        return not self.is_paused

    def get_balance(self):
        return self.current_balance_wei

class TokenMonitor:
    def __init__(self, w3, token_address, buy_price, token_balance, sell_time=None):
        self.w3 = w3
        self.token_address = token_address
        self.buy_price = buy_price
        self.token_balance = token_balance
        self.sell_time = sell_time
        self.is_monitoring = False
        self.thread = None
        self.purchase_time = time.time()
        self.sold = False
        self.sold_event = threading.Event()

    def start_monitoring(self):
        if not self.is_monitoring:
            self.is_monitoring = True
            self.thread = threading.Thread(target=self._monitor_token)
            self.thread.daemon = True
            self.thread.start()
            logger.info(f"Started monitoring token {self.token_address}")

    def _monitor_token(self):
        from exit_strategy import intelligent_adaptive_liquidation, time_based_exit
        from config import my_address, initialize_credentials

        try:
            if not my_address:
                logger.debug("Wallet address not initialized. Initializing credentials...")
                initialize_credentials()
                from config import my_address
                if not my_address:
                    logger.error("Failed to initialize wallet address. Cannot monitor token.")
                    return
                logger.debug(f"Wallet address initialized: {my_address}")

            if self.sell_time is not None:
                logger.info(f"Using time-based exit strategy with {self.sell_time} minute(s) timeout for token {self.token_address}")

                start_time = time.time()
                expected_sell_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time + self.sell_time * 60))
                logger.debug(f"Monitor thread: Will initiate sell of {self.token_address} at approximately {expected_sell_time}")
                result = time_based_exit(self.token_address, self.buy_price, self.token_balance, self.sell_time)
                logger.info(f"Time-based exit result for {self.token_address}: {result}")

                if result == "SOLD":
                    self.sold = True
                    self.sold_event.set()
                    logger.info(f"TokenMonitor: Token {self.token_address} marked as sold after {self.sell_time} minutes")

                    try:
                        import builtins
                        if hasattr(builtins, 'token_monitor_manager'):
                            token_monitor_manager = builtins.token_monitor_manager
                            token_monitor_manager.remove_token(self.token_address)
                            logger.debug(f"TokenMonitor: Token {self.token_address} explicitly removed from monitoring")
                    except Exception as e:
                        logger.debug(f"TokenMonitor: Could not explicitly remove token: {str(e)}")
                else:
                    logger.warning(f"TokenMonitor: Token {self.token_address} could not be sold after {self.sell_time} minutes, exit result: {result}")
            else:
                result = intelligent_adaptive_liquidation(self.token_address, self.buy_price, self.token_balance, None)
                if result == "SOLD":
                    self.sold = True
                    self.sold_event.set()

                    try:
                        import builtins
                        if hasattr(builtins, 'token_monitor_manager'):
                            token_monitor_manager = builtins.token_monitor_manager
                            token_monitor_manager.remove_token(self.token_address)
                            logger.debug(f"TokenMonitor: Token {self.token_address} explicitly removed from monitoring")
                    except Exception as e:
                        logger.debug(f"TokenMonitor: Could not explicitly remove token: {str(e)}")
        except Exception as e:
            logger.error(f"Error monitoring token {self.token_address}: {str(e)}")
        finally:
            self.is_monitoring = False
            logger.debug(f"Finished monitoring token {self.token_address}")


class TokenMonitorManager:
    def __init__(self, w3, balance_manager):
        self.w3 = w3
        self.balance_manager = balance_manager
        self.active_monitors = {}
        self.lock = threading.Lock()

    def add_token(self, token_address, buy_price, token_balance, sell_time=None):
        with self.lock:
            if token_address not in self.active_monitors:
                monitor = TokenMonitor(self.w3, token_address, buy_price, token_balance, sell_time)
                self.active_monitors[token_address] = monitor
                monitor.start_monitoring()
                logger.info(f"Added token {token_address} to monitoring")
                self.balance_manager.update_balance()

    def remove_token(self, token_address):
        with self.lock:
            if token_address in self.active_monitors:
                del self.active_monitors[token_address]
                logger.debug(f"Removed token {token_address} from monitoring")
                self.balance_manager.update_balance()

    def get_active_tokens(self):
        with self.lock:
            active_tokens = []
            for token_address, monitor in list(self.active_monitors.items()):
                if monitor.sold or monitor.sold_event.is_set():
                    del self.active_monitors[token_address]
                    logger.debug(f"Removed sold token {token_address} from monitoring")
                    self.balance_manager.update_balance()
                else:
                    active_tokens.append(token_address)
            return active_tokens
