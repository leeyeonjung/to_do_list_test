"""
토큰 상태 확인 유틸리티
"""

import logging
import os
from requests.auth import HTTPBasicAuth
import json
import requests
from ..src.utils.env_loader import load_env_files

# .env 파일 로드
load_env_files()

log = logging.getLogger(__name__)


jenkins_url = "http://3.36.219.242:8080"
credential_domain = "todolist_dev"
user = os.getenv("USER")
password = os.getenv("PASSWORD")


def is_token_valid(access_token):

    url = "https://openapi.naver.com/v1/nid/me"
    headers = {"Authorization": f"Bearer {access_token}"}

    res = requests.get(url, headers=headers, timeout=5)

    if res.status_code == 200:
        return True
    else:
        return False


def get_new_token():
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


if __name__ == "__main__":
    new_token = get_new_token()
    
    new_token_valid = is_token_valid(new_token["access_token"])

    if new_token_valid:
        new_naver_access_token = new_token["access_token"]
        new_naver_refresh_token = new_token["refresh_token"]

        # POST 요청을 보내는 부분
        access_token_url = f"{jenkins_url}/credentials/store/system/domain/{credential_domain}/credential/api_access_token"
        refresh_token_url = f"{jenkins_url}/credentials/store/system/domain/{credential_domain}/credential/api_refresh_token"
        headers = {
            "Content-Type": "application/json"
        }

        # 인증 정보 (기본 인증)
        auth = HTTPBasicAuth(user, password)

        # POST 요청
        access_token_response = requests.post(access_token_url, headers=headers, auth=auth, data=json.dumps({"credentials": {"scope": "GLOBAL", "id": "api_access_token", "secret": new_naver_access_token, "$class": "org.jenkinsci.plugins.plaincredentials.impl.StringCredentialsImpl"}}))
        refresh_token_response = requests.post(refresh_token_url, headers=headers, auth=auth, data=json.dumps({"credentials": {"scope": "GLOBAL", "id": "api_refresh_token", "secret": new_naver_refresh_token, "$class": "org.jenkinsci.plugins.plaincredentials.impl.StringCredentialsImpl"}}))

        print(access_token_response.status_code)
        print(refresh_token_response.status_code)
        if access_token_response.status_code == 200 and refresh_token_response.status_code == 200:
            print("Naver Token 업데이트 성공")
        else:
            print("Naver Token 업데이트 실패")

        print(new_token["access_token"])
        print(new_token["refresh_token"])
