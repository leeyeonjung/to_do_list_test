"""
JWT, Kakao, Naver 토큰 유효성 검증 및 갱신 유틸리티 (CI/CD 최적화 버전)
환경변수 > .env 파일 구조로 동작하도록 전체 리팩토링
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, Optional, Tuple

import requests
from src.utils.env_loader import get_env_path, upsert_env_value

log = logging.getLogger(__name__)


# ============================================================
# 1) JWT Functions
# ============================================================

def get_jwt_token(backend_base_url: str, user_id: int, email: Optional[str],
                  provider="test", endpoint="/api/auth/test-token") -> Dict:
    url = f"{backend_base_url.rstrip('/')}/{endpoint.lstrip('/')}"
    payload = {"id": user_id, "provider": provider}
    if email:
        payload["email"] = email

    headers = {"Content-Type": "application/json"}
    log.info(f"JWT 토큰 요청: {url}")
    resp = requests.post(url, json=payload, headers=headers)

    if resp.status_code != 200:
        log.error(f"JWT 토큰 요청 실패 {resp.status_code}: {resp.text}")
        return {}

    return resp.json() or {}


def update_jwt_env_file(env_path: Path, token: str, user_payload: Dict):
    """JWT 토큰과 사용자 정보를 환경 변수 파일에 업데이트"""
    upsert_env_value(env_path, "JWT_TOKEN", token)
    upsert_env_value(env_path, "JWT_USER", json.dumps(user_payload, ensure_ascii=False))
    log.info(f".env JWT 값 업데이트 완료: {env_path}")


def validate_jwt_token(backend_base_url: str, token: str,
                       endpoint="/api/auth/me") -> Tuple[bool, Optional[Dict]]:
    url = f"{backend_base_url.rstrip('/')}/{endpoint.lstrip('/')}"
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(url, headers=headers)

    if resp.status_code == 200:
        return True, resp.json()
    else:
        return False, None


def refresh_jwt_token(backend_base_url: str, refresh_token: str, access_token: Optional[str],
                      endpoint="/api/auth/refresh") -> Optional[Dict]:
    url = f"{backend_base_url.rstrip('/')}/{endpoint.lstrip('/')}"
    payload = {"refreshToken": refresh_token}
    if access_token:
        payload["token"] = access_token

    resp = requests.post(url, json=payload)

    if resp.status_code == 200:
        return resp.json()
    return None


def ensure_valid_jwt_token(user_id: int, email: Optional[str] = None, provider="test",
                           backend_base_url=None, token_endpoint="/api/auth/test-token",
                           validate_endpoint="/api/auth/me", env_path=None) -> str:

    if env_path is None:
        env_path = get_env_path()

    existing_token = os.getenv("JWT_TOKEN")

    if backend_base_url is None:
        backend_base_url = os.getenv("BACKEND_BASE_URL")

    if existing_token:
        is_valid, _ = validate_jwt_token(backend_base_url, existing_token, validate_endpoint)
        if is_valid:
            return existing_token

    resp = get_jwt_token(backend_base_url, user_id, email, provider, token_endpoint)
    token = resp.get("token")

    if token:
        update_jwt_env_file(env_path, token, resp.get("payload", {}))
        return token

    return ""


# ============================================================
# 2) OAuth Functions (Kakao / Naver 공통)
# ============================================================

def validate_oauth_token(backend_base_url, access_token, endpoint):
    url = f"{backend_base_url.rstrip('/')}/{endpoint.lstrip('/')}"
    payload = {"accessToken": access_token}
    resp = requests.post(url, json=payload)

    if resp.status_code == 200:
        return True, resp.json()
    else:
        return False, None


def refresh_oauth_token(backend_base_url, refresh_token, endpoint):
    url = f"{backend_base_url.rstrip('/')}/{endpoint.lstrip('/')}"
    payload = {"refreshToken": refresh_token}
    resp = requests.post(url, json=payload)

    return resp.json() if resp.status_code == 200 else None


def update_oauth_env_file(env_path: Path, refresh_token: str, provider: str):
    key = f"{provider.upper()}_REFRESH_TOKEN"
    upsert_env_value(env_path, key, refresh_token)


def ensure_valid_oauth_token(provider: str, backend_base_url=None, env_path=None,
                             validate_endpoint=None, refresh_endpoint=None):
    provider_upper = provider.upper()

    if env_path is None:
        env_path = get_env_path()

    access_token = os.getenv(f"{provider_upper}_ACCESS_TOKEN")
    refresh_token = os.getenv(f"{provider_upper}_REFRESH_TOKEN")

    if backend_base_url is None:
        backend_base_url = os.getenv("BACKEND_BASE_URL")

    if validate_endpoint is None:
        validate_endpoint = f"/api/auth/{provider}"
    if refresh_endpoint is None:
        refresh_endpoint = f"/api/auth/{provider}/refresh"

    # 기존 access 검증
    is_valid, resp_data = validate_oauth_token(
        backend_base_url, access_token, validate_endpoint
    )

    if is_valid and resp_data and resp_data.get("token"):
        return resp_data["token"]

    # refresh
    refresh_resp = refresh_oauth_token(
        backend_base_url, refresh_token, refresh_endpoint
    )

    new_token = refresh_resp.get("token") if refresh_resp else None
    new_refresh_token = refresh_resp.get("refreshToken") if refresh_resp else None

    if new_refresh_token:
        update_oauth_env_file(env_path, new_refresh_token, provider)

    if new_token:
        upsert_env_value(env_path, f"{provider_upper}_ACCESS_TOKEN", new_token)

    return new_token