"""소셜 로그인(Kakao / Naver) 테스트"""
import os
import pytest_check as check
from src.actions.api.base_api import LoginAPI

BASE_URL = os.getenv("BACKEND_BASE_URL")


def test_kakao_login():
    """Kakao AccessToken으로 JWT 발급 여부 확인"""
    access_token = os.getenv("KAKAO_ACCESS_TOKEN")

    res = LoginAPI(BASE_URL).request_social_login("kakao", access_token)
    body = res.json()

    check.equal(res.status_code, 200, "Kakao 로그인 응답 코드가 200이 아닙니다.")
    check.is_in("token", body, "'token' 키가 없습니다.")
    check.is_in("refreshToken", body, "'refreshToken' 키가 없습니다.")
    check.not_equal(body.get("token", ""), "", "'token' 값이 비어있습니다.")
    check.not_equal(body.get("refreshToken", ""), "", "'refreshToken' 값이 비어있습니다.")


def test_naver_login():
    """Naver AccessToken으로 JWT 발급 여부 확인"""
    access_token = os.getenv("NAVER_ACCESS_TOKEN")

    res = LoginAPI(BASE_URL).request_social_login("naver", access_token)
    body = res.json()

    check.equal(res.status_code, 200, "Naver 로그인 응답 코드가 200이 아닙니다.")
    check.is_in("token", body, "'token' 키가 없습니다.")
    check.is_in("refreshToken", body, "'refreshToken' 키가 없습니다.")
    check.not_equal(body.get("token", ""), "", "'token' 값이 비어있습니다.")
    check.not_equal(body.get("refreshToken", ""), "", "'refreshToken' 값이 비어있습니다.")
