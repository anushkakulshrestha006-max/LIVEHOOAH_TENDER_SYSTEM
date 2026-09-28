from unittest.mock import Mock, patch

from config.settings import (
    GOOGLE_SHEET_NAME,
    SERVICE_ACCOUNT_FILE,
)
from sheets.sheets_client import SheetsClient


def test_sheets_client_uses_project_relative_settings_path(
    tmp_path,
    monkeypatch,
):
    monkeypatch.chdir(tmp_path)

    fake_creds = object()
    fake_gspread_client = Mock()
    fake_sheet = object()
    fake_gspread_client.open.return_value = fake_sheet

    with patch(
        "sheets.sheets_client."
        "Credentials.from_service_account_file",
        return_value=fake_creds,
    ) as mock_credentials, patch(
        "sheets.sheets_client.gspread.authorize",
        return_value=fake_gspread_client,
    ) as mock_authorize:

        client = SheetsClient()

    mock_credentials.assert_called_once_with(
        str(SERVICE_ACCOUNT_FILE),
        scopes=client.scopes,
    )

    mock_authorize.assert_called_once_with(
        fake_creds
    )

    fake_gspread_client.open.assert_called_once_with(
        GOOGLE_SHEET_NAME
    )

    assert client.sheet is fake_sheet
    assert client._opportunities_cache is None
