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
    :return: 요청의 응답 객체
    """
    # Jenkins Credential API는 config.xml 형식 사용
    url = f"{jenkins_url}/credentials/store/system/domain/{credential_domain}/credential/{credential_id}/config.xml"
    headers = {"Content-Type": "application/xml"}
    auth = HTTPBasicAuth(user, password)
    
    # XML 형식으로 credential 업데이트
    xml_data = f"""<?xml version='1.1' encoding='UTF-8'?>
<org.jenkinsci.plugins.plaincredentials.impl.StringCredentialsImpl plugin="plain-credentials@182.v468b_97b_9dcb_8">
  <scope>GLOBAL</scope>
  <id>{credential_id}</id>
  <description></description>
  <secret>{token}</secret>
</org.jenkinsci.plugins.plaincredentials.impl.StringCredentialsImpl>"""
    
    return requests.post(url, headers=headers, auth=auth, data=xml_data)


if __name__ == "__main__":

    # ======================= jwt token =======================
    new_jwt_token = get_new_jwt_token()
    new_jwt_token_valid = is_jwt_token_valid(new_jwt_token["token"])

    if new_jwt_token_valid:

        # POST 요청
        jwt_access_token_response = post_token_to_jenkins("JWT_TOKEN", new_jwt_token["token"])
        jwt_refresh_token_response = post_token_to_jenkins("JWT_REFRESH_TOKEN", new_jwt_token["refreshToken"])

        print(f"[DEBUG] JWT_TOKEN API Status: {jwt_access_token_response.status_code}")
        print(f"[DEBUG] JWT_REFRESH_TOKEN API Status: {jwt_refresh_token_response.status_code}")
        
        if jwt_access_token_response.status_code == 200 and jwt_refresh_token_response.status_code == 200:
            print("✅ JWT Token 업데이트 성공")
        else:
            print(f"❌ JWT Token 업데이트 실패 - JWT: {jwt_access_token_response.status_code}, Refresh: {jwt_refresh_token_response.status_code}")


    # ======================= kakao token =======================
    print(f"[DEBUG] KAKAO_REST_API_KEY 존재 여부: {os.getenv('KAKAO_REST_API_KEY') is not None}")
    print(f"[DEBUG] KAKAO_REFRESH_TOKEN 존재 여부: {os.getenv('KAKAO_REFRESH_TOKEN') is not None}")
    
    new_kakao_token = get_new_kakao_token()
    
    if new_kakao_token is None:
        print("❌ Kakao Token 갱신 실패 - get_new_kakao_token()이 None을 반환했습니다.")
        print(f"[DEBUG] 현재 KAKAO_ACCESS_TOKEN: {os.getenv('KAKAO_ACCESS_TOKEN')[:20]}..." if os.getenv('KAKAO_ACCESS_TOKEN') else "None")
    else:
        print(f"[DEBUG] 새로운 Kakao access_token: {new_kakao_token.get('access_token', 'N/A')[:20]}...")
        new_kakao_token_valid = is_kakao_token_valid(new_kakao_token["access_token"])

        if new_kakao_token_valid:

            # POST 요청
            kakao_access_token_response = post_token_to_jenkins("KAKAO_ACCESS_TOKEN", new_kakao_token["access_token"])

            print(f"[DEBUG] Jenkins API Response Status: {kakao_access_token_response.status_code}")
            print(f"[DEBUG] Jenkins API Response Body: {kakao_access_token_response.text[:200]}")
            
            if kakao_access_token_response.status_code == 200:
                print("✅ Kakao Token 업데이트 성공")
            else:
                print(f"❌ Kakao Token 업데이트 실패 - Status: {kakao_access_token_response.status_code}")
        else:
            print("❌ 새로운 Kakao Token이 유효하지 않습니다.")


    # ======================= naver token =======================
    new_naver_token = get_new_naver_token()
    new_naver_token_valid = is_naver_token_valid(new_naver_token["access_token"])

    if new_naver_token_valid:

        # POST 요청
        naver_access_token_response = post_token_to_jenkins("NAVER_ACCESS_TOKEN", new_naver_token["access_token"])
        naver_refresh_token_response = post_token_to_jenkins("NAVER_REFRESH_TOKEN", new_naver_token["refresh_token"])

        print(f"[DEBUG] NAVER_ACCESS_TOKEN API Status: {naver_access_token_response.status_code}")
        print(f"[DEBUG] NAVER_REFRESH_TOKEN API Status: {naver_refresh_token_response.status_code}")
        
        if naver_access_token_response.status_code == 200 and naver_refresh_token_response.status_code == 200:
            print("✅ Naver Token 업데이트 성공")
        else:
            print(f"❌ Naver Token 업데이트 실패 - Access: {naver_access_token_response.status_code}, Refresh: {naver_refresh_token_response.status_code}")