# pylint: disable=wrong-import-position
# pylint: disable=too-many-nested-blocks
# pylint: disable=broad-exception-caught
# pylint: disable=line-too-long
# pylint: disable=consider-using-f-string

"""
This module contains the `ProgramBackground` class responsible for running background tasks related to the trading program.
"""

import sys
import time
from datetime import datetime, timedelta
from math import floor
from pathlib import Path
from typing import Any, Dict, List

from pandas import DataFrame
from py5paisa import FivePaisaClient

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.program_client_profile import ClientProfile
from src.program_constants import (
    DATA_DIR,
    INDEX_DETAILS_FNO,
    OPTION_TYPE_CALL,
    OPTION_TYPE_PUT,
)
from src.program_helpers import (
    create_empty_file_if_not_exists,
    create_scrip_code_match,
    disable_loguru_to_devnull,
    dump_data_to_file,
    fetch_scrip_code_from_csv,
    read_data_from_file,
    restore_loguru,
    run_as_background_thread,
    setup_logging,
    setup_signal_handlers,
)
from src.program_orders import Orders
from src.program_quotes import Quotes

setup_signal_handlers()

log = setup_logging("program_background")


class ProgramBackground:
    """
    Class responsible for running background tasks related to the trading program.

    Args:
        client (FivePaisaClient): The client object used for interacting with the trading platform.
        client_key (str): The key associated with the client.

    Attributes:
        client (FivePaisaClient): The client object used for interacting with the trading platform.
        client_key (str): The key associated with the client.
        quotes (Quotes): The quotes object used for retrieving index quotes.
        client_profile (ClientProfile): The client profile object used for retrieving client information.
        client_margin_file_path (str): The file path for storing the client's available margin.

    """

    def __init__(
        self, client: FivePaisaClient, client_key: str, df_pd: DataFrame
    ) -> None:
        self.client = client
        self.client_key = client_key.lower()
        self.quotes = Quotes(client, INDEX_DETAILS_FNO)
        self.client_profile = ClientProfile(self.client)
        self.client_path = None
        self.client_dir_path = DATA_DIR / self.client_key
        self.client_margin_file_path = self.client_dir_path / "client_margin.json"
        self.__create_client_directory(self.client_dir_path)
        self.client_orders = Orders(self.client)
        self.df_pd = df_pd

    def __create_client_directory(self, path_to_create: Path):
        """
        Create a directory for the client data.

        Returns:
            None
        """
        path_to_create.mkdir(parents=True, exist_ok=True)

    def store_client_open_positions_to_file(self):
        """
        Stores the client's open positions to a file.

        This method continuously retrieves the client's open positions and stores them in a file.
        The open positions are fetched using the `get_open_positions` method from the `client_profile` object.
        The open positions are then dumped to a file along with additional information such as the timestamp.

        Raises:
            Exception: If an error occurs while storing the client's open positions.

        """
        try:

            def store_client_open_positions_to_file_t():
                """
                Stores the client's open positions to a file.

                This function continuously retrieves the client's open positions,
                stores them in a dictionary, and dumps the data to a file.
                The process repeats every 1 second until stopped.

                Note: This function assumes the existence of certain helper functions
                such as `#disable_loguru_to_devnull()`, `#restore_loguru()`,
                `create_empty_file_if_not_exists()`, and `dump_data_to_file()`.

                Returns:
                    None
                """
                log.info("Storing client open positions to file...")
                while True:
                    try:
                        time.sleep(2)
                        disable_loguru_to_devnull()
                        open_positions = self.client_orders.order_book()
                        # restore_loguru()
                        open_positions_file_path = (
                            self.client_dir_path / "open_positions.json"
                        )
                        create_empty_file_if_not_exists(open_positions_file_path)
                        data_to_dump = {
                            "client": self.client_key,
                            "open_positions": open_positions,
                            "timestamp": "%s +5:30"
                            % (
                                datetime.utcnow() + timedelta(hours=5, minutes=30)
                            ).strftime("%Y-%m-%d %H:%M:%S"),
                        }
                        dump_data_to_file(data_to_dump, open_positions_file_path)
                    except Exception as e:
                        log.error("Error in store_client_open_positions_to_file: %s", e)
                        time.sleep(2)

            run_as_background_thread(store_client_open_positions_to_file_t)
        except Exception as e:
            log.error("Error in store_client_open_positions_to_file: %s", e)
            sys.exit(1)

    def store_index_quotes_to_file(self):
        """
        Stores index quotes to a file.

        This method continuously retrieves quotes for each index in `INDEX_DETAILS_FNO` and stores them in separate JSON files.
        The quotes are fetched using the `get_ltp_index` method from the `quotes` object.
        The quotes are then dumped to a file along with additional information such as the current week's expiry date and timestamp.

        Raises:
            Exception: If an error occurs while storing the index quotes.

        """
        try:

            def store_index_quotes_to_file_t(index_key: str):
                """
                Stores index quotes to a file.

                Args:
                    index_key (str): The key of the index for which quotes are to be stored.

                Returns:
                    None
                """
                log.info("Storing index quotes to file...")
                while True:
                    try:
                        time.sleep(2)
                        disable_loguru_to_devnull()
                        log.info("Getting quote for index: %s", index_key)
                        index_quote = self.quotes.get_ltp_index(index_key)
                        log.info("Index quote for %s: %s", index_key, index_quote)
                        # restore_loguru()
                        create_empty_file_if_not_exists(
                            f"{self.client_dir_path}/{index_key}.json"
                        )
                        current_week_expiry_date = (
                            self.quotes.get_current_week_expiry_date(
                                index_key=index_key
                            )
                        )
                        data_to_dump = {
                            "index": index_key,
                            "quote": index_quote,
                            "current_week_expiry_date": current_week_expiry_date,
                            "timestamp": "%s +5:30"
                            % (
                                datetime.utcnow() + timedelta(hours=5, minutes=30)
                            ).strftime("%Y-%m-%d %H:%M:%S"),
                        }
                        log.info("Dumping data to file: %s.json", index_key)
                        dump_data_to_file(
                            data_to_dump, f"{self.client_dir_path}/{index_key}.json"
                        )
                        log.info("Data dumped to file: %s.json", index_key)
                    except Exception as e:
                        log.error("Error in store_index_quotes_to_file: %s", e)
                        time.sleep(2)

            for index_key in INDEX_DETAILS_FNO:
                run_as_background_thread(store_index_quotes_to_file_t, index_key)
        except Exception as e:
            log.error("Error in store_index_quotes_to_file: %s", e)
            sys.exit(1)

    def store_client_margin_to_file(self):
        """
        Stores the client's available margin to a file.

        This method continuously retrieves the client's available margin,
        and stores it along with the current timestamp in a file.

        Raises:
            Exception: If an error occurs while storing the client margin to file.
        """
        try:

            def store_client_margin_to_file_t():
                """
                Stores the client's available margin to a file at regular intervals.

                This function continuously retrieves the client's available margin,
                stores it along with the current timestamp in a dictionary, and dumps
                the data to a file. The process repeats every 1 second until stopped.

                Note: This function assumes the existence of certain helper functions
                such as `#disable_loguru_to_devnull()`, `#restore_loguru()`,
                `create_empty_file_if_not_exists()`, and `dump_data_to_file()`.

                Returns:
                    None
                """
                log.info("Storing client margin to file...")
                while True:
                    try:
                        time.sleep(2)
                        disable_loguru_to_devnull()
                        client_margin = (
                            self.client_profile.get_client_available_margin()
                        )
                        log.info("Client margin: %s", client_margin)
                        # restore_loguru()
                        margin_file_path = self.client_margin_file_path
                        create_empty_file_if_not_exists(margin_file_path)
                        data_to_dump = {
                            "client": self.client_key,
                            "available_margin": client_margin,
                            "timestamp": "%s +5:30"
                            % (
                                datetime.utcnow() + timedelta(hours=5, minutes=30)
                            ).strftime("%Y-%m-%d %H:%M:%S"),
                        }
                        log.info("Dumping data to file: %s", margin_file_path)
                        dump_data_to_file(data_to_dump, margin_file_path)
                        log.info("Data dumped to file: %s", margin_file_path)
                    except Exception as e:
                        log.error("Error in store_client_margin_to_file: %s", e)
                        time.sleep(2)

            run_as_background_thread(store_client_margin_to_file_t)
        except Exception as e:
            log.error("Error in store_client_margin_to_file: %s", e)
            sys.exit(1)

    def store_index_option_quotes_to_file(self):
        """
        Stores index option quotes to a file.

        This method retrieves index option quotes, calculates option details, and stores them in a file.
        It runs as a background thread for each index key in the INDEX_DETAILS_FNO dictionary.

        Returns:
            None
        """
        try:

            def create_option_details(index_key, expiry, strike_price_list):
                option_details_map = []
                for strike_price in strike_price_list:
                    for option_type in [OPTION_TYPE_CALL, OPTION_TYPE_PUT]:
                        symbol = create_scrip_code_match(
                            index_key, expiry, option_type, strike_price
                        )
                        option_details_map.append(
                            {
                                "Exch": (
                                    "B" if index_key in ("SENSEX", "BANKEX") else "N"
                                ),
                                "ExchType": "D",
                                "Symbol": symbol,
                                "Expiry": datetime.strptime(
                                    expiry, "%Y-%m-%d"
                                ).strftime("%Y%m%d"),
                                "StrikePrice": f"{float(strike_price):.0f}",
                                "OptionType": option_type,
                            }
                        )
                log.info("Option details map: %s", option_details_map)
                return option_details_map

            def create_options_map(option_details_map, option_details, client_margin):
                options_map = []
                for detail_map, detail in zip(
                    option_details_map, option_details["Data"]
                ):
                    index_base = detail_map["Symbol"].split()[0]
                    if "LastRate" in detail and detail["LastRate"] > 0:
                        # Calculate how many units can be bought with the available margin
                        lot_quantity = INDEX_DETAILS_FNO.get(index_base, {}).get(
                            "lot_quantity", 1
                        )
                        max_lot_size = INDEX_DETAILS_FNO.get(index_base, {}).get(
                            "max_lot_size", 1
                        )
                        # max_multiplier = INDEX_DETAILS_FNO.get(index_base, {}).get( "max_multiplier", 1)

                        units_can_buy = floor(client_margin / detail["LastRate"])

                        # Calculate how many full lots can be bought
                        full_lots = units_can_buy // lot_quantity

                        # Calculate the quantity to purchase as full lots times the lot size
                        qty_to_purchase = full_lots * lot_quantity

                        # Fetch the scrip code from the CSV file
                        to_match = detail_map["Symbol"]
                        scrip_code = int(
                            fetch_scrip_code_from_csv(self.df_pd, to_match)
                        )

                        max_qty_per_order = (lot_quantity * max_lot_size) // 10
                        max_orders_per_list = (
                            lot_quantity * max_lot_size
                        ) // max_qty_per_order
                        # Initialize a list to store the bulk orders
                        bulk_order_list: List[List[Dict[str, Any]]] = []
                        bulk_order: List[Dict[str, Any]] = []
                        # Create bulk order dicts and distribute them into lists
                        qty_to_purchase_stat = qty_to_purchase
                        while qty_to_purchase > 0:
                            order_qty = min(qty_to_purchase, max_qty_per_order)
                            bulk_order.append(
                                {
                                    "Exchange": (
                                        "B"
                                        if index_base in ("SENSEX", "BANKEX")
                                        else "N"
                                    ),
                                    "ExchangeType": "D",
                                    "ScripCode": scrip_code,
                                    "Qty": order_qty,
                                    "OrderType": "B",
                                    "Price": 0,  # Assuming market order
                                }
                            )

                            if (
                                len(bulk_order) == max_orders_per_list
                                or qty_to_purchase <= max_qty_per_order
                            ):
                                # Once the list reaches its max size or remaining qty is less than max per order, add to bulk_order_list
                                bulk_order_list.append(bulk_order)
                                bulk_order = (
                                    []
                                )  # Reset the bulk order list for the next batch

                            qty_to_purchase -= (
                                order_qty  # Decrease the quantity left to purchase
                            )

                        # Add the remaining orders if any
                        if bulk_order:
                            bulk_order_list.append(bulk_order)

                        options_map.append(
                            {
                                "Index_Symbol": detail_map["Symbol"],
                                "Option_Symbol": detail["Symbol"],
                                "Expiry": detail_map["Expiry"],
                                "StrikePrice": detail_map["StrikePrice"],
                                "ScripCode": scrip_code,
                                "OptionType": detail_map["OptionType"],
                                "High": detail["High"],
                                "Low": detail["Low"],
                                "LastRate": detail["LastRate"],
                                "Quantity_to_Purchase": qty_to_purchase_stat,
                                "Client_Margin": client_margin,
                                "BulkOrderList": bulk_order_list,
                                "timestamp": "%s +5:30"
                                % (
                                    datetime.utcnow() + timedelta(hours=5, minutes=30)
                                ).strftime("%Y-%m-%d %H:%M:%S"),
                            }
                        )
                log.info("Options map: %s", options_map)
                return options_map

            def store_index_option_quotes_to_file_t(index_key: str):
                log.info("Storing index option quotes to file for index: %s", index_key)
                while True:
                    try:
                        time.sleep(1)
                        index_quote_file = f"{self.client_dir_path}/{index_key}.json"
                        file_contents_index_quote = read_data_from_file(
                            index_quote_file
                        )
                        if file_contents_index_quote is None:
                            log.info("Index quote file not found: %s", index_quote_file)
                            continue

                        index_quote = file_contents_index_quote["quote"]
                        expiry = file_contents_index_quote["current_week_expiry_date"]
                        option_strike_price_list = (
                            self.quotes.get_opt_strike_price_list(
                                index_key, index_quote
                            )
                        )
                        if not option_strike_price_list:
                            log.info("No option strike prices found for %s.", index_key)
                            continue

                        file_contents_client_margin = read_data_from_file(
                            self.client_margin_file_path
                        )
                        if file_contents_client_margin is None:
                            log.info(
                                "Client margin file not found: %s",
                                self.client_margin_file_path,
                            )
                            continue

                        client_margin = file_contents_client_margin["available_margin"]
                        option_details_map = create_option_details(
                            index_key, expiry, option_strike_price_list
                        )

                        disable_loguru_to_devnull()
                        option_details = self.quotes.get_ltp_for_opt_strike_price(
                            optional_list=option_details_map
                        )
                        log.info("Option details quotes: %s", option_details)
                        options_map = create_options_map(
                            option_details_map, option_details, client_margin
                        )
                        # restore_loguru()

                        option_details_file_path = (
                            f"{self.client_dir_path}/{index_key}_options.json"
                        )
                        create_empty_file_if_not_exists(option_details_file_path)
                        log.info("Dumping data to file: %s", option_details_file_path)
                        dump_data_to_file(options_map, option_details_file_path)
                    except Exception as e:
                        log.error("Error processing index %s: %s", index_key, str(e))
                        time.sleep(1)

            for index_key in INDEX_DETAILS_FNO:
                run_as_background_thread(store_index_option_quotes_to_file_t, index_key)
        except Exception as e:
            log.error("Error in store_index_option_quotes_to_file: %s", e)

    def start_background_client_tasks(self):
        """
        Starts background tasks for the client.

        This method starts the following background tasks for the client:
        - Storing index quotes to a file
        - Storing client margin to a file
        - Storing index option quotes to a file

        Returns:
            None

        Raises:
            Exception: If an error occurs while starting the background tasks.
        """
        try:
            self.store_index_quotes_to_file()
            self.store_client_margin_to_file()
            self.store_index_option_quotes_to_file()
            self.store_client_open_positions_to_file()
            log.info("Started background tasks for %s.", self.client_key)
        except Exception as e:
            log.error("Error in start_background_client_tasks: %s", e)
            sys.exit(1)
