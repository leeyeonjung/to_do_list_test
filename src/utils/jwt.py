"""JWT 토큰 주입 및 네트워크 헤더 설정 헬퍼"""
import os
import logging

log = logging.getLogger(__name__)


def setup_page_with_token(context, page, jwt_token):
    """
    Playwright page에 JWT 토큰을 주입하고 모든 요청에 Authorization 헤더를 추가.
    """
    # localStorage에 JWT 토큰 주입
    context.add_init_script(
        f'window.localStorage.setItem("token", "{jwt_token}");'
    )
    log.info("JWT 토큰이 localStorage에 주입됨")

    # 모든 API 요청에 Authorization 헤더 추가
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

