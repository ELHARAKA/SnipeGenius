# SnipeGenius 🥞 (PancakeSwap)
# Version: 1.5.0_Stable
# Developed by Fahd El Haraka ©
# Email: fahd@web3dev.ma
# Telegram: @thisiswhosthis
# Website: https://web3dev.ma
# GitHub: https://github.com/ELHARAKA

"""
© Copyright 2023
Proprietary Software by Fahd El Haraka, 2023.
Unauthorized use, duplication, modification, or distribution is strictly prohibited.
Contact fahd@web3dev.ma for permissions and inquiries.
"""

import base64
import os
import pwinput
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from cryptography.fernet import Fernet
from cryptography.fernet import InvalidToken

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

def get_credentials():
    from config import logger, file_logger
    if os.path.exists("wallet.txt"):
        incorrect_attempts = 0
        while True:
            password = pwinput.pwinput(prompt="Enter password to decrypt wallet: ")
            key = generate_key(password)
            cipher_suite = Fernet(key)
            with open("wallet.txt", "rb") as file:
                encrypted_data = file.read()
            salt = encrypted_data[:16]
            key, _ = generate_key(password, salt)
            cipher_suite = Fernet(key)
            try:
                decrypted_data = cipher_suite.decrypt(encrypted_data[16:])
                credentials = decrypted_data.decode().split('\n')
                if len(credentials) >= 2:
                    address, private_key = credentials
                    logger.info("Wallet loaded successfully.")
                    return address, private_key
                else:
                    logger.error("Invalid wallet data. Please re-import your wallet.")
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
        logger.info("Let's import your wallet:")
        address = input("Enter your wallet address: ")
        private_key = input("Enter your private key: ")
        password = input("Enter a password to encrypt your wallet, please choose a strong password: ")
        key, salt = generate_key(password)
        cipher_suite = Fernet(key)
        with open("wallet.txt", "wb") as file:
            encrypted_data = cipher_suite.encrypt(f'{address}\n{private_key}'.encode())
            file.write(salt + encrypted_data)
        logger.info("Wallet setup successful. Your wallet details have been encrypted and saved.")
        return address, private_key

def get_google_details():
    from config import logger, file_logger
    google_cse_id = "2202ec6543da44f6e"

    if os.path.exists("google.txt"):
        with open("google.txt", "r") as file:
            lines = file.readlines()
            google_api_key = lines[0].strip()

        if google_api_key:
            return google_api_key, google_cse_id
        else:
            logger.warning("Invalid Google API key. Please re-import your Google credentials.")
            return None
    else:
        google_api_key = input("Enter your Google API key: ")
        with open("google.txt", "w") as file:
            file.write(f"{google_api_key}\n{google_cse_id}")
        return google_api_key, google_cse_id
