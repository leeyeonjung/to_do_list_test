"""JWT 토큰 주입 및 네트워크 헤더 설정 헬퍼"""
import logging
import os

log = logging.getLogger(__name__)


def setup_page_with_token(context, page, jwt_token):
    """
    Playwright page에 JWT 토큰 주입 및 Authorization 헤더 설정
    
    Args:
        context: Playwright BrowserContext 인스턴스
        page: Playwright Page 인스턴스
        jwt_token: JWT 토큰
    """
    context.add_init_script(f'window.localStorage.setItem("token", "{jwt_token}");')
    log.info("JWT 토큰이 localStorage에 주입됨")

    def handle_route(route):
        headers = route.request.headers.copy()
        headers["Authorization"] = f"Bearer {jwt_token}"
        route.continue_(headers=headers)

    web_base_url = os.getenv("WEB_BASE_URL", "")
    page.route("**/api/**", handle_route)
    page.route("**/auth/**", handle_route)
    if web_base_url:
        page.route(f"{web_base_url}/**", handle_route)
    log.info("JWT 토큰이 네트워크 요청에 자동 추가됨")