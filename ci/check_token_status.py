"""
토큰 상태 확인 유틸리티
"""

import logging
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

log = logging.getLogger(__name__)


jenkins_url = "http://3.36.219.242:8080"
credential_domain = "todolist_dev"
user = os.getenv("JENKINS_USER")
password = os.getenv("JENKINS_PASS")


#===========jwt token validation===============
def is_jwt_token_valid(access_token):

    url = f"{os.getenv('BACKEND_BASE_URL')}/api/auth/me"
    headers = {"Authorization": f"Bearer {access_token}"}

    res = requests.get(url, headers=headers, timeout=5)

    if res.status_code == 200:
        return True

#===========jwt token refresh===============
def get_new_jwt_token():
    url = f"{os.getenv('BACKEND_BASE_URL')}/api/auth/refresh"
    payload = {
        "refreshToken": os.getenv("JWT_REFRESH_TOKEN")
        }

    res = requests.post(url, json=payload, timeout=10)
    if res.status_code == 200:
        return res.json()


#===========kakao token validation===============
def is_kakao_token_valid(access_token):

    url = "https://kapi.kakao.com/v2/user/me"
    headers = {"Authorization": f"Bearer {access_token}"}

    res = requests.get(url, headers=headers, timeout=5)

    if res.status_code == 200:
        return True

#===========kakao token refresh===============
def get_new_kakao_token():
    url = "https://kauth.kakao.com/oauth/token"  # 카카오 토큰 갱신 URL
    data = {
        'grant_type': 'refresh_token',
        'client_id': os.getenv("KAKAO_REST_API_KEY"),  # 카카오 개발자 콘솔에서 발급받은 client_id
        'refresh_token': os.getenv("KAKAO_REFRESH_TOKEN")  # 기존의 refresh_token
    }

    # POST 요청을 통해 새로운 토큰을 요청
    res = requests.post(url, data=data)

    # 요청이 성공하면 응답 반환
    if res.status_code == 200:
        return res.json()  # 새로운 access_token 반환


#===========naver token validation===============
def is_naver_token_valid(access_token):

    url = "https://openapi.naver.com/v1/nid/me"
    headers = {"Authorization": f"Bearer {access_token}"}

    res = requests.get(url, headers=headers, timeout=5)

    if res.status_code == 200:
        return True

#===========naver token refresh===============
def get_new_naver_token():
    url = "https://nid.naver.com/oauth2.0/token"
    data = {
        'grant_type': 'refresh_token',
        'client_id': os.getenv("NAVER_CLIENT_ID"),
        'client_secret': os.getenv("NAVER_CLIENT_SECRET"),
        'refresh_token': os.getenv("NAVER_REFRESH_TOKEN")
    }

    # POST 요청을 통해 새로운 토큰을 요청
    res = requests.post(url, data=data)

    # 요청이 성공하면 응답 반환
    if res.status_code == 200:
        return res.json()


#===========post token to jenkins===============
def post_token_to_jenkins(credential_id, token):
    """
    Jenkins에 토큰을 POST 요청으로 업데이트하는 함수
    :param credential_id: 토큰의 ID (JWT_TOKEN, JWT_REFRESH_TOKEN 등)
    :param token: 토큰 값
    :param user: Jenkins 사용자 이름
    :param password: Jenkins 비밀번호
    :return: 요청의 응답 객체
    """
    url = f"{jenkins_url}/credentials/store/system/domain/{credential_domain}/credential/{credential_id}"
    headers = {"Content-Type": "application/json"}
    auth = HTTPBasicAuth(user, password)
    data = json.dumps({
        "credentials": {
            "scope": "GLOBAL",
            "id": credential_id,
            "secret": token,
            "$class": "org.jenkinsci.plugins.plaincredentials.impl.StringCredentialsImpl"
        }
    })
    return requests.post(url, headers=headers, auth=auth, data=data)


if __name__ == "__main__":

    # ======================= jwt token =======================
    new_jwt_token = get_new_jwt_token()
    new_jwt_token_valid = is_jwt_token_valid(new_jwt_token["token"])

    if new_jwt_token_valid:

        # POST 요청
        jwt_access_token_response = post_token_to_jenkins("JWT_TOKEN", new_jwt_token["token"])
        jwt_refresh_token_response = post_token_to_jenkins("JWT_REFRESH_TOKEN", new_jwt_token["refreshToken"])

        if jwt_access_token_response.status_code == 200 and jwt_refresh_token_response.status_code == 200:
            print("JWT Token 업데이트 성공")
        else:
            print("JWT Token 업데이트 실패")


    # ======================= kakao token =======================
    new_kakao_token = get_new_kakao_token()
    new_kakao_token_valid = is_kakao_token_valid(new_kakao_token["access_token"])

    if new_kakao_token_valid:

        # POST 요청
        kakao_access_token_response = post_token_to_jenkins("KAKAO_ACCESS_TOKEN", new_kakao_token["access_token"])

        if kakao_access_token_response.status_code == 200:
            print("Kakao Token 업데이트 성공")
        else:
            print("Kakao Token 업데이트 실패")


    # ======================= naver token =======================
    new_naver_token = get_new_naver_token()
    new_naver_token_valid = is_naver_token_valid(new_naver_token["access_token"])

    if new_naver_token_valid:

        # POST 요청
        naver_access_token_response = post_token_to_jenkins("NAVER_ACCESS_TOKEN", new_naver_token["access_token"])
        naver_refresh_token_response = post_token_to_jenkins("NAVER_REFRESH_TOKEN", new_naver_token["refresh_token"])

        if naver_access_token_response.status_code == 200 and naver_refresh_token_response.status_code == 200:
            print("Naver Token 업데이트 성공")
        else:
            print("Naver Token 업데이트 실패")