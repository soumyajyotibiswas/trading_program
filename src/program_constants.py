"""
This module contains all the constants used in the trading program.
"""

from pathlib import Path

PARENT_DIR = Path(__file__).resolve().parent.parent
LOGS_DIR = PARENT_DIR / "logs"
DATA_DIR = PARENT_DIR / "data"
SCRIP_MASTER_FILE_NAME = "ScripMaster.csv"
SCRIP_MASTER_FILE_PATH = DATA_DIR / SCRIP_MASTER_FILE_NAME
SCRIP_MASTER_FILE_URL = (
    "https://openapi.5paisa.com/VendorsAPI/Service1.svc/ScripMaster/segment/All"
)
BUFFER_MARGIN = 5000
PICKLE_DATA_AGE = 8  # in hours
INDEX_DETAILS_FNO = {
    "NIFTY": {
        "symbol": "NIFTY",
        "weekly_expiry": "Thursday",
        "monthly_expiry": "Thursday",
        "lot_quantity": 25,
        "max_lot_size": 720,
        "max_multiplier": 5,
        "step_size": 50,
        "is_index": True,
        "instrument_token": 26000,
        "exchange_segment": "nse_cm",
        "exchange_segment_fo": "nse_fo",
        "exchange_identifier": "Nifty 50",
    },
    "BANKNIFTY": {
        "symbol": "BANKNIFTY",
        "weekly_expiry": "Wednesday",
        "monthly_expiry": "Thursday",
        "lot_quantity": 15,
        "max_lot_size": 600,
        "max_multiplier": 5,
        "step_size": 100,
        "is_index": True,
        "instrument_token": 26009,
        "exchange_segment": "nse_cm",
        "exchange_segment_fo": "nse_fo",
        "exchange_identifier": "Nifty Bank",
    },
    "FINNIFTY": {
        "symbol": "FINNIFTY",
        "weekly_expiry": "Tuesday",
        "monthly_expiry": "Tuesday",
        "lot_quantity": 40,
        "max_lot_size": 450,
        "max_multiplier": 5,
        "step_size": 50,
        "is_index": True,
        "instrument_token": 26037,
        "exchange_segment": "nse_cm",
        "exchange_segment_fo": "nse_fo",
        "exchange_identifier": "Nifty Fin Service",
    },
    "SENSEX": {
        "symbol": "SENSEX",
        "weekly_expiry": "Friday",
        "monthly_expiry": "Friday",
        "lot_quantity": 10,
        "max_lot_size": 1000,
        "max_multiplier": 5,
        "step_size": 100,
        "is_index": True,
        "instrument_token": 26037,
        "exchange_segment": "bse_cm",
        "exchange_segment_fo": "bse_fo",
        "exchange_identifier": "SENSEX",
    },
    # "BANKEX": {
    #     "symbol": "BANKEX",
    #     "weekly_expiry": "Monday",
    #     "monthly_expiry": "Monday",
    #     "lot_quantity": 15,
    #     "max_lot_size": 900,
    #     "max_multiplier": 5,
    #     "step_size": 100,
    #     "is_index": True,
    #     "instrument_token": 26037,
    #     "exchange_segment": "bse_cm",
    #     "exchange_segment_fo": "bse_fo",
    #     "exchange_identifier": "BANKEX",
    # },
    # "MIDCPNifty": {
    #     "symbol": "MIDCPNifty",
    #     "weekly_expiry": "Monday",
    #     "monthly_expiry": "Monday",
    #     "lot_quantity": 75,
    #     "max_lot_size": 4200,
    #     "max_multiplier": 5,
    #     "step_size": 25,
    #     "is_index": True,
    #     "instrument_token": 26000,
    #     "exchange_segment": "nse_cm",
    #     "exchange_segment_fo": "nse_fo",
    #     "exchange_identifier": "MIDCPNifty",
    # },
}
EXCHANGE = "N"
EXCHANGE_TYPE = "D"
ORDER_TYPE_BUY = "B"
ORDER_TYPE_SELL = "S"
OPTION_TYPE_CALL = "CE"
OPTION_TYPE_PUT = "PE"
OPTION_CHAIN_DEPTH = 6
IS_INTRA_DAY = True
INDEX_FINAL_DETAILS_FILE_NAME = "index_final_details.file"
INDEX_DETAILS_FILE_NAME = "index_details.file"
INDEX_FINAL_DETAILS_FETCH_INTERVAL = 180  # in seconds
INDEX_DETAILS_FETCH_INTERVAL = 1  # in seconds
QUOTE_DETAILS_FETCH_INTERVAL = 1  # in seconds
MARKET_CLOSE_FETCH_INTERVAL = 1800  # in seconds
MARKET_OPEN_TIME = "09:15:00"
MARKET_CLOSE_TIME = "15:30:00"
MARKET_OPEN_DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
HOLIDAY_LIST = [
    "20231225",  # Christmas -- Monday
    "20240126",  # Republic Day -- Friday
    "20240308",  # Maha Shivaratri -- Friday
    "20240325",  # Holi -- Monday
    "20240329",  # Good Friday -- Friday
    "20240410",  # Eid-Ul-Fitr (Ramzan Eid) -- Wednesday
    "20240414",  # Dr.Baba Saheb Ambedkar Jayanti (Weekend) -- Sunday
    "20240417",  # Ram Navami -- Wednesday
    "20240421",  # Mahavir Jayanti (Weekend) -- Sunday
    "20240501",  # Maharashtra Day -- Wednesday
    "20240617",  # Bakri Eid -- Monday
    "20240717",  # Moharram -- Wednesday
    "20240815",  # Independence Day -- Thursday
    "20240907",  # Ganesh Chaturthi (Weekend) -- Saturday
    "20241002",  # Mahatma Gandhi Jayanti -- Wednesday
    "20241013",  # Dussehra (Weekend) -- Sunday
    "20241101",  # Diwali-Laxmi Pujan -- Friday
    "20241102",  # Diwali-Balipratipada (Weekend) -- Saturday
    "20241115",  # Gurunanak Jayanti -- Friday
    "20241225",  # Christmas -- Wednesday
]
