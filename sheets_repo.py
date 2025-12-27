from typing import List, Dict
import gspread
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

SPREADSHEET_NAME = "RecToDo"      # sheet name
PIPELINE_TAB_NAME = "RecToDo"    # tab created earlier


def _get_client():
    creds = Credentials.from_service_account_file(
        "service_account.json",
        scopes=SCOPES,
    )
    return gspread.authorize(creds)


def get_pipeline_rows() -> List[Dict]:
    """
    Return all rows from the 'pipeline' tab as a list of dicts.
    Keys come from the header row (id, owner, candidate_name, ...).
    """
    client = _get_client()
    spreadsheet = client.open(SPREADSHEET_NAME)
    worksheet = spreadsheet.worksheet(PIPELINE_TAB_NAME)
    records = worksheet.get_all_records()  # list[dict]
    return records


def append_pipeline_row(row: Dict) -> None:
    """
    Append a single row (dict) to the pipeline tab.
    The dict keys must match the header names in the sheet.
    Missing keys will become empty cells.
    """
    client = _get_client()
    spreadsheet = client.open(SPREADSHEET_NAME)
    worksheet = spreadsheet.worksheet(PIPELINE_TAB_NAME)

    # Get header order from first row
    header = worksheet.row_values(1)

    values = [row.get(col, "") for col in header]
    worksheet.append_row(values)
