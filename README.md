<p align="center">
  <img src="https://i.ibb.co/PYsK1cr/snpepancakegenius-fotor-bg-remover-2023-2024102611743.png" alt="SnipeGenius">
</p>

# SnipeGenius

SnipeGenius is an advanced sniping bot designed to monitor newly created trading pair events on PancakeSwap. Upon detection, it conducts a series of comprehensive safety inspections to identify potential risks like honeypots, rug pulls, or transaction taxes. Following these checks, SnipeGenius runs buy/sell simulations to assess risks further before executing a purchase. The bot also features intelligent exit strategies to maximize profits and minimize losses.

* Note: Currently, the only supported DEX is PancakeSwap, with plans to include more in the future. Safety checks within the system are continually being enhanced to ensure secure transactions. As we expand to support additional DEX platforms, our focus on robust safety measures remains a top priority to provide a reliable and secure trading experience for our users.

---

## Core Components Breakdown

* **config.py**: Sets up logging, displays startup banner, and initializes connections to Binance Smart Chain.
* **coinOps.py**: Manages token operations including retrieving token balances, token information, and handling BNB/WBNB conversions.
* **wallet.py**: Handles encryption, storage, and retrieval of wallet credentials with secure password protection.
* **snipegenius.py**: Conducts comprehensive safety checks on tokens using the GoPlus API to calculate security scores.
* **transactions.py**: Manages and executes buy transactions on new token pairs with multiple slippage levels.
* **exit_strategy.py**: Implements a three-phase intelligent exit strategy for maximizing profits and minimizing losses.
* **balance_manager.py**: Manages wallet balances with automatic pausing when balance is low and resuming when sufficient.
* **snipe.py**: Main entry point that initializes the bot and monitors for new token pairs.

## Setup & Usage

```Make sure Python 3.x is installed on your machine.```

* Clone the SnipeGenius repository:

```bash
git clone https://github.com/ELHARAKA/SnipeGenius.git
```

* Navigate to the SnipeGenius directory:

```bash
cd SnipeGenius
```

* Install the necessary Python libraries:

```python
pip3 install -r requirements.txt
```

* Note: If you encounter any errors related to the pwinput package, execute the following command to resolve the issue:

```python
sudo python3 -m pip install pwinput
```

## Usage

SnipeGenius supports several command-line parameters to customize its behavior:

1. **--p**: (Required) Specifies the trade amount percentage of your wallet balance, e.g., 5 represents 5%.
2. **--score**: (Optional) Sets the minimum safety score for a token; for example, 90 means 90%. (Default: 100)
   * It's recommended to keep the --score above 75 to avoid the risk of encountering a fraudulent token and losing your money.
3. **--v**: (Optional) Sets the verbosity level. Use 2 for complete logs, but it's advised only for debugging.
   * Complete logs can be found in "trade_history.log".
4. **--min-balance**: (Optional) Sets the minimum WBNB balance threshold to pause operations (default: 0.002 WBNB).
5. **--resume-balance**: (Optional) Sets the WBNB balance threshold to resume operations (default: 0.004 WBNB).

### Example Commands

Default settings:

```python
python3 snipe.py --p 5 --score 90
```

With balance management thresholds:

```python
python3 snipe.py --p 5 --score 90 --min-balance 0.002 --resume-balance 0.004
```

Complete logs for debugging:

```python
python3 snipe.py --p 5 --score 90 --v 2
```

## Advanced Features

### Intelligent Exit Strategy

SnipeGenius implements a sophisticated three-phase exit strategy:

1. **Initial Monitoring (3 minutes)**: Quick profit-taking or stop-loss with aggressive parameters.
2. **Dynamic Protection Mode (5 minutes)**: Balanced approach with profit targets and trailing stops.
3. **Tiered Smart Exit**: Sells portions of holdings at different profit targets (1.5x, 2x, 3x).

### Balance Management

The bot automatically manages your wallet balance:

* Pauses new purchases when WBNB balance falls below the minimum threshold (default: 0.002 WBNB).
* Automatically resumes operations when balance is replenished above the resume threshold (default: 0.004 WBNB).
* Provides notifications when BNB needs to be converted to WBNB.

### Token Safety Checks

SnipeGenius performs extensive safety checks on tokens before purchasing:

* Honeypot detection
* Buy/sell tax analysis
* Contract ownership checks
* Blacklist detection
* Self-destruct code detection
* Mintable token detection
* Transfer pausable detection
* Trading cooldown detection
* Slippage modification detection

Each safety factor contributes to an overall security score, which must meet or exceed your specified minimum score (--score parameter) for the purchase to proceed.

## Run and Setup

* Upon code execution, you'll be prompted to enter wallet details.

1. Run `python3 snipe.py --p 5 --score 90` (Adjust parameters as needed)
2. Input wallet address, private key, and encryption password. Details are saved encrypted in wallet.txt locally.

## Important Note

This tool does not come with any warranty to anyone that they will make a profit, and we shall take no responsibility for any financial loss. Trading cryptocurrencies involves significant risk and can result in the loss of your invested capital. You should not invest more than you can afford to lose and should ensure that you fully understand the risks involved.

### License

SnipeGenius is proprietary software. The use, distribution, and modification of this software is governed by the license agreement provided in the [LICENSE](https://github.com/ELHARAKA/SnipeGenius/blob/main/LICENSE) file in this repository.

### Donations

* If this tool helped in any way, consider making a donation to support the developer:

1. ETH/BSC/POLY: 0x9f05c48003747eB6A5cC9C874cbE00Df75699673
2. BTC Address:  bc1q6zf7gxr7xqktv7gqdt7k9nawq8mu0xs99xrzrf
