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

from config import w3, wbnb, file_logger

def get_token_balance(tokentobuy):
    from config import my_address
    abi = [{
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    }]
    token_contract = w3.eth.contract(address=tokentobuy, abi=abi)
    balance = token_contract.functions.balanceOf(my_address).call()
    return balance

def get_token_info(token_address):
    from config import w3, token_abi

    try:
        token_contract = w3.eth.contract(address=token_address, abi=token_abi)

        name = token_contract.functions.name().call()
        symbol = token_contract.functions.symbol().call()
        decimals = token_contract.functions.decimals().call()
        total_supply = token_contract.functions.totalSupply().call()

        return {
            "name": name,
            "symbol": symbol,
            "decimals": decimals,
            "total_supply": total_supply
        }
    except Exception as e:
        file_logger.error(f"Error getting token info: {str(e)}")
        return {
            "name": "Unknown",
            "symbol": "Unknown",
            "decimals": 18,
            "total_supply": 0
        }

def get_wbnb_balance():
    from config import my_address
    balance = wbnb.functions.balanceOf(my_address).call()

    import sys
    if 'balance_manager' in sys.modules and 'balance_manager' in globals():
        try:
            from snipe import balance_manager
            if balance_manager is not None:
                balance_manager.update_balance()
        except Exception as e:
            file_logger.error(f"Error updating balance manager: {str(e)}")

    return balance

def get_bnb_balance():
    from config import my_address, w3
    return w3.eth.get_balance(my_address)

def ensure_wbnb_balance(amount_needed):
    from config import my_address, private_key, w3, wbnb, logger, file_logger

    wbnb_balance = get_wbnb_balance()
    file_logger.info(f"Current WBNB balance: {w3.from_wei(wbnb_balance, 'ether')} WBNB")

    if wbnb_balance >= amount_needed:
        return True

    bnb_balance = get_bnb_balance()
    file_logger.info(f"Current BNB balance: {w3.from_wei(bnb_balance, 'ether')} BNB")
    amount_to_convert = min(bnb_balance - w3.to_wei(0.005, 'ether'), amount_needed - wbnb_balance)

    if amount_to_convert <= 0:
        logger.error(f"Insufficient BNB to convert to WBNB. Need {w3.from_wei(amount_needed - wbnb_balance, 'ether')} more WBNB")
        return False

    try:
        logger.info(f"Converting {w3.from_wei(amount_to_convert, 'ether')} BNB to WBNB...")

        txn = {
            'from': my_address,
            'to': wbnb.address,
            'value': amount_to_convert,
            'gas': 50000,
            'gasPrice': w3.eth.gas_price,
            'nonce': w3.eth.get_transaction_count(my_address),
            'chainId': 56
        }

        signed_txn = w3.eth.account.sign_transaction(txn, private_key)
        txn_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
        receipt = w3.eth.wait_for_transaction_receipt(txn_hash)

        if receipt.status == 1:
            logger.info(f"Successfully converted BNB to WBNB")
            new_balance = get_wbnb_balance()
            file_logger.info(f"New WBNB balance: {w3.from_wei(new_balance, 'ether')} WBNB")
            return new_balance >= amount_needed
        else:
            logger.error("Failed to convert BNB to WBNB")
            return False

    except Exception as e:
        logger.error(f"Error converting BNB to WBNB: {str(e)}")
        file_logger.error(f"Error converting BNB to WBNB: {str(e)}")
        return False
