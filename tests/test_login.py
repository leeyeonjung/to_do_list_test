"""소셜 로그인(Kakao / Naver) 테스트"""
import pytest_check as check

from src.utils.token_validator import ensure_valid_kakao_token, ensure_valid_naver_token


def test_kakao_login(api_base_url):
    """
    Kakao AccessToken/RefreshToken을 사용하여 JWT 발급 성공 여부 확인
    
    .env의 KAKAO_ACCESS_TOKEN, KAKAO_REFRESH_TOKEN을 사용하여
    백엔드 API를 통해 JWT를 발급받고, 성공적으로 응답이 오면 테스트 통과
    """
    # Kakao JWT 토큰 가져오기
    kakao_jwt = ensure_valid_kakao_token(backend_base_url=api_base_url)
    
    # JWT 토큰이 성공적으로 발급되었는지 확인
    check.is_not_none(kakao_jwt, "Kakao JWT 토큰이 발급되지 않았습니다.")
    check.not_equal(kakao_jwt, "", "Kakao JWT 토큰이 비어있습니다.")


def test_naver_login(api_base_url):
    """
    Naver AccessToken/RefreshToken을 사용하여 JWT 발급 성공 여부 확인
    
    .env의 NAVER_ACCESS_TOKEN, NAVER_REFRESH_TOKEN을 사용하여
    백엔드 API를 통해 JWT를 발급받고, 성공적으로 응답이 오면 테스트 통과
    """
    # Naver JWT 토큰 가져오기
    naver_jwt = ensure_valid_naver_token(backend_base_url=api_base_url)
    
    # JWT 토큰이 성공적으로 발급되었는지 확인
    check.is_not_none(naver_jwt, "Naver JWT 토큰이 발급되지 않았습니다.")
    check.not_equal(naver_jwt, "", "Naver JWT 토큰이 비어있습니다.")
