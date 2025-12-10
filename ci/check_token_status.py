"""
토큰 상태 확인 및 갱신 유틸리티
"""
import os
import sys
from pathlib import Path
from requests.auth import HTTPBasicAuth
import requests

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.utils.env_loader import load_env_files

load_env_files()


jenkins_url = "http://3.36.219.242:8080"
credential_domain = "todolist_dev"
user = os.getenv("JENKINS_USER")
password = os.getenv("JENKINS_PASS")


def is_jwt_token_valid(access_token):
    """JWT 토큰 유효성 검증"""
    url = f"{os.getenv('BACKEND_BASE_URL')}/api/auth/me"
    headers = {"Authorization": f"Bearer {access_token}"}
    res = requests.get(url, headers=headers, timeout=5)
    
    if res.status_code == 200:
        return True


def get_new_jwt_token():
    """JWT 토큰 갱신"""
    url = f"{os.getenv('BACKEND_BASE_URL')}/api/auth/refresh"
    payload = {"refreshToken": os.getenv("JWT_REFRESH_TOKEN")}
    res = requests.post(url, json=payload, timeout=10)
    if res.status_code == 200:
        return res.json()


def is_kakao_token_valid(access_token):
    """Kakao 토큰 유효성 검증"""
    url = "https://kapi.kakao.com/v2/user/me"
    headers = {"Authorization": f"Bearer {access_token}"}
    res = requests.get(url, headers=headers, timeout=5)
    
    if res.status_code == 200:
        return True


def get_new_kakao_token():
    """Kakao 토큰 갱신"""
    url = "https://kauth.kakao.com/oauth/token"
    data = {
        'grant_type': 'refresh_token',
        'client_id': os.getenv("KAKAO_REST_API_KEY"),
        'refresh_token': os.getenv("KAKAO_REFRESH_TOKEN")
    }
    
    res = requests.post(url, data=data)
    if res.status_code == 200:
        return res.json()


def is_naver_token_valid(access_token):
    """Naver 토큰 유효성 검증"""
    url = "https://openapi.naver.com/v1/nid/me"
    headers = {"Authorization": f"Bearer {access_token}"}
    res = requests.get(url, headers=headers, timeout=5)
    
    if res.status_code == 200:
        return True


def get_new_naver_token():
    """Naver 토큰 갱신"""
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


def post_token_to_jenkins(credential_id, token):
    """Jenkins Credential 업데이트"""
    url = f"{jenkins_url}/credentials/store/system/domain/{credential_domain}/credential/{credential_id}/config.xml"
    headers = {"Content-Type": "application/xml"}
    auth = HTTPBasicAuth(user, password)
    
    xml_data = f"""<?xml version='1.1' encoding='UTF-8'?>
<org.jenkinsci.plugins.plaincredentials.impl.StringCredentialsImpl plugin="plain-credentials@182.v468b_97b_9dcb_8">
  <scope>GLOBAL</scope>
  <id>{credential_id}</id>
  <description></description>
  <secret>{token}</secret>
</org.jenkinsci.plugins.plaincredentials.impl.StringCredentialsImpl>"""
    
    return requests.post(url, headers=headers, auth=auth, data=xml_data)


if __name__ == "__main__":
    # JWT token
    new_jwt_token = get_new_jwt_token()
    new_jwt_token_valid = is_jwt_token_valid(new_jwt_token["token"])

    if new_jwt_token_valid:
        jwt_access_token_response = post_token_to_jenkins("JWT_TOKEN", new_jwt_token["token"])
        jwt_refresh_token_response = post_token_to_jenkins("JWT_REFRESH_TOKEN", new_jwt_token["refreshToken"])
        
        if jwt_access_token_response.status_code == 200 and jwt_refresh_token_response.status_code == 200:
            print("JWT Token 업데이트 성공")
        else:
            print(f"JWT Token 업데이트 실패 - Status: {jwt_access_token_response.status_code}, {jwt_refresh_token_response.status_code}")
            print(f"Response: {jwt_access_token_response.text[:100]}")

    # Kakao token
    new_kakao_token = get_new_kakao_token()
    
    if new_kakao_token is None:
        print("Kakao Token 갱신 실패")
    else:
        new_kakao_token_valid = is_kakao_token_valid(new_kakao_token["access_token"])

        if new_kakao_token_valid:
            kakao_access_token_response = post_token_to_jenkins("KAKAO_ACCESS_TOKEN", new_kakao_token["access_token"])
            
            if kakao_access_token_response.status_code == 200:
                print("Kakao Token 업데이트 성공")
            else:
                print(f"Kakao Token 업데이트 실패 - Status: {kakao_access_token_response.status_code}")
                print(f"Response: {kakao_access_token_response.text[:100]}")
        else:
            print("Kakao Token 유효성 검증 실패")

    # Naver token
    new_naver_token = get_new_naver_token()
    new_naver_token_valid = is_naver_token_valid(new_naver_token["access_token"])

    if new_naver_token_valid:
        naver_access_token_response = post_token_to_jenkins("NAVER_ACCESS_TOKEN", new_naver_token["access_token"])
        naver_refresh_token_response = post_token_to_jenkins("NAVER_REFRESH_TOKEN", new_naver_token["refresh_token"])
        
        if naver_access_token_response.status_code == 200 and naver_refresh_token_response.status_code == 200:
            print("Naver Token 업데이트 성공")
        else:
            print(f"Naver Token 업데이트 실패 - Status: {naver_access_token_response.status_code}, {naver_refresh_token_response.status_code}")
            print(f"Response: {naver_access_token_response.text[:100]}")