from typing import List, Dict, Any
import gspread
from google.oauth2.service_account import Credentials
from gspread.utils import rowcol_to_a1

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

SPREADSHEET_NAME = "RecToDo"
PIPELINE_TAB_NAME = "pipeline"


def _get_client():
    creds = Credentials.from_service_account_file(
        "service_account.json",
        scopes=SCOPES,
    )
    return gspread.authorize(creds)


def get_pipeline_rows() -> List[Dict[str, Any]]:
    """
    Return all rows from the 'pipeline' tab as a list of dicts.
    Keys come from the header row (id, owner, candidate_name, ...).
    """
    client = _get_client()
    spreadsheet = client.open(SPREADSHEET_NAME)
    worksheet = spreadsheet.worksheet(PIPELINE_TAB_NAME)
    records = worksheet.get_all_records()  # list[dict]
    return records


def append_pipeline_row(row: Dict[str, Any]) -> None:
    """
    Append a single row (dict) to the pipeline tab.
    The dict keys must match the header names in the sheet.
    Missing keys will become empty cells.
    """
    client = _get_client()
    spreadsheet = client.open(SPREADSHEET_NAME)
    worksheet = spreadsheet.worksheet(PIPELINE_TAB_NAME)

    header = worksheet.row_values(1)
    values = [row.get(col, "") for col in header]
    worksheet.append_row(values)


def update_pipeline_row(row_id: str, row: Dict[str, Any]) -> None:
    """
    Update an existing row (matched by 'id' column) in the pipeline tab.
    """
    client = _get_client()
    spreadsheet = client.open(SPREADSHEET_NAME)
    worksheet = spreadsheet.worksheet(PIPELINE_TAB_NAME)

    # Fetch all existing data to find the row index
    records = worksheet.get_all_records()
    header = worksheet.row_values(1)

    target_row_index = None  # 1-based index in sheet
    for idx, rec in enumerate(records, start=2):  # data starts at row 2
        if str(rec.get("id", "")) == str(row_id):
            target_row_index = idx
            break

    if target_row_index is None:
        raise ValueError(f"Row with id {row_id} not found in sheet")

    values = [row.get(col, "") for col in header]
    start = rowcol_to_a1(target_row_index, 1)
    end = rowcol_to_a1(target_row_index, len(header))
    worksheet.update(f"{start}:{end}", [values])


def delete_pipeline_row(row_id: str) -> None:
    """Delete a row (matched by 'id') from the pipeline tab."""
    client = _get_client()
    spreadsheet = client.open(SPREADSHEET_NAME)
    worksheet = spreadsheet.worksheet(PIPELINE_TAB_NAME)

    records = worksheet.get_all_records()
    target_row_index = None  # 1-based index in sheet
    for idx, rec in enumerate(records, start=2):  # data starts at row 2
        if str(rec.get("id", "")) == str(row_id):
            target_row_index = idx
            break

    if target_row_index is None:
        raise ValueError(f"Row with id {row_id} not found in sheet")

    worksheet.delete_rows(target_row_index)
