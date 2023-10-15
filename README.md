# SnipeGenius
SnipeGenius is a PancakeSwap trading bot on the Binance Smart Chain. It automates token buys with features like honeypot detection and gas estimation. It ensures sufficient liquidity, minimizes slippage, and performs dry-run simulations for risk mitigation.


### Core Components Breakdown

- config.py: Configures SnipeGenius for BSC, wallet, and 'PairCreated' event monitoring etc...
- api.py: Retrieves token ABI and balance data from BSC for sell simulation and balance checks.
- imports.py: Imports essential libraries for web3 connectivity and logging.
- snipegenius.py: Performs safety assessments for tokens before trading on PancakeSwap.
- transactions: Handles new token pairs on PancakeSwap, performs safety checks, and executes buy transactions.
- snipe.py: Initiates SnipeGenius, monitors, and handles PancakeSwap events.
- (wbnb,router,factory,pair): These ABIs enable SnipeGenius to interact with PancakeSwap's Factory, Router, WBNB, and Pair contracts.
- blacklist.txt: Tokens owned by blacklisted addresses are skipped during transactions.
- trade_history.log: is SnipeGenius' trade log, recording trade-related data and events
