"""pytest 설정 및 fixture 정의"""
import os
import logging
from datetime import datetime
from pathlib import Path

import pytest
import requests
from playwright.sync_api import sync_playwright

from src.actions.api.base_api import BaseAPI
from src.actions.web.auth_actions import AuthActions
from src.actions.web.todo_actions import TodoActions
from src.utils.env_loader import load_env_files
from src.utils.token_validator import (
    ensure_valid_jwt_token,
    ensure_valid_kakao_token,
    ensure_valid_naver_token,
    validate_jwt_token,
    validate_and_refresh_all_tokens,
)

log = logging.getLogger(__name__)

# .env 파일 로드 (공통 모듈 사용)
load_env_files()


# Utility Functions
def get_timestamp():
    """
    현재 시간을 타임스탬프 형식으로 반환

    Returns:
        str: YYYY-MM-DD_HH-MM-SS 형식의 타임스탬프 문자열
    """
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


def get_result_base_dir():
    """
    실행 시간 기준 Result 디렉토리 경로 반환

    실행 시간을 기준으로 Result/{timestamp} 디렉토리를 생성하고 반환
    리포트와 비디오 파일이 이 디렉토리 하위에 저장됨

    Returns:
        Path: Result/{timestamp} 디렉토리 경로
    """
    timestamp = get_timestamp()
    result_dir = Path(__file__).resolve().parents[0] / "Result" / timestamp
    result_dir.mkdir(parents=True, exist_ok=True)
    return result_dir


# Health Check (전체 테스트 시작 전 서버 상태 확인)
def _check_backend_health() -> bool:
    """
    백엔드 Health Check: GET {BACKEND_BASE_URL}/health
    기대 응답: 200, JSON { status: "ok", message: "Server is running" }
    """
    base_url = os.getenv("BACKEND_BASE_URL")
    if not base_url:
        log.error("[HEALTH] BACKEND_BASE_URL이 .env에 설정되어 있지 않습니다.")
        return False
    url = f"{base_url.rstrip('/')}/health"

    log.info(f"[HEALTH] 백엔드 헬스 체크 요청: {url}")
    resp = requests.get(url, timeout=3)

    if resp.status_code != 200:
        log.error(f"[HEALTH] 백엔드 상태 코드 비정상: {resp.status_code}")
        return False

    data = resp.json()

    status_ok = data.get("status") == "ok" and data.get("message") == "Server is running"
    if not status_ok:
        log.error(f"[HEALTH] 백엔드 응답 값 비정상: {data}")
        return False

    log.info("[HEALTH] 백엔드 서버 정상 동작 중")
    return True


def _check_frontend_health() -> bool:
    """
    프론트엔드 Health Check: GET {WEB_BASE_URL}/health
    기대 응답: 200, text/plain, body: "healthy"
    """
    base_url = os.getenv("WEB_BASE_URL")
    if not base_url:
        log.error("[HEALTH] WEB_BASE_URL이 .env에 설정되어 있지 않습니다.")
        return False
    url = f"{base_url.rstrip('/')}/health"

    log.info(f"[HEALTH] 프론트엔드 헬스 체크 요청: {url}")
    resp = requests.get(url, timeout=3)

    if resp.status_code != 200:
        log.error(f"[HEALTH] 프론트엔드 상태 코드 비정상: {resp.status_code}")
        return False

    body = resp.text.strip()
    if body != "healthy":
        log.error(f"[HEALTH] 프론트엔드 응답 바디 비정상: {body!r}")
        return False

    log.info("[HEALTH] 프론트엔드 서버 정상 동작 중")
    return True


def pytest_sessionstart(session: pytest.Session) -> None:  # type: ignore[override]
    """
    pytest 세션 시작 시 가장 먼저 호출되어
    1. 백엔드/프론트엔드 헬스 체크를 수행하고,
    2. 토큰 검증 및 갱신을 수행한다.
    둘 중 하나라도 실패하면 전체 테스트를 종료한다.
    """
    log.info("[HEALTH] 테스트 실행 전 서버 상태 점검 시작")

    backend_ok = _check_backend_health()
    frontend_ok = _check_frontend_health()

    if not (backend_ok and frontend_ok):
        msg = "[HEALTH] 서버 헬스 체크 실패로 테스트를 중단합니다."
        log.error(msg)
        pytest.exit(msg, returncode=1)

    log.info("[HEALTH] 서버 헬스 체크 통과.")
    
    log.info("[HEALTH] 테스트를 계속 진행합니다.")


# JWT Token Fixtures
@pytest.fixture(scope="session")
def jwt_token(api_base_url):
    """
    JWT 토큰 fixture

    기본값은 테스트용 /api/auth/test-token을 사용하여 JWT를 발급하고,
    .env에 JWT_TOKEN / JWT_USER를 갱신합니다.

    소셜 로그인(Kakao/Naver) 플로우를 테스트할 때는
    --login-mode=kakao|naver 옵션을 사용하고, 이 fixture를 쓰지 않는
    web_page 동작을 선택합니다.
    """
    # .env에서 사용자 정보 로드 (토큰 발급용)
    # 빈 문자열("")인 경우 기본값 "1"을 사용하도록 처리
    user_id = os.getenv("JWT_USER_ID") or "1"
    email = os.getenv("JWT_USER_EMAIL")
    provider = os.getenv("JWT_USER_PROVIDER", "test")

    log.info("JWT 발급 모드: test (테스트용 /api/auth/test-token 사용)")

    # 기존 토큰 확인
    existing_token = os.getenv("JWT_TOKEN")

    # 기존 토큰이 있으면 유효성 검증
    if existing_token:
        is_valid, _ = validate_jwt_token(
            backend_base_url=api_base_url,
            token=existing_token,
        )

        if is_valid:
            log.info("기존 JWT 토큰이 유효합니다.")
            return existing_token

    # 토큰이 없거나 유효하지 않으면 새로 발급
    log.info("JWT 토큰이 없거나 유효하지 않습니다. 새로 발급받습니다.")
    token = ensure_valid_jwt_token(
        user_id=int(user_id),
        email=email if email else None,
        provider=provider,
        backend_base_url=api_base_url,
    )

    return token


# API Fixtures
@pytest.fixture(scope="session")
def api_base_url():
    """
    환경 변수에서 API 기본 URL을 가져옴

    Returns:
        str: API 기본 URL
    """
    return os.getenv("BACKEND_BASE_URL")


@pytest.fixture
def api_client(api_base_url):
    """
    API 클라이언트 fixture 생성

    BaseAPI 인스턴스를 생성하여 API 테스트에 사용

    Args:
        api_base_url: API 기본 URL fixture

    Returns:
        BaseAPI: API 클라이언트 인스턴스
    """
    return BaseAPI(base_url=api_base_url)


# Web Fixtures
@pytest.fixture(scope="session")
def web_base_url():
    """
    환경 변수에서 웹 기본 URL을 가져옴

    Returns:
        str: 웹 기본 URL
    """
    web_url = os.getenv("WEB_BASE_URL")
    if not web_url:
        log.error("WEB_BASE_URL이 .env에 설정되어 있지 않습니다.")
        return ""
    return web_url


@pytest.fixture
def login_mode(request):
    """
    로그인 모드 결정용 fixture

    - 기본값: "" (빈값) → JWT 모드
    - 테스트에서 @pytest.mark.parametrize("login_mode", ["kakao"], indirect=True)
      처럼 지정하면 해당 값이 들어옴.
    """
    return getattr(request, "param", "")


def _setup_page_with_token(context, page, jwt_token, login_mode_name=""):
    """
    페이지에 JWT 토큰을 설정하는 헬퍼 함수
    
    Args:
        context: Playwright 브라우저 컨텍스트
        page: Playwright 페이지 인스턴스
        jwt_token: JWT 토큰 문자열
        login_mode_name: 로그인 모드 이름 (로그용, 기본값: "")
    """
    # localStorage에 JWT 토큰 주입
    context.add_init_script(
        f'window.localStorage.setItem("token", "{jwt_token}");'
    )
    mode_text = f"{login_mode_name} " if login_mode_name else ""
    log.info(f"{mode_text}JWT 토큰이 localStorage에 주입됨")
    
    # 모든 API 요청에 Authorization 헤더 추가
    def handle_route(route):
        log.debug(f"Route intercepted: {route.request.url}")
        headers = route.request.headers.copy()
        headers["Authorization"] = f"Bearer {jwt_token}"
        route.continue_(headers=headers)
    
    web_base_url = os.getenv("WEB_BASE_URL", "")
    page.route("**/api/**", handle_route)
    page.route("**/auth/**", handle_route)
    if web_base_url:
        page.route(f"{web_base_url}/**", handle_route)
    log.info(f"{mode_text}JWT 토큰이 네트워크 요청에 자동 추가됨")


@pytest.fixture(scope="function")
def web_page(request, login_mode):
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

        # 소셜 로그인 모드(kakao/naver): .env의 AccessToken/RefreshToken을 사용하여 JWT 발급 후 주입
        if login_mode == "kakao":
            log.info("Kakao 로그인 모드: .env의 KAKAO_ACCESS_TOKEN/REFRESH_TOKEN을 사용하여 JWT 발급")
            jwt_token = ensure_valid_kakao_token(backend_base_url=request.getfixturevalue("api_base_url"))
            
            if not jwt_token:
                log.error("Kakao JWT 토큰 발급에 실패했습니다.")
                page = context.new_page()
                yield page
                context.close()
                browser.close()
                return
            
            page = context.new_page()
            _setup_page_with_token(context, page, jwt_token, "Kakao")
            yield page
            context.close()
            browser.close()
            return
        
        if login_mode == "naver":
            log.info("Naver 로그인 모드: .env의 NAVER_ACCESS_TOKEN/REFRESH_TOKEN을 사용하여 JWT 발급")
            jwt_token = ensure_valid_naver_token(backend_base_url=request.getfixturevalue("api_base_url"))
            
            if not jwt_token:
                log.error("Naver JWT 토큰 발급에 실패했습니다.")
                page = context.new_page()
                yield page
                context.close()
                browser.close()
                return
            
            page = context.new_page()
            _setup_page_with_token(context, page, jwt_token, "Naver")
            yield page
            context.close()
            browser.close()
            return

        # 기본 모드: JWT를 localStorage/Authorization 헤더에 주입
        jwt_token = request.getfixturevalue("jwt_token")
        page = context.new_page()
        _setup_page_with_token(context, page, jwt_token)

        yield page
        context.close()
        browser.close()


@pytest.fixture
def todo_page(web_page, web_base_url):
    """
    할일 페이지 액션 생성 (JWT로 이미 로그인된 상태를 전제)

    JWT 토큰을 사용하여 로그인 설정을 수행하고 TodoActions 인스턴스를 반환
    웹 테스트에서 할일 관련 기능을 테스트할 때 사용

    Args:
        web_page: Playwright 페이지 fixture
        web_base_url: 웹 기본 URL fixture

    Returns:
        TodoActions: 할일 페이지 액션 인스턴스
    """
    # JWT 토큰을 사용한 로그인 설정
    auth = AuthActions(web_page)
    auth.setup_jwt_login(web_base_url)

    return TodoActions(web_page)


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
        result_base_dir = get_result_base_dir()
        timestamp = get_timestamp()
        report_path = result_base_dir / f"report_{timestamp}.html"

        config.option.htmlpath = str(report_path)
        config.option.self_contained_html = True
