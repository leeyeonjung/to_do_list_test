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
    domain = os.getenv("CREDENTIAL_DOMAIN", "todolist_dev")

    # 1) Crumb
    crumb_resp = requests.get(f"{jenkins_url}/crumbIssuer/api/json", auth=(user, password))
    crumb = crumb_resp.json()
    headers = {
        crumb["crumbRequestField"]: crumb["crumb"],
        "Content-Type": "application/xml"
    }

    # 2) GET existing config.xml
    url = f"{jenkins_url}/credentials/store/system/domain/{domain}/credential/{credential_id}/config.xml"
    get_resp = requests.get(url, auth=(user, password))

    if get_resp.status_code != 200:
        print("❌ Cannot fetch existing credential XML:", get_resp.text)
        return False

    xml = get_resp.text

    # 3) replace <secret>...</secret> value
    import re
    new_xml = re.sub(
        r"<secret>.*?</secret>",
        f"<secret>{new_value}</secret>",
        xml,
        flags=re.DOTALL
    )

    # 4) PUT updated XML back to Jenkins
    put_resp = requests.put(url, auth=(user, password), data=new_xml.encode("utf-8"), headers=headers)

    if put_resp.status_code in (200, 204):
        print(f"✅ Credential {credential_id} updated successfully")
        return True
    else:
        print(f"❌ Update failed: {put_resp.status_code} → {put_resp.text}")
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
