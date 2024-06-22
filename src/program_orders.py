"""
This module contains the Orders class which is used to place buy and sell orders.
"""

# pylint: disable=wrong-import-position
# pylint: disable=too-many-nested-blocks
# pylint: disable=broad-exception-caught
# pylint: disable=line-too-long
# pylint: disable=consider-using-f-string
# pylint: disable=fixme

import re
import sys
from pathlib import Path
from typing import Any, Dict, List

from py5paisa import FivePaisaClient

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.program_helpers import (
    run_as_background_thread,
    setup_logging,
    setup_signal_handlers,
)

setup_signal_handlers()

log = setup_logging("program_orders")

from src.program_constants import INDEX_DETAILS_FNO, ORDER_TYPE_BUY, ORDER_TYPE_SELL


class Orders:
    """
    Represents a class for managing trading orders.

    This class provides methods for placing buy and sell orders, as well as canceling open orders.

    Args:
        client (FivePaisaClient): An instance of the FivePaisaClient class.

    Attributes:
        client (FivePaisaClient): An instance of the FivePaisaClient class.

    """

    def __init__(self, client: FivePaisaClient) -> None:
        self.client = client

    def place_buy_order_bulk(
        self, bulk_order: List[List[Dict[str, Any]]], intraday: bool = True
    ):
        """
        Places multiple buy orders in bulk.

        Args:
            bulk_order (List[List[Dict[str, Any]]]): A list of lists, where each inner list contains
                dictionaries representing individual buy orders.
            intraday (bool, optional): Specifies whether the orders are intraday orders or not.
                Defaults to True.

        Raises:
            Exception: If there is an error while placing the bulk order.

        """

        def place_buy_order_bulk_t(order_b: List[Dict[str, Any]], intra_val: bool):
            for order_in in order_b:
                order_in["IsIntraday"] = intra_val
                # disable_loguru_to_devnull()
                response = self.client.place_order_bulk(OrderList=order_b)
                log.info("Order list: %s", order_b)
                log.info("Response: %s", response)
                # restore_loguru()

        try:
            for index_a, b_order in enumerate(bulk_order):
                for index_b, order in enumerate(b_order):
                    run_as_background_thread(place_buy_order_bulk_t, [order], intraday)
                    log.info("Placing Order List: %s, Sub-List: %s", index_a, index_b)

        except Exception as e:
            log.error("Error placing bulk order: %s", e)

    # def place_sell_order_all(self, intraday: bool = True):
    #     try:
    #         open_positions = self.client.positions()
    #         log.info("Open positions: %s", open_positions)
    #         bulk_orders = []
    #         all_batches = []

    #         # Organize orders into batches
    #         for position in open_positions:
    #             if position["BuyQty"] != position["SellQty"] or position["NetQty"] != 0:
    #                 qty_remaining = position["NetQty"]
    #                 max_qty = (
    #                     INDEX_DETAILS_FNO.get(position["ScripName"].split()[0], {}).get(
    #                         "max_lot_size", 25
    #                     )
    #                     * INDEX_DETAILS_FNO.get(
    #                         position["ScripName"].split()[0], {}
    #                     ).get("lot_quantity", 1)
    #                     / 10
    #                 )

    #                 while qty_remaining > 0:
    #                     if len(bulk_orders) == 9:
    #                         all_batches.append(bulk_orders)
    #                         bulk_orders = []

    #                     qty_to_order = min(qty_remaining, max_qty)
    #                     bulk_orders.append(
    #                         {
    #                             "Exchange": position["Exch"],
    #                             "ExchangeType": position["ExchType"],
    #                             "ScripCode": position["ScripCode"],
    #                             "Qty": int(qty_to_order),
    #                             "OrderType": "Sell",
    #                             "IsIntraday": intraday,
    #                         }
    #                     )
    #                     qty_remaining -= qty_to_order

    #         # Add any remaining orders to the batches
    #         if bulk_orders:
    #             all_batches.append(bulk_orders)

    #         # Submit each batch sequentially
    #         for batch in all_batches:
    #             log.info("Total sell order batches: %s", len(all_batches))
    #             log.info("Submitting sell order batch: %s", batch)
    #             response = self.client.place_order_bulk(OrderList=batch)
    #             log.info("Sell order response: %s", response)
    #             if "B" in [order["Exchange"] for order in batch]:
    #                 self.client.squareoff_all()

    #     except Exception as e:
    #         log.error("Error placing sell order: %s", e)
    #         return

    def place_sell_order_all(self, intraday: bool = True):
        """
        Processes all open positions and places sell orders for quantities that exceed the sold quantities.
        """

        def place_sell_order_t(order_details):
            """
            Function to place an individual sell order. This function is designed to be run in a background thread.
            """
            try:
                response = self.client.place_order(**order_details)
                log.info("Order placed: %s", order_details)
                log.info("Response: %s", response)
            except Exception as e:
                log.error(
                    "Failed to place sell order for %s: %s",
                    order_details["ScripCode"],
                    e,
                )

        try:
            open_positions = self.client.positions()
            log.info("Open positions: %s", open_positions)
            for position in open_positions:
                if position["BuyQty"] != position["SellQty"] or position["NetQty"] != 0:
                    qty_remaining = position["NetQty"]
                    max_qty = (
                        INDEX_DETAILS_FNO.get(position["ScripName"].split()[0], {}).get(
                            "max_lot_size", 25
                        )
                        * INDEX_DETAILS_FNO.get(
                            position["ScripName"].split()[0], {}
                        ).get("lot_quantity", 1)
                        / 10
                    )

                    while qty_remaining > 0:
                        qty_to_order = min(qty_remaining, max_qty)
                        order_details = {
                            "OrderType": ORDER_TYPE_SELL,
                            "Exchange": position["Exch"],
                            "ExchangeType": position["ExchType"],
                            "ScripCode": position["ScripCode"],
                            "Qty": int(qty_to_order),
                            "IsIntraday": intraday,
                            "Price": 0,
                        }
                        qty_remaining -= qty_to_order
                        run_as_background_thread(place_sell_order_t, order_details)

                    # If oversold, place buy orders to cover the difference
                    while qty_remaining < 0:
                        qty_to_order = min(qty_remaining * -1, max_qty)
                        order_details = {
                            "OrderType": ORDER_TYPE_BUY,
                            "Exchange": position["Exch"],
                            "ExchangeType": position["ExchType"],
                            "ScripCode": position["ScripCode"],
                            "Qty": int(qty_to_order),
                            "IsIntraday": intraday,
                            "Price": 0,
                        }
                        qty_remaining += qty_to_order
                        run_as_background_thread(place_sell_order_t, order_details)

        except Exception as e:
            log.error("Error placing sell orders: %s", e)

    def cancel_all_open_orders(self):
        """
        Cancels all open orders.

        This method retrieves the order book and cancels all open orders that meet the following criteria:
        - Have an 'ExchOrderID' field
        - Have a 'TradedQty' field
        - Have a 'ScripCode' field
        - Have an 'OrderStatus' field with a value of 'Pending'

        The method will attempt to cancel the orders up to a maximum number of attempts defined by 'max_attempts'.
        If the order cancellation is successful or there are no open orders to cancel, the method will return.

        Returns:
            None
        """
        try:
            # disable_loguru_to_devnull()
            response = self.client.order_book()
            max_attempts = 2
            total_attempts = 0
            log.info("Order book: %s", response)
            while total_attempts < max_attempts and response is not None:
                cancel_order_list = [
                    {"ExchOrderID": item["ExchOrderID"]}
                    for item in response
                    if "ExchOrderID" in item
                    and "TradedQty" in item
                    and "ScripCode" in item
                    and item.get("OrderStatus") == "Pending"
                ]
                if len(cancel_order_list) == 0:
                    return
                cancel_response = self.client.cancel_bulk_order(cancel_order_list)
                log.info("Cancel order list: %s", cancel_order_list)
                log.info("Cancel response: %s", cancel_response)
                response = self.client.order_book()
                total_attempts += 1
            # restore_loguru()
        except Exception as e:
            log.error("Error cancelling orders: %s", e)

    def get_open_positions(self):
        """
        Retrieves the open positions.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries representing the open positions.
        """
        try:
            # disable_loguru_to_devnull()
            open_positions = self.client.positions()
            display_positions = []
            for position in open_positions:
                if position["BuyQty"] != position["SellQty"] or position["NetQty"] != 0:
                    new_entry = {
                        "Exchange": position["Exch"],
                        "ExchangeType": position["ExchType"],
                        "ScripName": position["ScripName"],
                        "ScripCode": position["ScripCode"],
                        "Qty": position["NetQty"],
                    }
                    display_positions.append(new_entry)
            # restore_loguru()
            return display_positions
        except Exception as e:
            log.error("Error retrieving open positions: %s", e)
            return []
