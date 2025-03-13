# sheets.py
import os
import logging

from google.oauth2 import service_account
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

# Google Sheets 문서 ID (예: "1mBtwo9D7zj0b32TQl6zfyrrrjuM3eMj-7czWyg4UP3o")
SHEET_ID = "1mBtwo9D7zj0b32TQl6zfyrrrjuM3eMj-7czWyg4UP3o"

def get_sheets_service():
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not creds_path:
        logger.error("GOOGLE_APPLICATION_CREDENTIALS 환경변수가 설정되지 않았습니다.")
        return None
    logger.info(f"Credentials file path: {creds_path}")

    try:
        credentials = service_account.Credentials.from_service_account_file(
            creds_path,
            scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
        service = build("sheets", "v4", credentials=credentials)
        return service
    except Exception as e:
        logger.error(f"Error creating sheets service: {e}", exc_info=True)
        return None


def get_kpop_data():
    """
    K-pop 제품 정보를 시트에서 불러옵니다.
    Kpop!A2:G 범위를 조회.
    """
    logger.info("Fetching K-pop product data...")
    service = get_sheets_service()
    if not service:
        return []

    logger.info(f"Attempting to get data from sheet: {SHEET_ID}, range: Kpop!A2:G")
    try:
        result = service.spreadsheets().values().get(
            spreadsheetId=SHEET_ID,
            range="Kpop!A2:G"
        ).execute()
        data = result.get("values", [])
        return data
    except Exception as e:
        logger.error(f"Failed to fetch K-pop data: {e}", exc_info=True)
        return []


def get_size_data():
    """
    의류 사이즈 정보를 시트에서 불러옵니다.
    Size!A2:D 범위를 조회.
    """
    logger.info("Fetching size guide data...")
    service = get_sheets_service()
    if not service:
        return []

    logger.info(f"Attempting to get data from sheet: {SHEET_ID}, range: Size!A2:D")
    try:
        result = service.spreadsheets().values().get(
            spreadsheetId=SHEET_ID,
            range="Size!A2:D"
        ).execute()
        data = result.get("values", [])
        return data
    except Exception as e:
        logger.error(f"Failed to fetch size data: {e}", exc_info=True)
        return []


def get_faq_data():
    """
    FAQ 정보를 시트에서 불러옵니다.
    FAQ!A2:C 범위를 조회.
    """
    logger.info("Fetching FAQ data...")
    service = get_sheets_service()
    if not service:
        return []

    logger.info(f"Attempting to get data from sheet: {SHEET_ID}, range: FAQ!A2:C")
    try:
        result = service.spreadsheets().values().get(
            spreadsheetId=SHEET_ID,
            range="FAQ!A2:C"
        ).execute()
        data = result.get("values", [])
        return data
    except Exception as e:
        logger.error(f"Failed to fetch FAQ data: {e}", exc_info=True)
        return []
