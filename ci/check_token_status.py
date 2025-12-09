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





def is_kakao_token_valid(access_token):

    url = "https://kapi.kakao.com/v2/user/me"
    headers = {"Authorization": f"Bearer {access_token}"}

    res = requests.get(url, headers=headers, timeout=5)

    if res.status_code == 200:
        return True
    else:
        return False 


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
        return res.json()  # 새로운 access_token과 refresh_token 포함된 응답 반환



def is_naver_token_valid(access_token):

    url = "https://openapi.naver.com/v1/nid/me"
    headers = {"Authorization": f"Bearer {access_token}"}

    res = requests.get(url, headers=headers, timeout=5)

    if res.status_code == 200:
        return True
    else:
        return False


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


if __name__ == "__main__":

    # ======================= kakao token =======================
    new_kakao_token = get_new_kakao_token()
    print("new_kakao_token: ", new_kakao_token)
    new_kakao_token_valid = is_kakao_token_valid(new_kakao_token["access_token"])
    print("new_kakao_token_valid: ", new_kakao_token_valid)

    if new_kakao_token_valid:
        new_kakao_access_token = new_kakao_token["access_token"]
        new_kakao_refresh_token = new_kakao_token["refresh_token"]

        # POST 요청을 보내는 부분
        kakao_access_token_url = f"{jenkins_url}/credentials/store/system/domain/{credential_domain}/credential/KAKAO_ACCESS_TOKEN"
        kakao_refresh_token_url = f"{jenkins_url}/credentials/store/system/domain/{credential_domain}/credential/KAKAO_REFRESH_TOKEN"
        headers = {
            "Content-Type": "application/json"
        }

        # 인증 정보 (기본 인증)
        auth = HTTPBasicAuth(user, password)

        # POST 요청
        kakao_access_token_response = requests.post(kakao_access_token_url, headers=headers, auth=auth, data=json.dumps({"credentials": {"scope": "GLOBAL", "id": "KAKAO_ACCESS_TOKEN", "secret": new_kakao_access_token, "$class": "org.jenkinsci.plugins.plaincredentials.impl.StringCredentialsImpl"}}))
        kakao_refresh_token_response = requests.post(kakao_refresh_token_url, headers=headers, auth=auth, data=json.dumps({"credentials": {"scope": "GLOBAL", "id": "KAKAO_REFRESH_TOKEN", "secret": new_kakao_refresh_token, "$class": "org.jenkinsci.plugins.plaincredentials.impl.StringCredentialsImpl"}}))

        print("kakao_access_token_response.status_code: ", kakao_access_token_response.status_code)
        print("kakao_refresh_token_response.status_code: ", kakao_refresh_token_response.status_code)
        if kakao_access_token_response.status_code == 200 and kakao_refresh_token_response.status_code == 200:
            print("Kakao Token 업데이트 성공")
        else:
            print("Kakao Token 업데이트 실패")




    # ======================= naver token =======================
    new_naver_token = get_new_naver_token()
    new_naver_token_valid = is_naver_token_valid(new_naver_token["access_token"])

    if new_naver_token_valid:
        new_naver_access_token = new_naver_token["access_token"]
        new_naver_refresh_token = new_naver_token["refresh_token"]

        # POST 요청을 보내는 부분
        naver_access_token_url = f"{jenkins_url}/credentials/store/system/domain/{credential_domain}/credential/NAVER_ACCESS_TOKEN"
        naver_refresh_token_url = f"{jenkins_url}/credentials/store/system/domain/{credential_domain}/credential/NAVER_REFRESH_TOKEN"
        headers = {
            "Content-Type": "application/json"
        }

        # 인증 정보 (기본 인증)
        auth = HTTPBasicAuth(user, password)

        # POST 요청
        naver_access_token_response = requests.post(naver_access_token_url, headers=headers, auth=auth, data=json.dumps({"credentials": {"scope": "GLOBAL", "id": "NAVER_ACCESS_TOKEN", "secret": new_naver_access_token, "$class": "org.jenkinsci.plugins.plaincredentials.impl.StringCredentialsImpl"}}))
        naver_refresh_token_response = requests.post(naver_refresh_token_url, headers=headers, auth=auth, data=json.dumps({"credentials": {"scope": "GLOBAL", "id": "NAVER_REFRESH_TOKEN", "secret": new_naver_refresh_token, "$class": "org.jenkinsci.plugins.plaincredentials.impl.StringCredentialsImpl"}}))

        print("naver_access_token_response.status_code: ", naver_access_token_response.status_code)
        print("naver_refresh_token_response.status_code: ", naver_refresh_token_response.status_code)
        if naver_access_token_response.status_code == 200 and naver_refresh_token_response.status_code == 200:
            print("Naver Token 업데이트 성공")
        else:
            print("Naver Token 업데이트 실패")