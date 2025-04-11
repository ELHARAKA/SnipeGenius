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

import base64, os, pwinput
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from cryptography.fernet import Fernet, InvalidToken

def generate_key(password: str, salt=None):
    if salt is None:
        salt = os.urandom(16)
    password_bytes = password.encode()
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    key = base64.urlsafe_b64encode(kdf.derive(password_bytes))
    return key, salt

def get_api_key():
    from config import logger
    if os.path.exists("api.txt"):
        try:
            with open("api.txt", "r") as file:
                api_key = file.read().strip()
            return api_key
        except Exception as e:
            logger.error(f"Error reading API key: {e}")
            return ""
    return ""

def save_api_key(api_key):
    from config import logger
    try:
        with open("api.txt", "w") as file:
            file.write(api_key)
        logger.info("BSCScan API key saved to api.txt")
    except Exception as e:
        logger.error(f"Error saving API key: {e}")

def get_credentials():
    from config import logger
    bscscan_api_key = get_api_key()

    if os.path.exists("wallet.txt"):
        incorrect_attempts = 0
        while True:
            password = pwinput.pwinput(prompt="Enter password to decrypt wallet: ")
            key, _ = generate_key(password)
            cipher_suite = Fernet(key)
            with open("wallet.txt", "rb") as file:
                encrypted_data = file.read()
            salt = encrypted_data[:16]
            key, _ = generate_key(password, salt)
            cipher_suite = Fernet(key)
            try:
                decrypted_data = cipher_suite.decrypt(encrypted_data[16:])
                credentials = decrypted_data.decode().split('\n')

                if len(credentials) >= 3:
                    address, private_key, old_api_key = credentials[:3]

                    if not bscscan_api_key and old_api_key:
                        bscscan_api_key = old_api_key
                        save_api_key(bscscan_api_key)

                        key, salt = generate_key(password)
                        cipher_suite = Fernet(key)
                        with open("wallet.txt", "wb") as file:
                            encrypted_data = cipher_suite.encrypt(f'{address}\n{private_key}'.encode())
                            file.write(salt + encrypted_data)
                        logger.debug("Wallet file updated to new format (API key moved to api.txt)")
                elif len(credentials) >= 2:
                    address, private_key = credentials[:2]
                else:
                    logger.error("Invalid wallet data. Please re-import your wallet.")
                    reset_choice = input("Would you like to re-import your wallet? (yes/no): ")
                    if reset_choice.lower() == 'yes':
                        os.remove("wallet.txt")
                        return get_credentials()
                    else:
                        logger.warning("Exiting...")
                        exit(1)

                if not address or len(address) < 40:
                    logger.error(f"Invalid wallet address format: '{address}'. Please re-import your wallet.")
                    reset_choice = input("Would you like to re-import your wallet? (yes/no): ")
                    if reset_choice.lower() == 'yes':
                        os.remove("wallet.txt")
                        return get_credentials()
                    else:
                        logger.warning("Continuing with invalid address. This may cause errors.")

                if not bscscan_api_key:
                    logger.info("BSCScan API key not found. You need to provide it for token safety checks.")
                    bscscan_api_key = input("Enter your BSCScan API key (get one from https://bscscan.com/myapikey): ")
                    save_api_key(bscscan_api_key)

                return address, private_key, bscscan_api_key

            except InvalidToken:
                incorrect_attempts += 1
                if incorrect_attempts >= 5:
                    reset_choice = input("Incorrect password entered 5 times. Would you like to re-import your wallet? (yes/no): ")
                    if reset_choice.lower() == 'yes':
                        os.remove("wallet.txt")
                        return get_credentials()
                    else:
                        logger.warning("Exiting...")
                        exit(1)
                logger.warning("Incorrect password. Please try again.")
    else:
        logger.info("Let's import your wallet and API keys:")
        address = input("Enter your wallet address: ")
        private_key = input("Enter your private key: ")

        if not bscscan_api_key:
            bscscan_api_key = input("Enter your BSCScan API key (get one from https://bscscan.com/myapikey): ")
            save_api_key(bscscan_api_key)

        password = input("Enter a password to encrypt your wallet, please choose a strong password: ")
        key, salt = generate_key(password)
        cipher_suite = Fernet(key)

        with open("wallet.txt", "wb") as file:
            encrypted_data = cipher_suite.encrypt(f'{address}\n{private_key}'.encode())
            file.write(salt + encrypted_data)

        logger.info("Wallet & API setup successful. Your wallet have been encrypted and saved.")

        return address, private_key, bscscan_api_key
