<p align="center">
  <img src="https://i.ibb.co/PYsK1cr/snpepancakegenius-fotor-bg-remover-2023-2024102611743.png" alt="SnipeGenius">
</p>

# SnipeGenius
SnipeGenius is a sniping bot designed to monitor newly created trading pair events. Upon detection, it conducts a series of safety inspections to identify potential risks like honeypots, rug pulls, or transaction taxes. Following these checks, SnipeGenius runs buy/sell simulations to assess risks further before executing a purchase.

* Note: Currently, the only supported DEX is PancakeSwap, with plans to include more in the future. Safety checks within the system are continually being enhanced to ensure secure transactions. As i expand to support additional DEX platforms, my focus on robust safety measures remains a top priority to provide a reliable and secure trading experience for our users.


---
## Core Components Breakdown
- config.py: Sets up logging, displays startup banner, and initializes connections to Binance Smart Chain.
###
- coinOps.py: Retrieves specified token and WBNB balances for a given address.
###
- wallet.py: Handles encryption, storage, and retrieval of wallet and TokenSniffer API credentials.
###
- snipegenius.py: Conducts safety checks on tokens.
###
- transactions.py: Manages and executes buy transactions on new token pairs.
###
- snipe.py: Initiates SnipeGenius.

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
pip3 install -r requirements.txt
```
* Note: If you encounter any errors related to the pwinput package, execute the following command to resolve the issue:
```python
  sudo python3 -m pip install pwinput
```

### Usage:
1. The --p param is crucial for specifying the trade amount percentage, e.g., 5 represents 5%.
2. The --s param is optional and sets the minimum safety score for a token; for example, 100 means 100%. (Default: 100)
   * It's recommended to keep the --score above 75 to avoid the risk of encountering a fraudulent token and losing your money.
3. The --v param is optional and sets the verbosity level. Use 2 for complete logs, but it's advised only for debugging.
   * Complete logs can be found in "trade_history.log".

  Defaul Logs:
  ```bash
  python3 snipe.py --p 5 --score 100
  ```

  Complete Logs:
  ```bash
  python3 snipe.py --p 5 --score 75 --v 2
  ```

### Run and Setup
* Upon code execution, you'll be prompted to enter wallet details and TokenSniffer API key.
1. Run `python3 snipe.py --p 1` (Replace 1 with your desired value)
2. Input wallet address, private key, and encryption password. Details saved encrypted in wallet.txt locally.
3. Input TokenSniffer API key
   * Note: To obtain your TokenSniffer API Key, follow these instructions [TokenSniffer API](https://tokensniffer.com/TokenSnifferAPI)


## License
SnipeGenius is proprietary software. The use, distribution, and modification of this software is governed by the license agreement provided in the [LICENSE](https://github.com/ELHARAKA/SnipeGenius/blob/main/LICENSE) file in this repository.

## Donations
* If this tool helped in any way, consider making a donation to support the developer:

1. ETH/BSC/POLY: 0x9f05c48003747eB6A5cC9C874cbE00Df75699673
2. BTC Address:  bc1q6zf7gxr7xqktv7gqdt7k9nawq8mu0xs99xrzrf
