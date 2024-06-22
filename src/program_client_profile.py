# pylint: disable=wrong-import-position
# pylint: disable=too-many-nested-blocks
# pylint: disable=broad-exception-caught
# pylint: disable=line-too-long
# pylint: disable=consider-using-f-string

"""
Defines the client profile for the trading program.
"""

import datetime
import sys
from pathlib import Path

from py5paisa import FivePaisaClient

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))


from src.program_constants import BUFFER_MARGIN


class ClientProfile:
    """
    Represents the client profile for the trading program.
    """

    def __init__(self, client: FivePaisaClient) -> None:
        self.client = client

    def get_client_available_margin(self) -> float:
        """
        Get available margin for the client.

        Returns:
            float: The available margin for the client.
        """
        # Only if time is between 8:00 am to 11am or 3pm to 3:45pm
        now = datetime.datetime.now()
        current_time = now.time()

        # Define the time ranges
        afternoon_start = datetime.time(11, 55)
        afternoon_end = datetime.time(15, 45)

        if afternoon_start <= current_time <= afternoon_end:
            return 10000

        return self.client.margin()[0]["NetAvailableMargin"] - BUFFER_MARGIN
