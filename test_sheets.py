from sheets import get_kpop_data, get_size_data, get_faq_data, get_sheet_info
import logging
import os
from dotenv import load_dotenv

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 환경 변수 로드
load_dotenv()

def verify_env():
    """환경 변수 확인"""
    creds = os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON')
    if creds:
        logger.info("구글 인증 정보가 로드되었습니다.")
        return True
    else:
        logger.error("구글 인증 정보를 찾을 수 없습니다.")
        return False

def test_sheets():
    """시트 데이터 테스트"""
    if not verify_env():
        logger.error("환경 변수 설정이 필요합니다.")
        return {"env": False}
    
    results = {}
    
    # 시트 정보 확인
    try:
        sheet_info = get_sheet_info()
        if sheet_info:
            results['sheet_info'] = True
        else:
            results['sheet_info'] = False
    except Exception as e:
        logger.error(f"시트 정보 확인 실패: {e}")
        results['sheet_info'] = False
    
    # K-pop 데이터 테스트
    try:
        kpop = get_kpop_data()
        logger.info(f"K-pop 데이터 로드 성공 (항목 수: {len(kpop)})")
        results['kpop'] = True
    except Exception as e:
        logger.error(f"K-pop 데이터 로드 실패: {e}")
        results['kpop'] = False

    # 사이즈 데이터 테스트
    try:
        size = get_size_data()
        logger.info(f"사이즈 데이터 로드 성공 (항목 수: {len(size)})")
        results['size'] = True
    except Exception as e:
        logger.error(f"사이즈 데이터 로드 실패: {e}")
        results['size'] = False

    # FAQ 데이터 테스트
    try:
        faq = get_faq_data()
        logger.info(f"FAQ 데이터 로드 성공 (항목 수: {len(faq)})")
        results['faq'] = True
    except Exception as e:
        logger.error(f"FAQ 데이터 로드 실패: {e}")
        results['faq'] = False
    
    return results

if __name__ == "__main__":
    results = test_sheets()
    print("\n=== 테스트 결과 ===")
    for test, success in results.items():
        print(f"{test.upper()}: {'성공 ✓' if success else '실패 ✗'}") 