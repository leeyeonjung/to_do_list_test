import os
import json
import requests
import logging
from pathlib import Path
from typing import Optional, Tuple

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


# -------------------------------------------------------------
# 0. Jenkins Credential Update Helper
# -------------------------------------------------------------

def update_jenkins_credential(credential_id: str, new_value: str):
    jenkins_url = os.getenv("JENKINS_URL")
    user = os.getenv("JENKINS_USER")
    password = os.getenv("JENKINS_PASS")

    if not all([jenkins_url, user, password]):
        log.error("❌ Jenkins Credential 업데이트 실패: 인증 정보 부족")
        return False

    # -----------------------------
    # 1) Crumb Token 가져오기
    # -----------------------------
    crumb_url = f"{jenkins_url}/crumbIssuer/api/json"
    crumb_resp = requests.get(crumb_url, auth=(user, password))

    if crumb_resp.status_code != 200:
        log.error(f"❌ Crumb Token 요청 실패: {crumb_resp.status_code}")
        log.error(crumb_resp.text)
        return False

    crumb_data = crumb_resp.json()
    crumb_field = crumb_data["crumbRequestField"]
    crumb_value = crumb_data["crumb"]

    # -----------------------------
    # 2) Credential XML 생성
    # -----------------------------
    api_url = f"{jenkins_url}/credentials/store/system/domain/todolist_dev/credential/{credential_id}/config.xml"

    xml_data = f"""
<com.cloudbees.plugins.credentials.impl.StringCredentialsImpl>
  <scope>GLOBAL</scope>
  <id>{credential_id}</id>
  <description>Updated by CI</description>
  <secret>{new_value}</secret>
</com.cloudbees.plugins.credentials.impl.StringCredentialsImpl>
"""

    headers = {
        "Content-Type": "application/xml",
        crumb_field: crumb_value
    }

    # -----------------------------
    # 3) Credential 업데이트 요청
    # -----------------------------
    resp = requests.post(
        api_url,
        auth=(user, password),
        headers=headers,
        data=xml_data.encode("utf-8")
    )

    if resp.status_code in [200, 201, 204]:
        log.info(f"✅ Jenkins Credential 업데이트 성공: {credential_id}")
        return True
    else:
        log.error(f"❌ Credential 업데이트 실패 {resp.status_code}: {resp.text[:200]}")
        return False

# -------------------------------------------------------------
# 1. Helper Functions (Validation + Refresh)
# -------------------------------------------------------------

def validate_access_token(backend_base_url: str, provider: str, access_token: str) -> Tuple[bool, Optional[dict]]:
    """
    AccessToken 유효성 검사 (Kakao / Naver 공통)
    """
    endpoint = f"/api/auth/{provider}"
    url = f"{backend_base_url.rstrip('/')}/{endpoint.lstrip('/')}"
    payload = {"accessToken": access_token}

    resp = requests.post(url, json=payload)
    return (resp.status_code == 200, resp.json() if resp.status_code == 200 else None)


def refresh_provider_token(backend_base_url: str, provider: str, refresh_token: str) -> Optional[dict]:
    """
    RefreshToken으로 AccessToken 재발급
    """
    endpoint = f"/api/auth/{provider}/refresh"
    url = f"{backend_base_url.rstrip('/')}/{endpoint.lstrip('/')}"
    payload = {"refreshToken": refresh_token}

    resp = requests.post(url, json=payload)
    return resp.json() if resp.status_code == 200 else None


def validate_jwt(backend_base_url: str, access_token: str) -> bool:
    url = f"{backend_base_url}/api/auth/me"
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = requests.get(url, headers=headers)
    return resp.status_code == 200


def refresh_jwt(backend_base_url: str, refresh_token: str) -> Optional[dict]:
    url = f"{backend_base_url}/api/auth/refresh"
    payload = {"refreshToken": refresh_token}
    resp = requests.post(url, json=payload)
    return resp.json() if resp.status_code == 200 else None


# -------------------------------------------------------------
# 2. CI MAIN LOGIC
# -------------------------------------------------------------

def process_provider(provider: str, backend_base_url: str):
    upper = provider.upper()

    access = os.getenv(f"{upper}_ACCESS_TOKEN")
    refresh = os.getenv(f"{upper}_REFRESH_TOKEN")

    if not access or not refresh:
        log.error(f"❌ ENV에 {provider} 토큰 정보 없음")
        return

    log.info(f"🔍 {provider} AccessToken 유효 검증 중...")

    valid, resp = validate_access_token(backend_base_url, provider, access)

    if valid:
        log.info(f"✅ {provider} AccessToken 유효함")
        return

    log.warning(f"⚠️ {provider} AccessToken INVALID → Refresh 시도...")

    refreshed = refresh_provider_token(backend_base_url, provider, refresh)
    if not refreshed:
        log.error(f"❌ {provider} Refresh 실패")
        return

    new_access = refreshed.get("token")
    new_refresh = refreshed.get("refreshToken")

    if new_access:
        update_jenkins_credential(f"{upper}_ACCESS_TOKEN", new_access)

    if new_refresh:
        update_jenkins_credential(f"{upper}_REFRESH_TOKEN", new_refresh)


def process_jwt(backend_base_url: str):
    access = os.getenv("JWT_TOKEN")
    refresh = os.getenv("JWT_REFRESH_TOKEN")

    if not access or not refresh:
        log.error("❌ JWT 토큰 정보가 ENV에 없음")
        return

    log.info("🔍 JWT AccessToken 유효 검증 중...")

    if validate_jwt(backend_base_url, access):
        log.info("✅ JWT AccessToken 유효함")
        return

    log.warning("⚠️ JWT INVALID → Refresh 시도...")

    refreshed = refresh_jwt(backend_base_url, refresh)
    if not refreshed:
        log.error("❌ JWT refresh 실패")
        return

    new_access = refreshed.get("token")
    new_refresh = refreshed.get("refreshToken")

    if new_access:
        update_jenkins_credential("JWT_TOKEN", new_access)

    if new_refresh:
        update_jenkins_credential("JWT_REFRESH_TOKEN", new_refresh)


# -------------------------------------------------------------
# 3. ENTRY POINT
# -------------------------------------------------------------

def main():
    backend = os.getenv("BACKEND_BASE_URL")
    if not backend:
        raise Exception("❌ BACKEND_BASE_URL 환경변수 없음")

    log.info(f"🚀 CI Token Manager 시작 (backend={backend})")

    process_jwt(backend)
    process_provider("kakao", backend)
    process_provider("naver", backend)

    log.info("🎉 Token Validation + Refresh + Credential Update 완료!")


if __name__ == "__main__":
    main()
