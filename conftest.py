"""pytest 설정 및 fixture 정의"""
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.env_loader import load_env_files
from src.utils.health_check import check_health
from src.utils.jwt import setup_page_with_token

log = logging.getLogger(__name__)

load_env_files()

def pytest_sessionstart():
    """pytest 세션 시작 시 서버 헬스 체크 수행"""
    skip_health_check = os.getenv("SKIP_HEALTH_CHECK", "false").lower() == "true"
    if skip_health_check:
        log.warning("[HEALTH] SKIP_HEALTH_CHECK=true 설정으로 헬스 체크를 건너뜁니다")
        return
    
    log.info("[HEALTH] 테스트 실행 전 서버 상태 점검 시작")
    backend_ok = check_health(os.getenv("BACKEND_BASE_URL"), expect_json=True)
    frontend_ok = check_health(os.getenv("WEB_BASE_URL"), expect_json=False)

    if not (backend_ok and frontend_ok):
        msg = "[HEALTH] 서버 헬스 체크 실패로 테스트를 중단합니다"
        log.error(msg)
        pytest.exit(msg, returncode=1)

    log.info("[HEALTH] 서버 헬스 체크 통과")


@pytest.fixture(scope="function")
def web_page():
    """
    Playwright 페이지 fixture
    
    JWT 토큰이 주입된 브라우저 페이지를 생성하여 각 테스트에 제공
    
    Yields:
        Page: JWT 토큰이 설정된 Playwright Page 인스턴스
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=os.getenv("HEADLESS", "true").lower() == "true")
        context = browser.new_context()
        jwt_token = os.getenv("JWT_TOKEN")
        page = context.new_page()
        setup_page_with_token(context, page, jwt_token)

        yield page
        context.close()
        browser.close()


def pytest_configure(config):
    """pytest HTML 리포트 자동 생성 설정"""
    if not getattr(config.option, "htmlpath", None):
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        result_base_dir = Path(__file__).resolve().parents[0] / "Result" / timestamp
        result_base_dir.mkdir(parents=True, exist_ok=True)
        report_path = result_base_dir / f"report_{timestamp}.html"

        config.option.htmlpath = str(report_path)
        config.option.self_contained_html = True