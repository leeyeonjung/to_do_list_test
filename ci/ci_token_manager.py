import os
import requests
import logging

log = logging.getLogger(__name__)
log=logging.getLogger()


# ============================================================
# 0. Jenkins Credential Update Helper (with Crumb + PUT)
# ============================================================

def update_jenkins_credential(credential_id: str, new_value: str):

    jenkins_url = os.getenv("JENKINS_URL")
    user = os.getenv("JENKINS_USER")
    password = os.getenv("JENKINS_PASS")

    # 너희 Jenkins Credential Domain
    domain = os.getenv("CREDENTIAL_DOMAIN", "dev")

    if not all([jenkins_url, user, password]):
        log.error("❌ Jenkins Credential 업데이트 실패: 인증 정보 부족")
        return False

    # --- 1) Crumb Token 요청 ---
    crumb_url = f"{jenkins_url}/crumbIssuer/api/json"
    crumb_resp = requests.get(crumb_url, auth=(user, password))

    if crumb_resp.status_code != 200:
        log.error(f"❌ Crumb Token 요청 실패 ({crumb_resp.status_code})")
        log.error(crumb_resp.text[:200])
        return False

    crumb_data = crumb_resp.json()
    crumb_field = crumb_data["crumbRequestField"]
    crumb_value = crumb_data["crumb"]

    # --- 2) Credential 업데이트 URL ---
    api_url = (
        f"{jenkins_url}/credentials/store/system/domain/"
        f"{domain}/credential/{credential_id}/config.xml"
    )

    # --- 3) Credential XML ---
    xml_data = f"""
<com.cloudbees.plugins.credentials.impl.StringCredentialsImpl>
  <scope>GLOBAL</scope>
  <id>{credential_id}</id>
  <description>Updated by CI</description>
  <secret>{new_value}</secret>
</com.cloudbees.plugins.credentials.impl.StringCredentialsImpl>
""".strip()

    headers = {
        "Content-Type": "application/xml",
        crumb_field: crumb_value
    }

    log.info(f"🔐 Updating Jenkins credential ({credential_id}) @ domain={domain}")

    # --- 4) PUT 요청 ---
    resp = requests.put(
        api_url,
        auth=(user, password),
        headers=headers,
        data=xml_data.encode("utf-8")
    )

    if resp.status_code in (200, 201, 204):
        log.info(f"✅ Credential 업데이트 성공: {credential_id}")
        return True

    log.error(
        f"❌ Credential 업데이트 실패 {resp.status_code} → "
        f"{resp.text[:300]}"
    )
    return False



# ============================================================
# 1. Token helpers
# ============================================================

def validate_access_token(backend: str, provider: str, access_token: str):
    url = f"{backend}/api/auth/{provider}"
    resp = requests.post(url, json={"accessToken": access_token})
    return resp.status_code == 200, (resp.json() if resp.status_code == 200 else None)


def refresh_provider_token(backend: str, provider: str, refresh_token: str):
    url = f"{backend}/api/auth/{provider}/refresh"
    resp = requests.post(url, json={"refreshToken": refresh_token})
    return resp.json() if resp.status_code == 200 else None


def validate_jwt(backend: str, token: str):
    url = f"{backend}/api/auth/me"
    resp = requests.get(url, headers={"Authorization": f"Bearer {token}"})
    return resp.status_code == 200


def refresh_jwt(backend: str, refresh_token: str):
    url = f"{backend}/api/auth/refresh"
    resp = requests.post(url, json={"refreshToken": refresh_token})
    return resp.json() if resp.status_code == 200 else None



# ============================================================
# 2. Provider processing
# ============================================================

def process_provider(provider: str, backend: str):
    upper = provider.upper()

    access = os.getenv(f"{upper}_ACCESS_TOKEN")
    refresh = os.getenv(f"{upper}_REFRESH_TOKEN")

    if not access or not refresh:
        log.error(f"❌ {provider} 토큰 없음")
        return

    log.info(f"🔍 {provider} AccessToken 검증 중...")

    valid, _ = validate_access_token(backend, provider, access)
    if valid:
        log.info(f"✅ {provider} AccessToken OK")
        return

    log.warning(f"⚠️ {provider} INVALID → Refresh 시도")

    refreshed = refresh_provider_token(backend, provider, refresh)
    if not refreshed:
        log.error(f"❌ {provider} refresh 실패")
        return

    new_access = refreshed.get("token")
    new_refresh = refreshed.get("refreshToken")

    if new_access:
        update_jenkins_credential(f"{upper}_ACCESS_TOKEN", new_access)

    if new_refresh:
        update_jenkins_credential(f"{upper}_REFRESH_TOKEN", new_refresh)



def process_jwt(backend: str):
    access = os.getenv("JWT_TOKEN")
    refresh = os.getenv("JWT_REFRESH_TOKEN")

    if not access or not refresh:
        log.error("❌ JWT 토큰 없음")
        return

    log.info("🔍 JWT AccessToken 검증 중...")

    if validate_jwt(backend, access):
        log.info("✅ JWT OK")
        return

    log.warning("⚠️ JWT INVALID → Refresh 시도")

    refreshed = refresh_jwt(backend, refresh)
    if not refreshed:
        log.error("❌ JWT refresh 실패")
        return

    new_access = refreshed.get("token")
    new_refresh = refreshed.get("refreshToken")

    if new_access:
        update_jenkins_credential("JWT_TOKEN", new_access)

    if new_refresh:
        update_jenkins_credential("JWT_REFRESH_TOKEN", new_refresh)



# ============================================================
# 3. Entry_point
# ============================================================

def main():
    backend = os.getenv("BACKEND_BASE_URL")
    if not backend:
        raise Exception("❌ BACKEND_BASE_URL 없음")

    log.info(f"🚀 CI Token Manager 시작 → backend={backend}")

    process_jwt(backend)
    process_provider("kakao", backend)
    process_provider("naver", backend)

    log.info("🎉 토큰 검증 + Refresh + Jenkins Credential 업데이트 완료")


if __name__ == "__main__":
    main()
