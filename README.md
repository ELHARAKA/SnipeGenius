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

## Contribution
We warmly welcome contributions from the community. Whether you are a veteran developer or a newcomer, your input is highly valued. Here are some ways you can contribute to SnipeGenius:

* Bug Reporting: If you encounter any bugs or issues, please create an issue on GitHub detailing the problem, and if possible, steps to reproduce it.
* Feature Suggestions: Have a feature in mind? Open an issue to suggest new features or enhancements.
* Code: Feel free to fork SnipeGenius and submit your pull requests. We appreciate your effort to help improve the codebase.
* Documentation: Help us improve the documentation to make SnipeGenius more accessible to the community. Whether it's typo corrections or whole tutorials, your contributions are crucial.
* Testing: Assist us in improving the stability and reliability of SnipeGenius by testing it in different environments and reporting any problems.
* Before contributing, please ensure you have read and understood the contribution guidelines and code of conduct to maintain a healthy and inclusive community environment. Thank you for your interest in improving SnipeGenius!
