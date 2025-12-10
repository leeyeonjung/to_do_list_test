"""웹 테스트용 인증 액션"""
from src.locators.web import auth_locators
from src.actions.web.base_page import BasePage
import logging
import os

log = logging.getLogger(__name__)


class AuthActions:
    """인증/로그인 페이지 액션"""

    def __init__(self, page):
        """
        AuthActions 초기화

        Args:
            page: Playwright Page 인스턴스
        """
        self.base_page = BasePage(page)
        self.locators = auth_locators
        self.page = page


    def verify_logged_in(self):
        """
        로그인 상태 확인

        Returns:
            bool: 로그인 상태 여부
        """
        # 메인 컨테이너나 유저 프로필 섹션이 보이면 로그인 상태
        is_logged_in = (self.base_page.is_visible(self.locators.MAIN_CONTAINER)
                        or self.base_page.is_visible(self.locators.USER_PROFILE_SECTION))
        if is_logged_in:
            log.info("User is logged in")
        else:
            log.warning("User is not logged in")
        return is_logged_in

    def logout(self):
        """
        로그아웃 수행
        """
        # 사용자 메뉴 클릭 (필요한 경우)
        if self.base_page.is_visible(self.locators.USER_MENU):
            self.base_page.click(self.locators.USER_MENU)

        # 로그아웃 버튼 클릭
        self.base_page.click(self.locators.LOGOUT_BUTTON)
        log.info("Logout successful")

    def setup_jwt_login(self):
        """
        JWT 토큰을 사용한 로그인 설정
        
        conftest.py의 web_page fixture에서 Authorization 헤더가 자동 추가되므로
        프론트엔드가 /auth/me를 호출하여 인증 확인 후 메인 페이지로 전환될 때까지 대기
        """
        log.info("JWT 토큰을 사용하여 로그인 설정 중...")
        base_url = os.getenv("WEB_BASE_URL", "")
        
        self.base_page.navigate(base_url)
        self.base_page.wait_for_load_state("networkidle")
        
        log.info("프론트엔드 인증 확인 대기 중...")
        
        for _ in range(50):
            main_count = self.page.locator(self.locators.PAGE_MAIN).count()
            login_count = self.page.locator(self.locators.PAGE_LOGIN).count()

            if main_count > 0 and login_count == 0:
                log.info("메인 페이지 표시 확인. 로그인 성공")
                return

            self.page.wait_for_timeout(200)
        
        self.base_page.is_visible(self.locators.PAGE_MAIN)
        log.info("메인 페이지 표시 확인. 로그인 성공")
