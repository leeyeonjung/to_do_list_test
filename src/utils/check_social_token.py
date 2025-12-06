"""
check_social_token.py
NAVER, KAKAO Access Token 유효성 검사 스크립트
Jenkins에서 토큰 만료 여부를 확인하는 용도로 사용됨.
"""

import os
import requests
from dotenv import load_dotenv

# .env 로드 (로컬 환경용)
load_dotenv()


def is_naver_token_valid(access_token: str) -> bool:
    """
    NAVER Access Token 유효성 검사

    Args:
        access_token: NAVER Access Token

    Returns:
        True  → 유효한 토큰
        False → 만료 or 잘못된 토큰
    """
    if not access_token:
        return False

    url = "https://openapi.naver.com/v1/nid/me"
    headers = {"Authorization": f"Bearer {access_token}"}

    try:
        res = requests.get(url, headers=headers, timeout=5)
        return res.status_code == 200
    except Exception:
        return False


def is_kakao_token_valid(access_token: str) -> bool:
    """
    KAKAO Access Token 유효성 검사

    Args:
        access_token: KAKAO Access Token

    Returns:
        True  → 유효한 토큰
        False → 만료 or 잘못된 토큰
    """
    if not access_token:
        return False

    url = "https://kapi.kakao.com/v1/user/access_token_info"
    headers = {"Authorization": f"Bearer {access_token}"}

    try:
        res = requests.get(url, headers=headers, timeout=5)
        return res.status_code == 200
    except Exception:
        return False


if __name__ == "__main__":
    # 네이버와 카카오 둘 다 검증
    naver_token = os.getenv("NAVER_ACCESS_TOKEN") or os.getenv("ACCESS_TOKEN")
    kakao_token = os.getenv("KAKAO_ACCESS_TOKEN") or os.getenv("ACCESS_TOKEN")
    
    naver_valid = is_naver_token_valid(naver_token)
    kakao_valid = is_kakao_token_valid(kakao_token)
    
    # 둘 다 유효해야 VALID
    if naver_valid and kakao_valid:
        print("VALID")
    else:
        print("INVALID")
