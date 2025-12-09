"""pytest 설정 및 fixture 정의"""
import os
import logging
from datetime import datetime
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

from src.utils.env_loader import load_env_files
from src.utils.jwt import setup_page_with_token
from src.utils.health_check import check_health

log = logging.getLogger(__name__)

# .env 파일 로드 (공통 모듈 사용)
load_env_files()

def pytest_sessionstart():
    """
    pytest 세션 시작 시 가장 먼저 호출되어
    백엔드/프론트엔드 헬스 체크를 수행
    """
    log.info("[HEALTH] 테스트 실행 전 서버 상태 점검 시작")

    backend_ok = check_health(os.getenv("BACKEND_BASE_URL"), expect_json=True)
    frontend_ok = check_health(os.getenv("WEB_BASE_URL"), expect_json=False)

    if not (backend_ok and frontend_ok):
        msg = "[HEALTH] 서버 헬스 체크 실패로 테스트를 중단합니다."
        log.error(msg)
        pytest.exit(msg, returncode=1)

    log.info("[HEALTH] 서버 헬스 체크 통과.")
    
    log.info("[HEALTH] 테스트를 계속 진행합니다.")


@pytest.fixture(scope="function")
def web_page():
    """
    Playwright 페이지 fixture

    브라우저 컨텍스트를 생성하고 JWT 토큰을 localStorage에 주입
    각 테스트 함수마다 새로운 페이지 인스턴스를 생성

    Args:
        jwt_token: JWT 토큰 fixture

    Yields:
        Page: Playwright Page 인스턴스

    Note:
        - add_init_script로 localStorage에 토큰 주입
        - page.route()로 네트워크 요청에 Authorization 헤더 추가
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=os.getenv("HEADLESS", "true").lower() == "true")
        context = browser.new_context()

        # 기본 모드: JWT를 localStorage/Authorization 헤더에 주입
        jwt_token = os.getenv("JWT_TOKEN")
        page = context.new_page()
        setup_page_with_token(context, page, jwt_token)

        yield page
        context.close()
        browser.close()


# Pytest Configuration Hooks
def pytest_configure(config):
    """
    pytest 실행 시 HTML 리포트 자동 생성

    --html 옵션이 지정되지 않은 경우 자동으로 리포트를 생성
    리포트는 Result/{timestamp}/report_{timestamp}.html 경로에 저장됨

    Args:
        config: pytest 설정 객체
    """
    if not getattr(config.option, "htmlpath", None):
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        result_base_dir = Path(__file__).resolve().parents[0] / "Result" / timestamp
        result_base_dir.mkdir(parents=True, exist_ok=True)
        report_path = result_base_dir / f"report_{timestamp}.html"

        config.option.htmlpath = str(report_path)
        config.option.self_contained_html = True
