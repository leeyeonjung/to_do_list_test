"""Health check utilities"""
import logging
import requests

log = logging.getLogger(__name__)


def check_health(base_url, expect_json=False):
    """
    서버 헬스 체크
    
    Args:
        base_url: 서버 기본 URL
        expect_json: JSON 응답 기대 여부
        
    Returns:
        bool: 헬스 체크 성공 여부
    """
    if not base_url:
        log.error("[HEALTH] BASE_URL이 설정되지 않았습니다")
        return False

    url = f"{base_url.rstrip('/')}/health"
    log.info(f"[HEALTH] 헬스 체크 요청: {url}")
    resp = requests.get(url, timeout=3)

    if resp.status_code != 200:
        log.error(f"[HEALTH] 상태 코드 비정상: {resp.status_code}")
        return False

    if expect_json:
        data = resp.json()
        status_ok = data.get("status") == "ok" and data.get("message") == "Server is running"
        if not status_ok:
            log.error(f"[HEALTH] 응답 값 비정상: {data}")
            return False
    else:
        body = resp.text.strip()
        if body != "healthy":
            log.error(f"[HEALTH] 응답 바디 비정상: {body!r}")
            return False

    log.info("[HEALTH] 서버 정상 동작 중")
    return True