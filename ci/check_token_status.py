"""
토큰 상태 확인 유틸리티
"""

import os
from requests.auth import HTTPBasicAuth
import json
import requests


import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.utils.env_loader import load_env_files

# .env 파일 로드
load_env_files()


jenkins_url = "http://3.36.219.242:8080"
credential_domain = "todolist_dev"
user = os.getenv("JENKINS_USER")
password = os.getenv("JENKINS_PASS")


#===========공통 함수===============
def validate_token(url, access_token, timeout=5):
    """토큰 유효성 검증 공통 함수"""
    headers = {"Authorization": f"Bearer {access_token}"}
    res = requests.get(url, headers=headers, timeout=timeout)
    return res.status_code == 200


def update_jenkins_credential(credential_id, secret):
    """Jenkins credential 업데이트 공통 함수"""
    url = f"{jenkins_url}/credentials/store/system/domain/{credential_domain}/credential/{credential_id}"
    headers = {"Content-Type": "application/json"}
    auth = HTTPBasicAuth(user, password)
    data = json.dumps({
        "credentials": {
            "scope": "GLOBAL",
            "id": credential_id,
            "secret": secret,
            "$class": "org.jenkinsci.plugins.plaincredentials.impl.StringCredentialsImpl"
        }
    })
    response = requests.post(url, headers=headers, auth=auth, data=data)
    return response.status_code == 200


def process_token_refresh(token_type, get_token_func, validate_url, access_token_key, refresh_token_key=None):
    """토큰 갱신 및 Jenkins 업데이트 프로세스 공통 함수"""
    new_token = get_token_func()
    if not new_token:
        print(f"{token_type} Token 갱신 실패")
        return False
    
    access_token = new_token.get(access_token_key)
    if not access_token:
        print(f"{token_type} Token에서 access_token을 찾을 수 없습니다")
        return False
    
    if not validate_token(validate_url, access_token):
        print(f"{token_type} Token 검증 실패")
        return False
    
    # Access token 업데이트
    access_credential_id = f"{token_type}_TOKEN" if token_type == "JWT" else f"{token_type}_ACCESS_TOKEN"
    access_success = update_jenkins_credential(access_credential_id, access_token)
    
    # Refresh token 업데이트 (있는 경우)
    refresh_success = True
    if refresh_token_key and refresh_token_key in new_token:
        refresh_token = new_token.get(refresh_token_key)
        refresh_credential_id = f"{token_type}_REFRESH_TOKEN"
        refresh_success = update_jenkins_credential(refresh_credential_id, refresh_token)
    
    if access_success and refresh_success:
        print(f"{token_type} Token 업데이트 성공")
        return True
    else:
        print(f"{token_type} Token 업데이트 실패")
        return False


#===========jwt token refresh===============
def get_new_jwt_token():
    url = f"{os.getenv('BACKEND_BASE_URL')}/api/auth/refresh"
    payload = {"refreshToken": os.getenv("JWT_REFRESH_TOKEN")}
    res = requests.post(url, json=payload, timeout=10)
    if res.status_code == 200:
        return res.json()
    return None

#===========kakao token refresh===============
def get_new_kakao_token():
    url = "https://kauth.kakao.com/oauth/token"
    data = {
        'grant_type': 'refresh_token',
        'client_id': os.getenv("KAKAO_REST_API_KEY"),
        'refresh_token': os.getenv("KAKAO_REFRESH_TOKEN")
    }
    res = requests.post(url, data=data)
    if res.status_code == 200:
        return res.json()
    return None

#===========naver token refresh===============
def get_new_naver_token():
    url = "https://nid.naver.com/oauth2.0/token"
    data = {
        'grant_type': 'refresh_token',
        'client_id': os.getenv("NAVER_CLIENT_ID"),
        'client_secret': os.getenv("NAVER_CLIENT_SECRET"),
        'refresh_token': os.getenv("NAVER_REFRESH_TOKEN")
    }
    res = requests.post(url, data=data)
    if res.status_code == 200:
        return res.json()
    return None


if __name__ == "__main__":
    # ======================= jwt token =======================
    jwt_validate_url = f"{os.getenv('BACKEND_BASE_URL')}/api/auth/me"
    process_token_refresh("JWT", get_new_jwt_token, jwt_validate_url, "token", "refreshToken")

    # ======================= kakao token =======================
    kakao_validate_url = "https://kapi.kakao.com/v2/user/me"
    process_token_refresh("KAKAO", get_new_kakao_token, kakao_validate_url, "access_token")

    # ======================= naver token =======================
    naver_validate_url = "https://openapi.naver.com/v1/nid/me"
    process_token_refresh("NAVER", get_new_naver_token, naver_validate_url, "access_token", "refresh_token")