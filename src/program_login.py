# pylint: disable=wrong-import-position
# pylint: disable=too-many-nested-blocks
# pylint: disable=broad-exception-caught
# pylint: disable=line-too-long
# pylint: disable=consider-using-f-string
# pylint: disable=broad-exception-raised

"""
This module contains the Login class which is used to authenticate with the trading program.
"""

import pickle
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List

from py5paisa import FivePaisaClient

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.program_constants import DATA_DIR, PICKLE_DATA_AGE
from src.program_helpers import setup_logging

log = setup_logging("program_login")


class Login:
    """
    Represents a login session for the trading program.

    Args:
        account_name (str): The name of the account.
        account_details (Dict[str, str]): A dictionary containing the account details.

    Attributes:
        account_name (str): The name of the account.
        account_details (Dict[str, str]): A dictionary containing the account details.
        cred (Dict[str, str]): A dictionary containing the credentials for authentication.
        pin (str): The PIN for the account.
        client_code (str): The client code for the account.
        client_session_file (Path): The path to the file where the login information is stored.
        client (FivePaisaClient): The client instance for the trading program.

    Methods:
        login(): Logs in to the trading program using TOTP authentication, with caching of the login session.
        _authenticate(): Authenticates with the trading API and returns a new client instance.
        _save_client(): Saves the client to a pickle file, ensuring that the directory path exists.
        _load_client(): Loads the client from a pickle file.
        _delete_old_session(): Deletes the old session file if it exists.
        _is_session_valid(): Checks if the cached session is still valid (not older than 6 hours).
        _is_auth_valid(client: FivePaisaClient): Checks if the authentication is still valid (not older than 6 hours).
        logout(): Logs out from the trading program.
    """

    def __init__(self, account_name, account_details: Dict[str, str]):
        self.account_name = account_name
        self.account_details = account_details
        self.cred = {
            "APP_NAME": account_details["APP_NAME"],
            "APP_SOURCE": account_details["APP_SOURCE"],
            "USER_ID": account_details["USER_ID"],
            "PASSWORD": account_details["PASSWORD"],
            "USER_KEY": account_details["USER_KEY"],
            "ENCRYPTION_KEY": account_details["ENCRYPTION_KEY"],
        }
        self.pin = account_details["PIN"]
        self.client_code = account_details["CLIENT_CODE"]
        self.client_session_file = (
            DATA_DIR / account_name.lower() / "login_information.pkl"
        )
        self.client = None

    def login(self):
        """
        Logs in to the trading program using TOTP authentication, with caching of the login session.

        Returns:
            The client instance if login is successful.
        """
        if self._is_session_valid():
            self.client = self._load_client()
            # Check if auth is valid
            if self._is_auth_valid(self.client):
                log.info("Loaded client from cache for user '%s'.", self.account_name)
                return self.client
        self._delete_old_session()
        self.client = self._authenticate()
        self._save_client()
        return self.client

    def _authenticate(self):
        """
        Authenticates with the trading API and returns a new client instance.
        """
        log.info("Authenticating user '%s' with new session.", self.account_name)
        client = FivePaisaClient(cred=self.cred)
        TOTP = input("Enter TOTP for '{}' and press enter: ".format(self.account_name))
        client.get_totp_session(self.client_code, TOTP, self.pin)
        # Add auth check with max retries 2
        max_retries = 2
        auth_status = self._is_auth_valid(client)
        if auth_status:
            log.info("Authentication successful for user '%s'.", self.account_name)
            return client
        while not auth_status and max_retries > 0:
            TOTP = input(
                "Enter TOTP for '{}' and press enter: ".format(self.account_name)
            )
            client.get_totp_session(self.client_code, TOTP, self.pin)
            auth_status = self._is_auth_valid(client)
            if auth_status:
                log.info("Authentication successful for user '%s'.", self.account_name)
                return client
            max_retries -= 1
        raise Exception(
            "Authentication failed for user '{}'.".format(self.account_name)
        )

    def _save_client(self):
        """
        Saves the client to a pickle file, ensuring that the directory path exists.
        """
        # Ensure the directory for the client session file exists
        self.client_session_file.parent.mkdir(parents=True, exist_ok=True)

        with open(self.client_session_file, "wb") as file:
            pickle.dump(self.client, file)
        log.info("Client session saved to '%s'.", self.client_session_file)

    def _load_client(self):
        """
        Loads the client from a pickle file.
        """
        with open(self.client_session_file, "rb") as file:
            return pickle.load(file)

    def _delete_old_session(self):
        """
        Deletes the old session file if it exists.
        """
        if self.client_session_file.exists():
            self.client_session_file.unlink()
            log.info("Deleted old client session file.")

    def _is_session_valid(self):
        """
        Checks if the cached session is still valid (not older than 6 hours).
        """
        if not self.client_session_file.exists():
            return False
        file_mod_time = datetime.fromtimestamp(self.client_session_file.stat().st_mtime)
        return datetime.now() - file_mod_time < timedelta(hours=PICKLE_DATA_AGE)

    def _is_auth_valid(self, client: FivePaisaClient):
        """
        Checks if the authentication is still valid (not older than 6 hours).
        """
        try:
            if client.Login_check() == ".ASPXAUTH=None":
                return False
            return True
        except Exception as e:
            log.error("Error checking authentication: %s", e)
            return False

    @staticmethod  # pylint: disable=no-self-use
    def delete_all_session_files(account_list: List):
        """
        Deletes all session files for the given account list.

        Args:
            account_list (List): A list of account names.

        Returns:
            None
        """
        for account in account_list:
            client_session_file = DATA_DIR / account.lower() / "login_information.pkl"
            if client_session_file.exists():
                client_session_file.unlink()
                log.info("Deleted old client session file for '%s'.", account)

    def logout(self):
        """
        Logs out from the trading program.
        """
        self.client.logout()
