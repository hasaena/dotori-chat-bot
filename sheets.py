from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.discovery_cache.base import Cache
import os
import json
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 캐시 비활성화
class MemoryCache(Cache):
    _CACHE = {}

    def get(self, url):
        return MemoryCache._CACHE.get(url)

    def set(self, url, content):
        MemoryCache._CACHE[url] = content

# 스프레드시트 ID
SPREADSHEET_ID = "1mBtwo9D7zj0b32TQl6zfyrrrjuM3eMj-7czWyg4UP3o"
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

def get_sheets_service():
    """구글 스프레드시트 서비스 객체를 생성합니다."""
    try:
        creds_json = os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON')
        if not creds_json:
            logger.error("GOOGLE_APPLICATION_CREDENTIALS_JSON not found")
            return None
            
        logger.info("Credentials JSON found, creating service...")
        creds_dict = json.loads(creds_json)
        logger.info(f"Service account email: {creds_dict.get('client_email')}")
        
        credentials = service_account.Credentials.from_service_account_info(
            creds_dict,
            scopes=SCOPES
        )
        
        service = build('sheets', 'v4', credentials=credentials, cache=MemoryCache())
        logger.info("Successfully created sheets service")
        return service
    except Exception as e:
        logger.error(f"Error creating sheets service: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return None

def get_sheet_info():
    """스프레드시트의 기본 정보를 가져옵니다."""
    try:
        service = get_sheets_service()
        if not service:
            return None
            
        sheet_metadata = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
        logger.info("스프레드시트 정보:")
        logger.info(f"제목: {sheet_metadata.get('properties', {}).get('title')}")
        logger.info("시트 목록:")
        for sheet in sheet_metadata.get('sheets', []):
            sheet_title = sheet.get('properties', {}).get('title')
            logger.info(f"- {sheet_title}")
        return sheet_metadata
    except Exception as e:
        logger.error(f"Error getting sheet info: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return None

def get_sheet_data(range_name):
    """스프레드시트에서 데이터를 가져옵니다."""
    try:
        logger.info(f"Attempting to get data from sheet: {SPREADSHEET_ID}, range: {range_name}")
        service = get_sheets_service()
        if not service:
            logger.error("Failed to create sheets service")
            return []
            
        result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=range_name
        ).execute()
        
        values = result.get('values', [])
        logger.info(f"Retrieved {len(values)} rows from {range_name}")
        return values
    except Exception as e:
        logger.error(f"Error getting sheet data: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return []

def get_kpop_data():
    """K-pop 상품 정보를 가져옵니다."""
    logger.info("Fetching K-pop product data...")
    return get_sheet_data('Kpop!A2:G')

def get_size_data():
    """사이즈 가이드 정보를 가져옵니다."""
    logger.info("Fetching size guide data...")
    return get_sheet_data('Size!A2:D')

def get_faq_data():
    """FAQ 정보를 가져옵니다."""
    logger.info("Fetching FAQ data...")
    return get_sheet_data('FAQ!A2:C')

if __name__ == "__main__":
    # 스프레드시트 정보 확인
    get_sheet_info() 