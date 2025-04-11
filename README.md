<p align="center">
  <img src="https://i.ibb.co/4ZYSN1q7/Snipe-Genius-Bot.png" alt="SnipeGenius" width="600" style="max-height: 200px;">
</p>

# SnipeGenius (V3.0)

SnipeGenius is an advanced sniping bot designed to monitor newly created trading pair events on PancakeSwap. Upon detection, it conducts a series of comprehensive safety inspections to identify potential risks like honeypots, rug pulls, or transaction taxes. Following these checks, SnipeGenius runs buy/sell simulations to assess risks further before executing a purchase. The bot also features intelligent exit strategies to maximize profits and minimize losses.

* Note: Currently, the only supported DEX is PancakeSwap, with plans to include more in the future. Safety checks within the system are continually being enhanced to ensure secure transactions. As we expand to support additional DEX platforms, our focus on robust safety measures remains a top priority to provide a reliable and secure trading experience for our users.

---

## Core Components Breakdown

| File | Description |
|------|-------------|
| **config.py** | Sets up logging, displays startup banner, and initializes Binance Smart Chain connection |
| **coinOps.py** | Manages token operations: balance retrieval, token info, BNB/WBNB conversions |
| **wallet.py** | Handles secure encryption, storage, and retrieval of wallet credentials |
| **snipegenius.py** | Performs safety checks using GoPlus API and calculates token security scores |
| **transactions.py** | Executes buy transactions with multi-slippage logic (1%, 5%, 10%) |
| **exit_strategy.py** | Implements dynamic exit strategies to protect profits and minimize losses |
| **balance_manager.py** | Auto-pauses and resumes trading based on wallet balance thresholds |
| **snipe.py** | Main bot logic: initializes the system and monitors for new token pairs |

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

## Usage

SnipeGenius supports several command-line parameters to customize its behavior:

1. **--p**: (Required) Specifies the trade amount percentage of your wallet balance, e.g., 5 represents 5%.
2. **--score**: (Optional) Sets the minimum safety score for a token; for example, 90 means 90%. (Default: 100)
   * It's recommended to keep the --score above 75 to avoid the risk of encountering a fraudulent token and losing your money.
3. **--v**: (Optional) Sets the verbosity level (Default: 1)
   * Level 1: Shows INFO level logs in the console
   * Level 2: Shows DEBUG level logs in the console (comprehensive logs for debugging)
   * Note: All logs (regardless of console verbosity) are always saved to "trade_history.log"
4. **--min-balance**: (Optional) Sets the minimum BNB balance threshold to pause operations (default: 0.002 BNB).
5. **--resume-balance**: (Optional) Sets the BNB balance threshold to resume operations (default: 0.004 BNB).
6. **--mode**: (Optional) Sets the trading mode (default: 1)
   * Mode 1: Default behavior - continuously monitors for new pairs and can buy multiple tokens simultaneously
   * Mode 2: Pauses monitoring for new pairs after buying a token until it's sold - focuses on one token at a time
7. **--sell-time**: (Optional) Overrides the default exit strategy with a time-based exit (in minutes)
   * Example: `--sell-time 5` will sell the token after 5 minutes regardless of price

### Example Commands

Default settings:

```python
python3 snipe.py --p 5 --score 90
```

With balance management thresholds:

```python
python3 snipe.py --p 5 --score 90 --min-balance 0.002 --resume-balance 0.004
```

Using trading mode 2 (focus on one token at a time):

```python
python3 snipe.py --p 5 --score 90 --mode 2
```

With time-based exit strategy (sell after 10 minutes):

```python
python3 snipe.py --p 5 --score 90 --sell-time 10
```

Complete logs for debugging:

```python
python3 snipe.py --p 5 --score 90 --v 2
```

## Advanced Features

### Intelligent Exit Strategy

| Phase | Description |
|-------|-------------|
| **Initial Monitoring (4 min)** | • Profit at 10% gain<br>• Stop loss at 10% loss<br>• Trailing stop of 5% from peak price |
| **Dynamic Protection Mode (5 min)** | • Profit at 20% gain with 3% trailing<br>• Profit at 50%+ gain<br>• Trailing stop of 5% from peak<br>• Stop loss at 15% |
| **Tiered Smart Exit** | • Sell 25% at 1.5x buy<br>• Sell 25% at 2x buy<br>• Sell 25% at 3x buy<br>• Trailing stop of 7% from peak<br>• Sell remainder after 15 min |

### Time-Based Exit Strategy

In addition to the intelligent exit strategy, SnipeGenius supports a time-based exit option:

* Set a specific time period after which the token will be sold regardless of price
* Useful for quick trades or when you want to ensure tokens are sold within a certain timeframe
* Can be enabled with the `--sell-time` parameter followed by the number of minutes
* Attempts to sell with increasing slippage (1%, 3%, 5%, 10%) if initial sell attempts fail

### Trading Modes

SnipeGenius offers two trading modes to suit different strategies:

| Mode | Description |
|------|-------------|
| **Mode 1 (Default)** | • Continuously monitors for new token pairs<br>• Can buy multiple tokens simultaneously |
| **Mode 2** | • Focuses on one token at a time<br>• Pauses monitoring after a buy until token is sold<br>• Ideal for focused trading<br>• Reduces capital spread risk |

### Balance Management

The bot automatically manages your wallet balance:

* Pauses new purchases when BNB balance falls below the minimum threshold (default: 0.002 BNB).
* Automatically resumes operations when balance is replenished above the resume threshold (default: 0.004 BNB).
* Provides notifications when balance thresholds are crossed.

### Token Safety Checks

SnipeGenius performs extensive safety checks on tokens before purchasing:

| Check Type | Description |
|------------|-------------|
| Pre-check verification | Ensures contract is verified on BSCScan and does not contain suspicious functions |
| GoPlus API Security Analysis | Multiple factors checked:<br>• Honeypot detection (automatic rejection)<br>• Cannot sell all (-90 points)<br>• Cannot buy (-80 points)<br>• Blacklist detection (-70 points)<br>• Hidden owner (-60 points)<br>• Take-back ownership (-50 points)<br>• Self-destruct code (-50 points)<br>• Buy/sell tax (-10 to -40 points)<br>• Mintable token (-30 points)<br>• Transfer pausable (-30 points)<br>• Proxy contract (-25 points)<br>• Trading cooldown (-20 points)<br>• Slippage modification (-40 points)<br>• Personal slippage mod (-30 points)<br>• Non-open source (-20 points)<br>• Not in DEX (-15 points)<br>• Trust list (+10 points) |

Each safety factor contributes to an overall security score, which must meet or exceed your specified minimum score (--score parameter) for the purchase to proceed.

### Logging System

SnipeGenius implements a comprehensive logging system:

* **Console Logs**:
  * Level 1 (default): Shows INFO level and above messages with color coding
  * Level 2: Shows DEBUG level and above messages for detailed debugging

* **File Logs**:
  * All logs (regardless of verbosity level) are saved to "trade_history.log"
  * Contains complete transaction history, token details, and system operations

* **Color-Coded Output**:
  * INFO (green): Normal operations and success messages
  * WARNING (yellow): Important alerts and potential issues
  * ERROR (red): Critical issues and failures
  * DEBUG (cyan): Detailed technical information (only shown with --v 2)

## Run and Setup

* Upon code execution, you'll be prompted to enter wallet details.

1. Run `python3 snipe.py --p 5 --score 90` (Adjust parameters as needed)
2. Input wallet address, private key, and BSCScan API key. Details are saved encrypted in wallet.txt locally.

## Important Note

This tool does not come with any warranty to anyone that they will make a profit, and we shall take no responsibility for any financial loss. Trading cryptocurrencies involves significant risk and can result in the loss of your invested capital. You should not invest more than you can afford to lose and should ensure that you fully understand the risks involved.

### 📜 License

SnipeGenius is proprietary, source-available software. Personal use is permitted, but resale, redistribution, and offering it as a service are strictly prohibited.

Please review the [LICENSE](https://github.com/ELHARAKA/SnipeGenius/blob/main/LICENSE) for full terms.
A plain-English summary is available in [LICENSE-EXPLAINED.md](https://github.com/ELHARAKA/SnipeGenius/blob/main/LICENSE-EXPLAINED.md).

### ☕️ Support the Developer

Support the project and help push it forward with a donation

| Network | Address | Badge | QR |
|---------|---------|--------|----|
| **EVM Chains** _(ETH, BSC, Polygon, etc.)_ | `0x9f05c48003747eB6A5cC9C874cbE00Df75699673` | ![Donate ETH](https://img.shields.io/badge/Donate-ETH-blueviolet?logo=ethereum) | ![ETH QR](assets/eth-qr.png) |
| **Bitcoin (BTC)** | `bc1qvn7e76ecl3uann6gash5zvr645nd2fav6hqzmd` | ![Donate BTC](https://img.shields.io/badge/Donate-BTC-orange?logo=bitcoin) | ![BTC QR](assets/btc-qr.png) |

> ✅ _EVM address supports all Ethereum-compatible tokens._
