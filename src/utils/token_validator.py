"""JWT, Kakao, Naver 토큰 유효성 검증 및 갱신 유틸리티"""
import argparse
import json
import logging
import os
import re
from pathlib import Path
from typing import Dict, Optional, Tuple

import requests
from dotenv import load_dotenv

log = logging.getLogger(__name__)


# Utility Functions
def get_env_value(env_path: Path, key: str) -> Optional[str]:
    """
    .env 파일에서 환경 변수 값을 읽어옴
    값에 '=' 기호가 포함되어 있어도 정상적으로 읽을 수 있음
    
    Args:
        env_path: .env 파일 경로
        key: 환경 변수 키
        
    Returns:
        환경 변수 값, 없으면 None
    """
    if not env_path.exists():
        return None
    
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            # 주석이나 빈 줄 건너뛰기
            if not line or line.startswith("#"):
                continue
            
            # 첫 번째 '='를 기준으로 키와 값 분리
            if "=" in line:
                key_part, value_part = line.split("=", 1)
                key_part = key_part.strip()
                
                if key_part == key:
                    # 따옴표 제거 (있는 경우)
                    value = value_part.strip()
                    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
                        value = value[1:-1]
                    return value
    
    return None


# JWT Token Functions
def get_jwt_token(
    backend_base_url: str,
    user_id: int,
    email: Optional[str] = None,
    provider: str = "test",
    endpoint: str = "/api/auth/test-token",
) -> Dict[str, any]:
    """
    API를 통해 JWT 토큰을 요청

    Args:
        backend_base_url: 백엔드 기본 URL
        user_id: 사용자 ID (필수)
        email: 이메일 (선택)
        provider: 제공자 (기본값: "test")
        endpoint: 토큰 요청 엔드포인트 (기본값: "/api/auth/test-token")

    Returns:
        dict: {"token": str, "payload": dict} 형식의 응답 데이터
    """
    url = f"{backend_base_url.rstrip('/')}/{endpoint.lstrip('/')}"

    # 요청 Body 구성
    payload: Dict[str, object] = {
        "id": user_id,
        "provider": provider,
    }

    if email:
        payload["email"] = email

    headers = {
        "Content-Type": "application/json",
    }

    log.info(f"JWT 토큰 요청: {url}")
    log.debug(f"Request payload: {payload}")

    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code != 200:
        log.error(f"JWT 토큰 요청 실패: {response.status_code} - {response.text}")
        return {}

    data = response.json()

    if "token" not in data:
        log.error("응답에 'token' 필드가 없습니다.")
        return {}

    log.info("JWT 토큰 요청 성공")
    return data


def update_jwt_env_file(
    env_path: Path,
    token: str,
    user_payload: Dict,
) -> None:
    """
    .env 파일의 WEB_TEST_JWT_TOKEN와 WEB_TEST_JWT_USER 값을 업데이트

    Args:
        env_path: .env 파일 경로
        token: JWT 토큰 문자열
        user_payload: 사용자 정보 딕셔너리 (payload)
    """
    if not env_path.exists():
        log.error(f".env 파일을 찾을 수 없습니다: {env_path}")
        return

    # .env 파일 읽기
    with open(env_path, "r", encoding="utf-8") as f:
        content = f.read()

    # WEB_TEST_JWT_TOKEN 업데이트
    token_pattern = r"^WEB_TEST_JWT_TOKEN=.*$"
    token_replacement = f"WEB_TEST_JWT_TOKEN={token}"

    if re.search(token_pattern, content, re.MULTILINE):
        content = re.sub(token_pattern, token_replacement, content, flags=re.MULTILINE)
    else:
        # 없으면 추가
        content += f"\nWEB_TEST_JWT_TOKEN={token}\n"

    # WEB_TEST_JWT_USER 업데이트 (JSON 문자열로 변환)
    user_json = json.dumps(user_payload, ensure_ascii=False)
    user_pattern = r"^WEB_TEST_JWT_USER=.*$"
    user_replacement = f"WEB_TEST_JWT_USER={user_json}"

    if re.search(user_pattern, content, re.MULTILINE):
        content = re.sub(user_pattern, user_replacement, content, flags=re.MULTILINE)
    else:
        # 없으면 추가
        content += f"\nWEB_TEST_JWT_USER={user_json}\n"

    # .env 파일 쓰기
    with open(env_path, "w", encoding="utf-8") as f:
        f.write(content)

    log.info(f".env 파일 업데이트 완료: {env_path}")


def validate_jwt_token(
    backend_base_url: str,
    token: str,
    endpoint: str = "/api/auth/me"
) -> Tuple[bool, Optional[Dict]]:
    """
    JWT 토큰의 유효성을 검증

    Args:
        backend_base_url: 백엔드 기본 URL
        token: 검증할 JWT 토큰
        endpoint: 토큰 검증 엔드포인트 (기본값: "/api/auth/me")

    Returns:
        tuple: (is_valid: bool, user_data: Optional[Dict])
        - is_valid: 토큰이 유효하면 True, 아니면 False
        - user_data: 토큰이 유효할 경우 사용자 정보, 아니면 None
    """
    url = f"{backend_base_url.rstrip('/')}/{endpoint.lstrip('/')}"
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    log.info(f"JWT 토큰 유효성 검증: {url}")
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        user_data = response.json()
        log.info("JWT 토큰이 유효합니다.")
        return True, user_data
    elif response.status_code == 401:
        log.warning("JWT 토큰이 유효하지 않거나 만료되었습니다.")
        return False, None
    else:
        log.warning(f"토큰 검증 중 예상치 못한 상태 코드: {response.status_code}")
        return False, None


def fetch_and_update_jwt_token(
    user_id: int,
    email: Optional[str] = None,
    provider: str = "test",
    backend_base_url: Optional[str] = None,
    endpoint: str = "/api/auth/test-token",
    env_path: Optional[Path] = None,
) -> Dict[str, any]:
    """
    JWT 토큰을 요청하고 .env 파일을 업데이트하는 통합 함수

    Args:
        user_id: 사용자 ID (필수)
        email: 이메일 (선택)
        provider: 제공자 (기본값: "test")
        backend_base_url: 백엔드 기본 URL (None이면 .env에서 로드)
        endpoint: 토큰 요청 엔드포인트 (기본값: "/api/auth/test-token")
        env_path: .env 파일 경로 (None이면 프로젝트 루트의 .env 사용)

    Returns:
        dict: {"token": str, "payload": dict} 형식의 응답 데이터
    """
    # .env 파일 경로 설정
    if env_path is None:
        env_path = Path(__file__).resolve().parent.parent.parent / ".env"

    # 백엔드 기본 URL 설정
    if backend_base_url is None:
        load_dotenv(env_path)
        backend_base_url = os.getenv("BACKEND_BASE_URL")
        if not backend_base_url:
            log.error("BACKEND_BASE_URL이 .env 파일에 설정되어 있지 않습니다.")
            return {}

    # JWT 토큰 요청
    response_data = get_jwt_token(
        backend_base_url=backend_base_url,
        user_id=user_id,
        email=email,
        provider=provider,
        endpoint=endpoint,
    )

    token = response_data.get("token")
    payload = response_data.get("payload", {})

    if not token:
        log.error("JWT 토큰 응답에 token 필드가 없거나 비어 있습니다.")
        return {}

    # .env 파일 업데이트
    update_jwt_env_file(
        env_path=env_path,
        token=token,
        user_payload=payload,
    )

    log.info("JWT 토큰 요청 및 .env 파일 업데이트 완료")
    return response_data


def ensure_valid_jwt_token(
    user_id: int,
    email: Optional[str] = None,
    provider: str = "test",
    backend_base_url: Optional[str] = None,
    token_endpoint: str = "/api/auth/test-token",
    validate_endpoint: str = "/api/auth/me",
    env_path: Optional[Path] = None
) -> str:
    """
    JWT 토큰이 유효한지 확인하고, 유효하지 않으면 새로 발급받아 .env에 업데이트

    Args:
        user_id: 사용자 ID (필수)
        email: 이메일 (선택)
        provider: 제공자 (기본값: "test")
        backend_base_url: 백엔드 기본 URL (None이면 .env에서 로드)
        token_endpoint: 토큰 발급 엔드포인트 (기본값: "/api/auth/test-token")
        validate_endpoint: 토큰 검증 엔드포인트 (기본값: "/api/auth/me")
        env_path: .env 파일 경로 (None이면 프로젝트 루트의 .env 사용)

    Returns:
        str: 유효한 JWT 토큰
    """
    # .env 파일 경로 설정
    if env_path is None:
        env_path = Path(__file__).resolve().parent.parent.parent / ".env"
    
    # 백엔드 기본 URL 설정
    if backend_base_url is None:
        load_dotenv(env_path)
        backend_base_url = os.getenv("BACKEND_BASE_URL")
        if not backend_base_url:
            log.error("BACKEND_BASE_URL이 .env 파일에 설정되어 있지 않습니다.")
            return ""
    
    # .env에서 기존 토큰 확인
    load_dotenv(env_path)
    existing_token = os.getenv("WEB_TEST_JWT_TOKEN")
    
    # 기존 토큰이 있고 유효한지 확인
    if existing_token:
        is_valid, _ = validate_jwt_token(
            backend_base_url=backend_base_url,
            token=existing_token,
            endpoint=validate_endpoint
        )
        
        if is_valid:
            log.info("기존 JWT 토큰이 유효합니다. 새로 발급받지 않습니다.")
            return existing_token
    
    # 토큰이 없거나 유효하지 않으면 새로 발급
    log.info("JWT 토큰이 없거나 유효하지 않습니다. 새로 발급받습니다.")
    response_data = fetch_and_update_jwt_token(
        user_id=user_id,
        email=email,
        provider=provider,
        backend_base_url=backend_base_url,
        endpoint=token_endpoint,
        env_path=env_path,
    )
    
    if not response_data or "token" not in response_data:
        log.error("JWT 토큰 발급에 실패했습니다.")
        return ""
    
    return response_data["token"]


# OAuth Token Functions (Common)
def validate_oauth_token(
    backend_base_url: str,
    access_token: str,
    provider: str,
    endpoint: str
) -> Tuple[bool, Optional[Dict]]:
    """
    OAuth AccessToken을 백엔드 API로 검증하여 JWT 토큰 발급 (공통 함수)

    Args:
        backend_base_url: 백엔드 기본 URL
        access_token: OAuth AccessToken
        provider: OAuth 제공자 이름 (예: "kakao", "naver")
        endpoint: 토큰 검증 엔드포인트

    Returns:
        tuple: (is_valid: bool, response_data: Optional[Dict])
        - is_valid: 토큰이 유효하면 True, 아니면 False
        - response_data: {"token": str, "user": dict} 형식의 응답 데이터, 실패 시 None
    """
    url = f"{backend_base_url.rstrip('/')}/{endpoint.lstrip('/')}"
    
    headers = {
        "Content-Type": "application/json"
    }
    
    payload = {
        "accessToken": access_token
    }
    
    log.info(f"{provider.capitalize()} 토큰 유효성 검증: {url}")
    
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        log.info(f"{provider.capitalize()} 토큰이 유효합니다.")
        return True, data
    else:
        log.warning(f"{provider.capitalize()} 토큰 검증 실패: {response.status_code} - {response.text}")
        return False, None


def refresh_oauth_token(
    backend_base_url: str,
    refresh_token: str,
    provider: str,
    endpoint: str
) -> Optional[Dict]:
    """
    OAuth RefreshToken을 사용하여 새로운 AccessToken 발급 (공통 함수)

    Args:
        backend_base_url: 백엔드 기본 URL
        refresh_token: OAuth RefreshToken
        provider: OAuth 제공자 이름 (예: "kakao", "naver")
        endpoint: 토큰 갱신 엔드포인트

    Returns:
        dict: {"token": str, "refreshToken": str, "user": dict} 형식의 응답 데이터, 실패 시 None
    """
    url = f"{backend_base_url.rstrip('/')}/{endpoint.lstrip('/')}"
    
    headers = {
        "Content-Type": "application/json"
    }
    
    payload = {
        "refreshToken": refresh_token
    }
    
    log.info(f"{provider.capitalize()} 토큰 갱신 요청: {url}")
    
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        log.info(f"{provider.capitalize()} 토큰 갱신 성공")
        return data
    else:
        log.error(f"{provider.capitalize()} 토큰 갱신 실패: {response.status_code} - {response.text}")
        return None


def update_oauth_env_file(
    env_path: Path,
    refresh_token: Optional[str],
    provider: str
) -> None:
    """
    .env 파일의 OAuth RefreshToken 업데이트 (공통 함수)
    (WEB_TEST_JWT_TOKEN은 API 엔드포인트로만 업데이트됨)

    Args:
        env_path: .env 파일 경로
        refresh_token: OAuth RefreshToken (갱신된 경우)
        provider: OAuth 제공자 이름 (예: "kakao", "naver")
    """
    if not env_path.exists():
        log.error(f".env 파일을 찾을 수 없습니다: {env_path}")
        return
    
    if not refresh_token:
        return
    
    # .env 파일 읽기
    with open(env_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # OAuth RefreshToken 업데이트
    env_key = f"{provider.upper()}_REFRESH_TOKEN"
    refresh_token_pattern = rf"^{env_key}=.*$"
    refresh_token_replacement = f"{env_key}={refresh_token}"
    
    if re.search(refresh_token_pattern, content, re.MULTILINE):
        content = re.sub(refresh_token_pattern, refresh_token_replacement, content, flags=re.MULTILINE)
    else:
        content += f"\n{env_key}={refresh_token}\n"
    
    # .env 파일 쓰기
    with open(env_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    log.info(f".env 파일 업데이트 완료: {env_path}")


def ensure_valid_oauth_token(
    provider: str,
    backend_base_url: Optional[str] = None,
    env_path: Optional[Path] = None,
    validate_endpoint: Optional[str] = None,
    refresh_endpoint: Optional[str] = None
) -> Optional[str]:
    """
    OAuth 토큰이 유효한지 확인하고, 유효하지 않으면 RefreshToken으로 갱신하여 JWT 토큰 발급 (공통 함수)

    Args:
        provider: OAuth 제공자 이름 (예: "kakao", "naver")
        backend_base_url: 백엔드 기본 URL (None이면 .env에서 로드)
        env_path: .env 파일 경로 (None이면 프로젝트 루트의 .env 사용)
        validate_endpoint: 토큰 검증 엔드포인트 (None이면 기본값 사용)
        refresh_endpoint: 토큰 갱신 엔드포인트 (None이면 기본값 사용)

    Returns:
        str: 유효한 JWT 토큰, 실패 시 None
    """
    # .env 파일 경로 설정
    if env_path is None:
        env_path = Path(__file__).resolve().parent.parent.parent / ".env"
    
    # .env 파일 로드
    load_dotenv(env_path)
    
    # 백엔드 기본 URL 설정
    if backend_base_url is None:
        backend_base_url = os.getenv("BACKEND_BASE_URL")
        if not backend_base_url:
            log.error("BACKEND_BASE_URL이 .env 파일에 설정되어 있지 않습니다.")
            return None
    
    # 엔드포인트 기본값 설정
    if validate_endpoint is None:
        validate_endpoint = f"/api/auth/{provider}"
    if refresh_endpoint is None:
        refresh_endpoint = f"/api/auth/{provider}/refresh"
    
    # OAuth 토큰 정보 로드 (값에 '=' 기호가 포함될 수 있으므로 직접 파싱)
    provider_upper = provider.upper()
    access_token = get_env_value(env_path, f"{provider_upper}_ACCESS_TOKEN")
    refresh_token = get_env_value(env_path, f"{provider_upper}_REFRESH_TOKEN")
    
    if not access_token:
        log.error(f"{provider_upper}_ACCESS_TOKEN이 .env 파일에 설정되어 있지 않습니다.")
        return None
    
    # 기존 AccessToken으로 검증
    is_valid, response_data = validate_oauth_token(
        backend_base_url=backend_base_url,
        access_token=access_token,
        provider=provider,
        endpoint=validate_endpoint,
    )
    
    if is_valid and response_data:
        token = response_data.get("token")
        if token:
            log.info(f"기존 {provider.capitalize()} 토큰이 유효합니다.")
            return token
    
    # 토큰이 유효하지 않으면 RefreshToken으로 갱신 시도
    if not refresh_token:
        log.error(f"{provider_upper}_REFRESH_TOKEN이 .env 파일에 설정되어 있지 않습니다.")
        return None
    
    log.info(f"{provider.capitalize()} 토큰이 유효하지 않습니다. RefreshToken으로 갱신합니다.")
    refresh_response = refresh_oauth_token(
        backend_base_url=backend_base_url,
        refresh_token=refresh_token,
        provider=provider,
        endpoint=refresh_endpoint,
    )
    
    if not refresh_response:
        log.error(f"{provider.capitalize()} 토큰 갱신에 실패했습니다.")
        return None
    
    # 갱신된 토큰 정보 추출
    new_token = refresh_response.get("token")
    new_refresh_token = refresh_response.get("refreshToken")
    
    if new_token:
        if new_refresh_token:
            update_oauth_env_file(env_path, refresh_token=new_refresh_token, provider=provider)
        log.info(f"{provider.capitalize()} 토큰 갱신 및 JWT 토큰 발급 완료")
        return new_token
    
    log.error("갱신된 응답에 JWT 토큰이 없습니다.")
    return None


# Kakao Token Functions
def validate_kakao_token(
    backend_base_url: str,
    access_token: str,
    endpoint: str = "/api/auth/kakao"
) -> Tuple[bool, Optional[Dict]]:
    """
    Kakao AccessToken을 백엔드 API로 검증하여 JWT 토큰 발급

    Args:
        backend_base_url: 백엔드 기본 URL
        access_token: Kakao AccessToken
        endpoint: 토큰 검증 엔드포인트 (기본값: "/api/auth/kakao")

    Returns:
        tuple: (is_valid: bool, response_data: Optional[Dict])
        - is_valid: 토큰이 유효하면 True, 아니면 False
        - response_data: {"token": str, "user": dict} 형식의 응답 데이터, 실패 시 None
    """
    return validate_oauth_token(
        backend_base_url=backend_base_url,
        access_token=access_token,
        provider="kakao",
        endpoint=endpoint
    )


def refresh_kakao_token(
    backend_base_url: str,
    refresh_token: str,
    endpoint: str = "/api/auth/kakao/refresh"
) -> Optional[Dict]:
    """
    Kakao RefreshToken을 사용하여 새로운 AccessToken 발급

    Args:
        backend_base_url: 백엔드 기본 URL
        refresh_token: Kakao RefreshToken
        endpoint: 토큰 갱신 엔드포인트 (기본값: "/api/auth/kakao/refresh")

    Returns:
        dict: {"token": str, "refreshToken": str, "user": dict} 형식의 응답 데이터, 실패 시 None
    """
    return refresh_oauth_token(
        backend_base_url=backend_base_url,
        refresh_token=refresh_token,
        provider="kakao",
        endpoint=endpoint
    )


def update_kakao_env_file(
    env_path: Path,
    refresh_token: Optional[str] = None
) -> None:
    """
    .env 파일의 Kakao RefreshToken 업데이트
    (WEB_TEST_JWT_TOKEN은 API 엔드포인트로만 업데이트됨)

    Args:
        env_path: .env 파일 경로
        refresh_token: Kakao RefreshToken (갱신된 경우)
    """
    update_oauth_env_file(
        env_path=env_path,
        refresh_token=refresh_token,
        provider="kakao"
    )


def ensure_valid_kakao_token(
    backend_base_url: Optional[str] = None,
    env_path: Optional[Path] = None
) -> Optional[str]:
    """
    Kakao 토큰이 유효한지 확인하고, 유효하지 않으면 RefreshToken으로 갱신하여 JWT 토큰 발급

    Args:
        backend_base_url: 백엔드 기본 URL (None이면 .env에서 로드)
        env_path: .env 파일 경로 (None이면 프로젝트 루트의 .env 사용)

    Returns:
        str: 유효한 JWT 토큰, 실패 시 None
    """
    return ensure_valid_oauth_token(
        provider="kakao",
        backend_base_url=backend_base_url,
        env_path=env_path
    )


# Naver Token Functions
def validate_naver_token(
    backend_base_url: str,
    access_token: str,
    endpoint: str = "/api/auth/naver"
) -> Tuple[bool, Optional[Dict]]:
    """
    Naver AccessToken을 백엔드 API로 검증하여 JWT 토큰 발급

    Args:
        backend_base_url: 백엔드 기본 URL
        access_token: Naver AccessToken
        endpoint: 토큰 검증 엔드포인트 (기본값: "/api/auth/naver")

    Returns:
        tuple: (is_valid: bool, response_data: Optional[Dict])
        - is_valid: 토큰이 유효하면 True, 아니면 False
        - response_data: {"token": str, "user": dict} 형식의 응답 데이터, 실패 시 None
    """
    return validate_oauth_token(
        backend_base_url=backend_base_url,
        access_token=access_token,
        provider="naver",
        endpoint=endpoint
    )


def refresh_naver_token(
    backend_base_url: str,
    refresh_token: str,
    endpoint: str = "/api/auth/naver/refresh"
) -> Optional[Dict]:
    """
    Naver RefreshToken을 사용하여 새로운 AccessToken 발급

    Args:
        backend_base_url: 백엔드 기본 URL
        refresh_token: Naver RefreshToken
        endpoint: 토큰 갱신 엔드포인트 (기본값: "/api/auth/naver/refresh")

    Returns:
        dict: {"token": str, "refreshToken": str, "user": dict} 형식의 응답 데이터, 실패 시 None
    """
    return refresh_oauth_token(
        backend_base_url=backend_base_url,
        refresh_token=refresh_token,
        provider="naver",
        endpoint=endpoint
    )


def update_naver_env_file(
    env_path: Path,
    refresh_token: Optional[str] = None
) -> None:
    """
    .env 파일의 Naver RefreshToken 업데이트
    (WEB_TEST_JWT_TOKEN은 API 엔드포인트로만 업데이트됨)

    Args:
        env_path: .env 파일 경로
        refresh_token: Naver RefreshToken (갱신된 경우)
    """
    update_oauth_env_file(
        env_path=env_path,
        refresh_token=refresh_token,
        provider="naver"
    )


def ensure_valid_naver_token(
    backend_base_url: Optional[str] = None,
    env_path: Optional[Path] = None
) -> Optional[str]:
    """
    Naver 토큰이 유효한지 확인하고, 유효하지 않으면 RefreshToken으로 갱신하여 JWT 토큰 발급

    Args:
        backend_base_url: 백엔드 기본 URL (None이면 .env에서 로드)
        env_path: .env 파일 경로 (None이면 프로젝트 루트의 .env 사용)

    Returns:
        str: 유효한 JWT 토큰, 실패 시 None
    """
    return ensure_valid_oauth_token(
        provider="naver",
        backend_base_url=backend_base_url,
        env_path=env_path
    )


# Main Script
if __name__ == "__main__":
    """스크립트로 직접 실행할 때 사용"""
    parser = argparse.ArgumentParser(description="토큰 유효성을 확인하고 필요시 갱신합니다.")
    parser.add_argument("--provider", type=str, choices=["jwt", "kakao", "naver"], default="jwt", help="토큰 제공자 (기본값: jwt)")
    parser.add_argument("--user-id", type=int, help="사용자 ID (JWT 모드에서 필수)")
    parser.add_argument("--email", type=str, help="이메일 (JWT 모드에서 선택)")
    parser.add_argument("--backend-base-url", type=str, help="백엔드 기본 URL (.env에서 로드하지 않을 경우)")
    parser.add_argument("--env-path", type=str, help=".env 파일 경로 (기본값: 프로젝트 루트의 .env)")
    
    args = parser.parse_args()
    
    env_path = Path(args.env_path) if args.env_path else None
    
    if args.provider == "jwt":
        if not args.user_id:
            parser.error("--user-id는 JWT 모드에서 필수입니다.")
        token = ensure_valid_jwt_token(
            user_id=args.user_id,
            email=args.email,
            backend_base_url=args.backend_base_url,
            env_path=env_path
        )
    elif args.provider == "kakao":
        token = ensure_valid_kakao_token(
            backend_base_url=args.backend_base_url,
            env_path=env_path
        )
    elif args.provider == "naver":
        token = ensure_valid_naver_token(
            backend_base_url=args.backend_base_url,
            env_path=env_path
        )
    else:
        parser.error(f"지원하지 않는 제공자: {args.provider}")
    
    if token:
        print(f"✅ 유효한 JWT 토큰: {token[:50]}...")
    else:
        print("❌ JWT 토큰 발급 실패")

