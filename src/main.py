# pylint: disable=wrong-import-position
# pylint: disable=too-many-nested-blocks
# pylint: disable=broad-exception-caught
# pylint: disable=line-too-long
# pylint: disable=consider-using-f-string
# pylint: disable=dangerous-default-value
# pylint: disable=eval-used
# pylint: disable=global-variable-not-assigned
# pylint: disable=global-statement

"""
This is the main program runner for the trading program. It provides a menu for the user to interact with the program.
"""

import datetime
import sys
from pathlib import Path

import pandas as pd

# Get the absolute path of the project root directory, which contains the 'src' directory.
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.program_background import ProgramBackground
from src.program_constants import INDEX_DETAILS_FNO, LOGS_DIR, SCRIP_MASTER_FILE_PATH
from src.program_display import ProgramDisplay
from src.program_helpers import (
    clear_screen,
    create_data_frame_from_scrip_master_csv,
    disable_loguru_to_devnull,
    get_account_config,
    get_account_names_from_config,
    get_scrip_master,
    remove_old_logs,
    run_as_background_thread,
    setup_logging,
    setup_signal_handlers,
    wait_for_user_input,
)
from src.program_login import Login
from src.program_orders import Orders
from src.program_secrets import SECRETS

log = setup_logging("primary_program_runner", log_to_console=True)

setup_signal_handlers()
DF_PD = pd.DataFrame()
CLIENT_SESSIONS = {}
INTRADAY = True


def start_background_client_tasks():
    """
    Starts background tasks for all logged-in clients.

    This function creates a ProgramBackground instance for each logged-in client and starts the background tasks.

    Returns:
        None
    """
    for account_key, client in CLIENT_SESSIONS.items():
        bg = ProgramBackground(client, account_key, DF_PD)
        bg.start_background_client_tasks()
        log.info("Started background tasks for %s.", account_key)


def login_to_accounts():
    """
    Logs in to user accounts based on user input.

    This function prompts the user to select accounts to log in to and then attempts to log in to each selected account.
    If successful, the logged-in client session is stored in the global CLIENT_SESSIONS dictionary.

    Returns:
        None
    """
    global CLIENT_SESSIONS
    clear_screen()
    print("Login to Accounts:\n")
    accounts = get_account_names_from_config(SECRETS)
    for index, account in enumerate(accounts, start=1):
        print(f"{index}. {account}")
    print("\n")

    selected = input(
        "Enter 'r' to return to the main menu.\nEnter the account number(s) you want to log in to, separated by commas, or 'all' to log in to all accounts: "
    )

    if selected.lower() == "r":
        return

    if selected.lower() == "all":
        selected_indices = range(len(accounts))
    else:
        try:
            selected_indices = [int(num.strip()) - 1 for num in selected.split(",")]
        except ValueError:
            log.error("Invalid input. Please enter only numbers or 'all'.")
            return

    for index in selected_indices:
        if index < 0 or index >= len(accounts):
            log.error("No account found for index %s.", index + 1)
            continue
        account_key = accounts[index]
        try:
            print("\n")
            client = Login(account_key, get_account_config(account_key, SECRETS))
            authenticated_client = client.login()
            CLIENT_SESSIONS[account_key] = authenticated_client
            log.info("Logged in to %s successfully.", account_key)
        except Exception as e:
            log.error("Failed to log in to %s: %s", account_key, e)
    start_background_client_tasks()
    wait_for_user_input()


def sell_order_t(order: Orders, intra_day: bool):
    """
    Places a sell order for the given client.

    Args:
        order (Orders): The Orders object for the client.

    Returns:
        None
    """
    try:
        order.place_sell_order_all(intra_day)
    except Exception as e:
        log.error("Failed to place sell order: %s", e)


def cancel_order_t(order: Orders):
    """
    Places a cancel order for the given client.

    Args:
        order (Orders): The Orders object for the client.

    Returns:
        None
    """
    try:
        order.cancel_all_open_orders()
    except Exception as e:
        log.error("Failed to place cancel order: %s", e)


def place_order_for_all_clients(order_type, response_option=None):
    """
    Places an order for all logged-in clients.

    This function places an order of the given type (buy/sell/cancel) for all clients that are currently logged in.

    Args:
        order_type (str): The type of order to place. Must be 'buy', 'sell', or 'cancel'.

    Returns:
        None
    """
    if not CLIENT_SESSIONS:
        log.error("No clients are currently logged in.")
        wait_for_user_input()
        return

    if order_type not in ["buy", "sell", "cancel"]:
        log.error("Invalid order type. Must be 'buy', 'sell', or 'cancel'.")
        wait_for_user_input()
        return

    if order_type in ["sell", "cancel"]:
        for account_key, client in CLIENT_SESSIONS.items():
            try:
                orders = Orders(client)
                if order_type == "sell":
                    log.info("Placing sell order for %s", account_key)
                    run_as_background_thread(sell_order_t, orders, INTRADAY)
                elif order_type == "cancel":
                    log.info("Placing cancel order for %s", account_key)
                    run_as_background_thread(cancel_order_t, orders)
            except Exception as e:
                log.error("Failed to place order for %s: %s", account_key, e)
        return

    for response in response_option:
        for key, val in response.items():
            try:
                client = CLIENT_SESSIONS[key]
                orders = Orders(client)
                if order_type == "buy":
                    run_as_background_thread(orders.place_buy_order_bulk, val, INTRADAY)
            except Exception as e:
                log.error("Failed to place order for %s: %s", account_key, e)


def debug_client_interaction():
    """
    Allows debugging of client interactions.

    This function displays a menu of clients currently logged in and prompts the user to select a client to debug.
    Once a client is selected, the user can enter commands to run on the client object, prefixed with 'client.'.
    The command is executed using eval and the result is printed.

    Returns:
        None
    """
    clear_screen()
    print("DEBUG MODE\n")
    if not CLIENT_SESSIONS:
        print("No clients currently logged in.\n")
        input("Press Enter to continue...")
        return
    print("Select a client to debug:")
    show_logged_in_accounts()

    selected = int(input("Choose a client number: ")) - 1
    account_keys = list(CLIENT_SESSIONS.keys())
    if selected < 0 or selected >= len(account_keys):
        print("Invalid client selection.\n")
        input("Press Enter to continue...")
        return

    account_key = account_keys[selected]
    client = CLIENT_SESSIONS[account_key]

    while True:
        print(
            "Enter commands to run on the client, e.g., 'client.order_report()'. Type 'exit' to return.\n"
        )
        cmd = input(">> ")
        if cmd.lower() == "exit":
            break
        if not cmd.startswith("client."):
            print("Invalid command. Ensure your command starts with 'client.'")
            continue
        try:
            # Using eval to execute the command
            result = eval(cmd)
            print("Command result:", result)
        except Exception as e:
            print("Failed to execute command:", str(e))


def show_logged_in_accounts():
    """
    Displays the accounts that are currently logged in.

    Returns:
        None
    """
    if not CLIENT_SESSIONS:
        print("No accounts are currently logged in.")
    else:
        print("Accounts currently logged in:")
        for idx, account in enumerate(CLIENT_SESSIONS, start=1):
            print(f"{idx}. {account}")
    print("\n")
    wait_for_user_input()


def main_menu():
    # disable_loguru_to_devnull()
    """
    Displays the main menu and handles user input for various options.

    The main menu allows the user to perform actions such as logging in to accounts,
    placing buy/sell/cancel orders, logging out of accounts, checking logged-in accounts,
    debugging, and exiting the program.

    Returns:
        None
    """
    global INTRADAY
    global DF_PD
    global CLIENT_SESSIONS
    log.info("Getting scrip master")
    get_scrip_master()
    DF_PD = create_data_frame_from_scrip_master_csv(SCRIP_MASTER_FILE_PATH)
    remove_old_logs(LOGS_DIR)
    log.info("Starting main menu")
    while True:

        # Only if time is between 8:00 am to 11am or 3pm to 3:45pm
        now = datetime.datetime.now()
        current_time = now.time()

        # Define the time ranges
        morning_start = datetime.time(8, 0)
        morning_end = datetime.time(11, 0)
        afternoon_start = datetime.time(14, 45)
        afternoon_end = datetime.time(15, 45)

        # Check if current time is outside both time ranges
        if not (
            morning_start <= current_time <= morning_end
            or afternoon_start <= current_time <= afternoon_end
        ):
            print(
                current_time, morning_start, morning_end, afternoon_start, afternoon_end
            )
            print(
                "The main menu is only available between 8:00 am to 11:00 am and 2:45 pm to 3:45 pm."
            )
            wait_for_user_input()
            return

        try:
            # disable_loguru_to_devnull()
            clear_screen()  # Clear the screen before showing the main menu
            print("\t\t\t\tTrade with 5paisa\n")
            print("Main Menu:\n")
            options = [
                "Login to accounts",
                "Place buy order for all logged in accounts",
                "Place sell order for all logged in accounts",
                "Place cancel order for all logged in accounts",
                "Logout of accounts",
                "See which accounts are logged in",
                "Debug",
                "Flip delivery flag for all clients",
                "Remove all session files for all clients",
                "Exit program",
            ]
            for i, option in enumerate(options):
                print(f"{i + 1}. {option}")

            choice = input("\nSelect an option: ")
            log.info("User selected option %s\n", choice)
            if choice.isdigit():
                choice = int(choice)
                if choice == 1:
                    login_to_accounts()
                elif choice == 2:
                    if not CLIENT_SESSIONS:
                        log.info("No clients are currently logged in.")
                        wait_for_user_input()
                        continue
                    display = ProgramDisplay(CLIENT_SESSIONS, INDEX_DETAILS_FNO)
                    while True:
                        response = display.place_buy_order_choose_index_submenu()
                        if response != "r":
                            break

                    if isinstance(response, str):
                        max_attempts = 3
                        while True:
                            try:
                                response_option = (
                                    display.display_option_data_menu_to_user_submenu(
                                        response
                                    )
                                )
                                max_attempts = 3
                            except Exception as e:
                                max_attempts -= 1
                                if max_attempts == 0:
                                    log.error(
                                        "Max attempts reached. Error %s Exiting...", e
                                    )
                                    wait_for_user_input()
                                    break
                                continue
                            if response_option != "r":
                                break
                        if not response_option:
                            continue
                        log.info("Placing buy order for all clients")
                        log.info(response_option)
                        place_order_for_all_clients("buy", response_option)
                elif choice == 3:
                    place_order_for_all_clients("sell")
                elif choice == 4:
                    place_order_for_all_clients("cancel")
                elif choice == 5:
                    raise NotImplementedError("Logout of accounts")
                elif choice == 6:
                    show_logged_in_accounts()
                elif choice == 7:
                    debug_client_interaction()
                elif choice == 8:
                    log.info(
                        "Flipping delivery flag for all clients, current value: %s",
                        INTRADAY,
                    )
                    if INTRADAY:
                        INTRADAY = False
                        log.info("INTRADAY set to False")
                    else:
                        INTRADAY = True
                        log.info("INTRADAY set to True")
                    wait_for_user_input()
                elif choice == 9:
                    Login.delete_all_session_files(list(SECRETS.keys()))
                    CLIENT_SESSIONS = {}
                    log.info("Deleted all session files for all clients.")
                    wait_for_user_input()
                elif choice == 10:
                    break
                else:
                    log.error("Invalid option. Please try again.")
                    wait_for_user_input()
            else:
                log.error("Please enter a number corresponding to the options.")
                wait_for_user_input()  # Wait for user to acknowledge the error
        except Exception as e:
            continue
    log.info("Exiting program...")


if __name__ == "__main__":
    main_menu()
