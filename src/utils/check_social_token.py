"""
check_social_token.py
NAVER, KAKAO Access Token 유효성 검사 스크립트
Jenkins 환경에서도 환경 변수 우선으로 동작하도록 리팩터링됨.
"""

import os
import requests

from src.utils.env_loader import load_env_files

# ============================================================
# 1. 환경 변수 파일 로딩
# ============================================================

# 🔥 환경 변수 파일 자동 로딩 (공통 모듈 사용)
# 우선순위: 1. .env (로컬), 2. .env-dev-test (Jenkins)
load_env_files()


# ============================================================
# 2. NAVER / KAKAO token validators
# ============================================================

def is_naver_token_valid(access_token: str) -> bool:
    """NAVER Access Token 유효성 검사"""
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
    """KAKAO Access Token 유효성 검사"""
    if not access_token:
        return False

    url = "https://kapi.kakao.com/v1/user/access_token_info"
    headers = {"Authorization": f"Bearer {access_token}"}

    try:
        res = requests.get(url, headers=headers, timeout=5)
        return res.status_code == 200
    except Exception:
        return False


# ============================================================
# 3. Main 실행부
# ============================================================

if __name__ == "__main__":
    # 🚀 우선순위: OS 환경변수 → ENV_FILE → .env
    naver_token = (
        os.getenv("NAVER_ACCESS_TOKEN")
        or os.getenv("ACCESS_TOKEN")
    )

    kakao_token = (
        os.getenv("KAKAO_ACCESS_TOKEN")
        or os.getenv("ACCESS_TOKEN")
    )

    naver_valid = is_naver_token_valid(naver_token)
    kakao_valid = is_kakao_token_valid(kakao_token)

    # 둘 다 VALID → Jenkins에 "VALID" 신호 전달
    if naver_valid and kakao_valid:
        print("VALID")
    else:
        print("INVALID")
