<p align="center">
  <img src="https://i.ibb.co/fSc0xXb/web3dev-ma-snipegenius-py.png" alt="SnipeGenius">
</p>

# SnipeGenius
SnipeGenius is a sniping bot designed to monitor newly created trading pair events. Upon detection, it conducts a series of safety inspections to identify potential risks like honeypots, rug pulls, or transaction taxes. Following these checks, SnipeGenius runs buy/sell simulations to assess risks further before executing a purchase.

* Note: Currently, the only supported DEX is PancakeSwap, with plans to include more in the future.

---
## Core Components Breakdown
- config.py: Configuration for setting up logs, wallet details, abi, and event listening.
###
- api.py: Retrieves token ABI and balance data from BSC for sell simulation and balance checks.
### 
- imports.py: Imports essential libraries for web3 connectivity and logging. (Will be removed later)
### 
- snipegenius.py: Performs different safety checks for tokens such as honeypot... before buying it. (Safety check accuracy so far is approx 50% so more work needed here in the future)
###
- transactions: Handles new token pairs on PancakeSwap, executes buy transactions.
###
- snipe.py: Initiates SnipeGenius (Main file: python snipe.py)
###
- (wbnb,router,factory,pair): These ABIs enable SnipeGenius to interact with PancakeSwap's Factory, Router, WBNB, and Pair contracts.
###
- blacklist.txt: Tokens owned by blacklisted addresses are skipped during transactions.
###
- trade_history.log: is SnipeGenius' trade log, recording trade-related data and events
