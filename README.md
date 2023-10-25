<p align="center">
  <img src="https://i.ibb.co/fSc0xXb/web3dev-ma-snipegenius-py.png" alt="SnipeGenius">
</p>

# SnipeGenius (V1.5.0 Stable)
SnipeGenius is a sniping bot designed to monitor newly created trading pair events. Upon detection, it conducts a series of safety inspections to identify potential risks like honeypots, rug pulls, or transaction taxes. Following these checks, SnipeGenius runs buy/sell simulations to assess risks further before executing a purchase.

* Note: Currently, the only supported DEX is PancakeSwap, with plans to include more in the future. Safety checks within the system are continually being enhanced to ensure secure transactions. As i expand to support additional DEX platforms, my focus on robust safety measures remains a top priority to provide a reliable and secure trading experience for our users.


---
## Core Components Breakdown
- config.py: Sets up logging, displays startup banner, and initializes connections to Binance Smart Chain.
###
- coinOps.py: Retrieves specified token and WBNB balances for a given address.
### 
- wallet.py: Handles encryption, storage, and retrieval of wallet and Google credentials.
### 
- snipegenius.py: Conducts safety checks on tokens by verifying ownership, checking against a blacklist, analyzing token parameters, performing simulated transactions, and searching for associated risks online.
###
- transactions: Manages and executes buy transactions on new token pairs.
###
- snipe.py: Initiates SnipeGenius.
###
- (wbnb,router,factory,pair): These ABIs enable SnipeGenius to interact with PancakeSwap's Factory, Router, WBNB, and Pair contracts.
###
- blacklist.txt: Tokens owned by blacklisted addresses are skipped during transactions.
###
- trade_history.log: is SnipeGenius' trade log, recording trade-related data, events and errors for debugging.

## Setup & Usage
* Make sure Python 3.x installed on your machine.
1. Clone the SnipeGenius repository:
```
git clone https://github.com/ELHARAKA/SnipeGenius.git
```
2. Navigate to the SnipeGenius directory:
```
cd SnipeGenius
```
3. Install the necessary Python libraries:
```
pip3 install requirements.txt
```
* Note: If you encounter any errors related to the pwinput package, execute the following command to resolve the issue:
```python
  sudo python3 -m pip install pwinput
```

### Usage:
1. The --p parameter is essential to designate the percentage of amount for trade; for instance, 1 denotes 1%.
2. The --v parameter is optional. Use 2 to show all logs. Verbosity level 2 is recommended only for debugging purposes.
   * To debug logs later without passing --v 2, check the log file "trade_history.log".
   ```bash
   sudo python3 snipe.py --p 1
   ```

### Run and Setup
* Upon code execution, you'll be prompted to enter wallet details and Google API key.
1. Run `sudo python3 snipe.py`
2. Input wallet address, private key, and encryption password. Details saved encrypted in wallet.txt locally.
3. Input Google API key and CSE ID.
   * Note: To obtain your Google API Key and CSE ID, follow these instructions [Google API Key](https://developers.google.com/webmaster-tools/search-console-api/v1/configure)

## Contribution
We warmly welcome contributions from the community, in adherence with the [licensing](https://github.com/ELHARAKA/SnipeGenius/blob/main/LICENSE) terms. Whether you are a veteran developer or a newcomer, your input is highly valued. Here are some ways you can contribute to SnipeGenius:

* Bug Reporting: If you encounter any bugs or issues, please create an issue on GitHub detailing the problem, and if possible, steps to reproduce it.
* Feature Suggestions: Have a feature in mind? Open an issue to suggest new features or enhancements.
* Code: Feel free to fork SnipeGenius and submit your pull requests. We appreciate your effort to help improve the codebase.
* Documentation: Help us improve the documentation to make SnipeGenius more accessible to the community. Whether it's typo corrections or whole tutorials, your contributions are crucial.
* Testing: Assist us in improving the stability and reliability of SnipeGenius by testing it in different environments and reporting any problems.
* Before contributing, please ensure you have read and understood the contribution guidelines and code of conduct to maintain a healthy and inclusive community environment. Thank you for your interest in improving SnipeGenius!

## License
SnipeGenius is proprietary software. The use, distribution, and modification of this software is governed by the license agreement provided in the [LICENSE](https://github.com/ELHARAKA/SnipeGenius/blob/main/LICENSE) file in this repository.
