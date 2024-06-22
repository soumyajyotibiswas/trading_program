# pylint: disable=protected-access
# pylint: disable=unused-variable
# pylint: disable=global-variable-not-assigned
# pylint: disable=unused-argument
# pylint: disable=unspecified-encoding
# pylint: disable=global-statement
# pylint: disable=line-too-long

"""
This module contains helper functions for the trading program.
"""

import json
import logging
import os
import signal
import sys
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import requests
from loguru import logger as loguru_logger
from src.program_constants import (
    DATA_DIR,
    LOGS_DIR,
    SCRIP_MASTER_FILE_PATH,
    SCRIP_MASTER_FILE_URL,
)

ORIGINAL_LOGURU_HANDLERS = []


def disable_loguru_to_devnull():
    global ORIGINAL_LOGURU_HANDLERS
    ORIGINAL_LOGURU_HANDLERS = loguru_logger._core.handlers.copy()
    loguru_logger.remove()
    loguru_logger.add(os.devnull, enqueue=True)


def restore_loguru():
    loguru_logger.remove()  # Remove the devnull handler
    for handler_id, handler in ORIGINAL_LOGURU_HANDLERS.items():
        loguru_logger.add(**handler)


def get_account_config(account_name, account_config):
    """
    Retrieves the account configuration for the specified account name.

    Args:
        account_name (str): The name of the account to retrieve the configuration for.
        account_config (dict): A dictionary containing the account configurations.

    Returns:
        str: The account configuration for the specified account name. If the account name is not found, returns "Account not found".
    """
    return account_config.get(account_name, "Account not found")


def get_account_names_from_config(account_config):
    """
    Returns a list of account names from the given account configuration.

    Args:
        account_config (dict): A dictionary containing account configurations.

    Returns:
        list: A list of account names extracted from the account configuration.

    """
    return list(account_config.keys())


def get_scrip_master():
    """
    Downloads the scrip master csv file from a given URL and stores it in DATA_DIR.
    The file is downloaded only if the scrip master is not present or is older than 48 hours.

    Returns:
        None
    """
    if SCRIP_MASTER_FILE_PATH.exists():
        file_mod_time = datetime.fromtimestamp(SCRIP_MASTER_FILE_PATH.stat().st_mtime)
        if datetime.now() - file_mod_time < timedelta(hours=48):
            print("Scrip Master file is up-to-date.")
            return  # File is up-to-date, no need to download
        else:
            print("Scrip Master file is outdated, downloading new file.")
    else:
        print("Scrip Master file does not exist, downloading new file.")
    try:
        response = requests.get(SCRIP_MASTER_FILE_URL, timeout=300)
        response.raise_for_status()  # Raise an exception for HTTP errors
        # Ensure DATA_DIR exists
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        # Write the content to a file
        with open(SCRIP_MASTER_FILE_PATH, "wb") as f:
            f.write(response.content)
        print("Scrip Master file has been downloaded and saved.")
    except requests.RequestException as e:
        print(f"An error occurred while downloading the file: {e}")


def continue_or_back():
    """
    Prompts the user to continue with the action or go back to the main menu.

    Returns:
        str or bool: The user's choice. Returns False if the choice is invalid.
    """
    print("Y. Continue with the action")
    print("N. Back to main menu\n")
    choice = input("Select an option: ")
    if choice not in ["Y", "N", "y", "n"]:
        return False
    return choice


def clear_screen():
    """
    Clears the terminal screen.

    This function checks the operating system and uses the appropriate command
    to clear the terminal screen. On Windows, it uses the "cls" command, and on
    other operating systems, it uses the "clear" command.

    Note:
        This function relies on the `os.name` attribute to determine the
        operating system. Make sure to import the `os` module before using
        this function.

    """
    if os.name == "nt":
        _ = os.system("cls")
    else:
        _ = os.system("clear")


def setup_logging(script_name, log_to_console=False):
    """
    Sets up logging for a script, saving logs to a file based on the script's name and the current date/time.
    Optionally logs to console based on the log_to_console flag.

    Args:
        script_name (str): The name of the script, used to create a dedicated log directory and file.
        log_to_console (bool): Flag to determine whether logs should also be output to the console.
    """
    logs_dir = LOGS_DIR / script_name
    logs_dir.mkdir(parents=True, exist_ok=True)

    current_time = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    log_filename = logs_dir / f"{current_time}.log"

    logger = logging.getLogger(script_name)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    fh = logging.FileHandler(log_filename)
    fh.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "[(%(asctime)s) (%(name)s) (%(levelname)s)] %(message)s"
    )
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    if log_to_console:
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        ch.setFormatter(formatter)
        logger.addHandler(ch)

    return logger


def wait_for_user_input():
    """
    Waits for user input.

    This function prompts the user to press Enter to continue.

    Parameters:
        None

    Returns:
        None
    """
    input("\nPress Enter to continue...")


def create_index_json_files(data, directory=DATA_DIR):
    """
    Create JSON files for each item in the given dictionary.

    Args:
        data (dict): The dictionary containing the items to be saved as JSON files.
        directory (str): The directory where the JSON files will be created. Defaults to DATA_DIR.

    Returns:
        None
    """
    # Ensure the directory exists
    Path(directory).mkdir(parents=True, exist_ok=True)

    # Iterate over each item in the dictionary
    for key, _details in data.items():
        # Define the file path
        file_path = os.path.join(directory, f"{key}_details.json")

        # Check if the file already exists
        if not file_path.exists():
            # Create an empty file if it does not exist
            file_path.touch()
            print(f"File created: {file_path}")
        else:
            print(f"File already exists: {file_path}")


def create_data_frame_from_scrip_master_csv(file_path: Path) -> pd.DataFrame:
    """
    Create a pandas DataFrame from a CSV file containing scrip master data.

    Args:
        file_path (Path or str): The path to the CSV file.

    Returns:
        df_pd (pandas.DataFrame): The DataFrame created from the CSV file.

    Raises:
        None
    """
    if not isinstance(file_path, Path):
        file_path = Path(file_path)
    df_pd = pd.read_csv(file_path)
    print(df_pd.columns)  # Check what columns are present
    df_pd.set_index("Name", inplace=True)
    return df_pd


def create_empty_file_if_not_exists(file_path):
    """Ensures an empty file exists at the specified file path."""
    if not os.path.exists(file_path):
        with open(file_path, "w") as file:
            pass  # Create an empty file


def dump_data_to_file(data, file_path):
    """Dumps a list of dictionaries to a file as JSON."""
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


def is_file_not_present_or_empty(file_path):
    """Checks if a file is not present or empty."""
    return not os.path.exists(file_path) or os.path.getsize(file_path) == 0


def read_data_from_file(file_path):
    """Reads JSON data from a file and returns it as a list of dictionaries."""
    if is_file_not_present_or_empty(file_path):
        return None
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def thread_function(name):
    """Function to run in the background thread."""
    try:
        while True:
            print(f"Thread {name}: updating data...")
            time.sleep(1)  # Simulate work by sleeping
    except KeyboardInterrupt:
        print(f"Thread {name} received a signal to terminate")


def run_as_background_thread(target, *args):
    """Runs the given target function as a background daemon thread."""
    thread = threading.Thread(target=target, args=args)
    thread.daemon = True
    thread.start()
    return thread


def signal_handler(signum, frame):
    """Handle signals to terminate the main script and cleanup resources."""
    print("Signal handler called with signal", signum)
    sys.exit(0)


def setup_signal_handlers():
    """Setup signal handling to gracefully handle termination."""
    signal.signal(signal.SIGINT, signal_handler)  # Handle Ctrl-C
    signal.signal(signal.SIGTERM, signal_handler)  # Handle kill command


def create_scrip_code_match(
    symbol: str, expiry_date_dt: datetime, option_type: str, option_strike: float
):
    """
    Creates a scrip code match based on the given parameters.

    Args:
        symbol (str): The symbol of the scrip.
        expiry_date_dt (datetime): The expiry date of the option in datetime format.
        option_type (str): The type of the option (e.g., 'CALL', 'PUT').
        option_strike (float): The strike price of the option.

    Returns:
        str: The scrip code match generated based on the given parameters.
    """
    if isinstance(expiry_date_dt, str):
        expiry_date_dt = datetime.strptime(expiry_date_dt, "%Y-%m-%d")
    option_strike = float(option_strike)
    return f"{symbol} {expiry_date_dt.strftime('%d %b %Y')} {option_type} {option_strike:.2f}"


def fetch_scrip_code_from_csv(df_pd: pd.DataFrame, to_match: str):
    """
    Get the scrip code for a given name from a CSV file loaded into a pandas DataFrame.

    Args:
    - df_pd: pandas DataFrame containing the CSV file data.
    - to_match: the name of the scrip for which to find the scrip code.

    Returns:
    - Scrip code of the matching scrip name in the DataFrame.

    Raises:
    - ValueError: If the scrip code for the given name is not found in the DataFrame.
    """
    # Check if the name exists in the index
    if to_match in df_pd.index:
        scrip_code = df_pd.loc[to_match, "ScripCode"]  # Corrected the column name here
        return scrip_code
    raise ValueError(f"Scripcode for {to_match} not found.")


def remove_old_logs(logs_dir: Path, days: int = 2):
    """
    Removes files in the specified logs directory that are older than the given number of days and
    keeps only the latest three files in each subdirectory of the logs directory.

    Args:
        logs_dir (Path): The path to the directory containing log files.
        days (int): The number of days beyond which a file is considered old and will be deleted.
    """
    current_time = datetime.now()
    cutoff_time = current_time - timedelta(days=days)

    # First, remove files older than the specified number of days
    for log_file in logs_dir.rglob("*"):
        if log_file.is_file():  # Ensure it's a file
            modification_time = datetime.fromtimestamp(log_file.stat().st_mtime)
            if modification_time < cutoff_time:
                log_file.unlink()  # Delete the file

    # Then, keep only the latest three files in each subdirectory
    for subdirectory in [d for d in logs_dir.iterdir() if d.is_dir()]:
        file_list = list(subdirectory.glob("*"))  # Get all files in the subdirectory
        file_list = [f for f in file_list if f.is_file()]  # Filter out directories
        if len(file_list) > 3:
            file_list.sort(
                key=lambda x: x.stat().st_mtime, reverse=True
            )  # Sort by modification time, newest first
            for file_to_delete in file_list[
                3:
            ]:  # Remove all but the three newest files
                file_to_delete.unlink()
