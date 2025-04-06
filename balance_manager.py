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

from web3 import Web3
from config import logger, file_logger
import threading

class BalanceManager:
    def __init__(self, w3, min_balance_threshold=0.002, resume_balance_threshold=0.004):
        """
        Initialize the balance manager with thresholds in WBNB

        Args:
            w3: Web3 instance
            min_balance_threshold: Minimum balance in WBNB to continue operations (default 0.002 WBNB)
            resume_balance_threshold: Balance in WBNB to resume operations (default 0.004 WBNB)
        """
        self.w3 = w3
        self.min_balance_threshold = Web3.to_wei(min_balance_threshold, 'ether')
        self.resume_balance_threshold = Web3.to_wei(resume_balance_threshold, 'ether')
        self.is_paused = False
        self.current_balance_wei = 0
        self.lock = threading.Lock()

        self.update_balance()

    def update_balance(self):
        """Update the current balance and check if we need to pause/resume"""
        from coinOps import get_wbnb_balance, get_bnb_balance

        with self.lock:
            self.current_balance_wei = get_wbnb_balance()
            bnb_balance = get_bnb_balance()

            wbnb_eth = Web3.from_wei(self.current_balance_wei, 'ether')
            bnb_eth = Web3.from_wei(bnb_balance, 'ether')
            file_logger.info(f"Current balances - WBNB: {wbnb_eth} WBNB, BNB: {bnb_eth} BNB")

            if not self.is_paused and self.current_balance_wei < self.min_balance_threshold:
                self.is_paused = True
                min_balance_eth = Web3.from_wei(self.min_balance_threshold, 'ether')
                current_balance_eth = Web3.from_wei(self.current_balance_wei, 'ether')
                logger.warning(f"WBNB Balance below {min_balance_eth} WBNB. Pausing new purchases.")
                file_logger.warning(f"WBNB Balance below {min_balance_eth} WBNB ({current_balance_eth} WBNB). Pausing new purchases.")

                if bnb_balance > Web3.to_wei(0.01, 'ether'):
                    logger.info(f"You have {bnb_eth} BNB. Consider converting some to WBNB to continue operations.")
                    file_logger.info(f"You have {bnb_eth} BNB. Consider converting some to WBNB to continue operations.")

            elif self.is_paused and self.current_balance_wei >= self.resume_balance_threshold:
                self.is_paused = False
                resume_balance_eth = Web3.from_wei(self.resume_balance_threshold, 'ether')
                current_balance_eth = Web3.from_wei(self.current_balance_wei, 'ether')
                logger.info(f"WBNB Balance above {resume_balance_eth} WBNB. Resuming operations.")
                file_logger.info(f"WBNB Balance above {resume_balance_eth} WBNB ({current_balance_eth} WBNB). Resuming operations.")

        return self.current_balance_wei

    def can_purchase(self):
        """Check if the bot can make new purchases"""
        self.update_balance()
        return not self.is_paused

    def get_balance(self):
        """Get the current balance in wei"""
        return self.current_balance_wei


class TokenMonitor:
    def __init__(self, w3, token_address, buy_price, token_balance):
        """
        Initialize a token monitor for a specific token

        Args:
            w3: Web3 instance
            token_address: Address of the token to monitor
            buy_price: Price at which the token was bought
            token_balance: Amount of tokens bought
        """
        self.w3 = w3
        self.token_address = token_address
        self.buy_price = buy_price
        self.token_balance = token_balance
        self.is_monitoring = False
        self.thread = None

    def start_monitoring(self):
        """Start monitoring the token in a separate thread"""
        if not self.is_monitoring:
            self.is_monitoring = True
            self.thread = threading.Thread(target=self._monitor_token)
            self.thread.daemon = True
            self.thread.start()
            file_logger.info(f"Started monitoring token {self.token_address}")

    def _monitor_token(self):
        """Monitor the token and execute the exit strategy"""
        from exit_strategy import intelligent_adaptive_liquidation
        try:
            intelligent_adaptive_liquidation(self.token_address, self.buy_price, self.token_balance)
        except Exception as e:
            file_logger.error(f"Error monitoring token {self.token_address}: {str(e)}")
        finally:
            self.is_monitoring = False
            file_logger.info(f"Finished monitoring token {self.token_address}")


class TokenMonitorManager:
    def __init__(self, w3, balance_manager):
        """
        Initialize the token monitor manager

        Args:
            w3: Web3 instance
            balance_manager: BalanceManager instance
        """
        self.w3 = w3
        self.balance_manager = balance_manager
        self.active_monitors = {}
        self.lock = threading.Lock()

    def add_token(self, token_address, buy_price, token_balance):
        """
        Add a token to be monitored

        Args:
            token_address: Address of the token to monitor
            buy_price: Price at which the token was bought
            token_balance: Amount of tokens bought
        """
        with self.lock:
            if token_address not in self.active_monitors:
                monitor = TokenMonitor(self.w3, token_address, buy_price, token_balance)
                self.active_monitors[token_address] = monitor
                monitor.start_monitoring()
                logger.info(f"Added token {token_address} to monitoring")
                self.balance_manager.update_balance()

    def remove_token(self, token_address):
        """
        Remove a token from monitoring

        Args:
            token_address: Address of the token to remove
        """
        with self.lock:
            if token_address in self.active_monitors:
                del self.active_monitors[token_address]
                logger.info(f"Removed token {token_address} from monitoring")
                self.balance_manager.update_balance()

    def get_active_tokens(self):
        with self.lock:
            return list(self.active_monitors.keys())
