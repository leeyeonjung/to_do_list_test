"""
JWT, Kakao, Naver 토큰 유효성 검증 및 갱신 유틸리티 (CI/CD 최적화 버전)
환경변수 > .env 파일 구조로 동작하도록 전체 리팩토링
"""

import argparse
import json
import logging
import os
import re
from pathlib import Path
from typing import Dict, Optional, Tuple

import requests
from dotenv import load_dotenv
from src.utils.env_loader import get_env_path

log = logging.getLogger(__name__)


# ============================================================
# 1) 공용 ENV LOAD 함수
# ============================================================

def load_env_safe(env_path: Optional[Path]):
    """
    .env 파일을 로드하되 override=False로 하여 Jenkins 환경변수를 덮지 않도록 한다.
    """
    if env_path and env_path.exists():
        load_dotenv(env_path, override=False)


def get_env_value(env_path: Path, key: str) -> Optional[str]:
    """환경변수 → 파일(.env) 순으로 안전하게 읽는다."""
    # 1) 환경변수 우선
    if key in os.environ:
        return os.environ.get(key)

    # 2) fallback: 파일에서 직접 읽기
    if not env_path or not env_path.exists():
        return None

    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            if "=" in line:
                k, v = line.split("=", 1)
                if k.strip() == key:
                    v = v.strip().strip('"').strip("'")
                    return v
    return None


# ============================================================
# 2) ".env 파일 수정" 유틸
# ============================================================

def _upsert_env_value(env_path: Path, key: str, value: str) -> None:
    """env 파일에 key=value를 업데이트하거나 추가"""
    if not env_path.exists():
        log.error(f".env 파일 없음: {env_path}")
        return

    with open(env_path, "r", encoding="utf-8") as f:
        content = f.read()

    pattern = rf"^{re.escape(key)}=.*$"
    replacement = f"{key}={value}"

    if re.search(pattern, content, flags=re.MULTILINE):
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
    else:
        content += f"\n{replacement}\n"

    with open(env_path, "w", encoding="utf-8") as f:
        f.write(content)


# ============================================================
# 3) JWT Functions
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
    if not env_path.exists():
        log.error(f".env 파일 없음: {env_path}")
        return

    with open(env_path, "r", encoding="utf-8") as f:
        content = f.read()

    token_pattern = r"^JWT_TOKEN=.*$"
    user_pattern = r"^JWT_USER=.*$"

    token_line = f"JWT_TOKEN={token}"
    user_line = f"JWT_USER={json.dumps(user_payload, ensure_ascii=False)}"

    content = re.sub(token_pattern, token_line, content, flags=re.MULTILINE) \
        if re.search(token_pattern, content, flags=re.MULTILINE) else content + f"\n{token_line}\n"

    content = re.sub(user_pattern, user_line, content, flags=re.MULTILINE) \
        if re.search(user_pattern, content, flags=re.MULTILINE) else content + f"\n{user_line}\n"

    with open(env_path, "w", encoding="utf-8") as f:
        f.write(content)

    log.info(f".env JWT 값 업데이트 완료: {env_path}")


def validate_jwt_token(backend_base_url: str, token: str,
                       endpoint="/api/auth/me") -> Tuple[bool, Optional[Dict]]:
    url = f"{backend_base_url.rstrip('/')}/{endpoint.lstrip('/')}"
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(url, headers=headers)

    if resp.status_code == 200:
        return True, resp.json()
    elif resp.status_code == 401:
        return False, None
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
    load_env_safe(env_path)

    existing_token = get_env_value(env_path, "JWT_TOKEN")

    if backend_base_url is None:
        backend_base_url = get_env_value(env_path, "BACKEND_BASE_URL")

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
# 4) OAuth Functions (Kakao / Naver 공통)
# ============================================================

def validate_oauth_token(backend_base_url, access_token, provider, endpoint):
    url = f"{backend_base_url.rstrip('/')}/{endpoint.lstrip('/')}"
    payload = {"accessToken": access_token}
    resp = requests.post(url, json=payload)

    if resp.status_code == 200:
        return True, resp.json()
    else:
        return False, None


def refresh_oauth_token(backend_base_url, refresh_token, provider, endpoint):
    url = f"{backend_base_url.rstrip('/')}/{endpoint.lstrip('/')}"
    payload = {"refreshToken": refresh_token}
    resp = requests.post(url, json=payload)

    return resp.json() if resp.status_code == 200 else None


def update_oauth_env_file(env_path: Path, refresh_token: str, provider: str):
    key = f"{provider.upper()}_REFRESH_TOKEN"
    _upsert_env_value(env_path, key, refresh_token)


def ensure_valid_oauth_token(provider: str, backend_base_url=None, env_path=None,
                             validate_endpoint=None, refresh_endpoint=None):
    provider_upper = provider.upper()

    if env_path is None:
        env_path = get_env_path()
    load_env_safe(env_path)

    access_token = get_env_value(env_path, f"{provider_upper}_ACCESS_TOKEN")
    refresh_token = get_env_value(env_path, f"{provider_upper}_REFRESH_TOKEN")

    if backend_base_url is None:
        backend_base_url = get_env_value(env_path, "BACKEND_BASE_URL")

    if validate_endpoint is None:
        validate_endpoint = f"/api/auth/{provider}"
    if refresh_endpoint is None:
        refresh_endpoint = f"/api/auth/{provider}/refresh"

    # 기존 access 검증
    is_valid, resp_data = validate_oauth_token(
        backend_base_url, access_token, provider, validate_endpoint
    )

    if is_valid and resp_data and resp_data.get("token"):
        return resp_data["token"]

    # refresh
    refresh_resp = refresh_oauth_token(
        backend_base_url, refresh_token, provider, refresh_endpoint
    )

    if not refresh_resp:
        return None

    new_token = refresh_resp.get("token")
    new_refresh_token = refresh_resp.get("refreshToken")

    if new_refresh_token:
        update_oauth_env_file(env_path, new_refresh_token, provider)

    if new_token:
        _upsert_env_value(env_path, f"{provider_upper}_ACCESS_TOKEN", new_token)

    return new_token


# ============================================================
# CLI 실행 (테스트 용)
# ============================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", choices=["jwt", "kakao", "naver"], default="jwt")

    parser.add_argument("--user-id", type=int)
    parser.add_argument("--email", type=str)
    parser.add_argument("--backend-base-url", type=str)
    parser.add_argument("--env-path", type=str)

    args = parser.parse_args()

    env_path = Path(args.env_path) if args.env_path else get_env_path()
    load_env_safe(env_path)

    if args.provider == "jwt":
        token = ensure_valid_jwt_token(
            user_id=args.user_id,
            email=args.email,
            backend_base_url=args.backend_base_url,
            env_path=env_path
        )

    elif args.provider == "kakao":
        token = ensure_valid_oauth_token(
            provider="kakao",
            backend_base_url=args.backend_base_url,
            env_path=env_path
        )

    elif args.provider == "naver":
        token = ensure_valid_oauth_token(
            provider="naver",
            backend_base_url=args.backend_base_url,
            env_path=env_path
        )