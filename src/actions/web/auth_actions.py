"""웹 테스트용 인증 액션"""
from src.locators.web import auth_locators
from src.actions.web.base_page import BasePage
import logging
import os

log = logging.getLogger(__name__)


class AuthActions:
    """인증/로그인 페이지 액션"""

    def __init__(self, page, timeout=10000):
        """
        AuthActions 초기화.

        Args:
            page: Playwright Page 인스턴스
            timeout: 기본 타임아웃 (밀리초)
        """
        self.base_page = BasePage(page, timeout)
        self.locators = auth_locators
        self.page = page
        self.timeout = timeout


    def verify_logged_in(self):
        """
        로그인 상태 확인.

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
        로그아웃 수행.
        """
        # 사용자 메뉴 클릭 (필요한 경우)
        if self.base_page.is_visible(self.locators.USER_MENU, timeout=5000):
            self.base_page.click(self.locators.USER_MENU)

        # 로그아웃 버튼 클릭
        self.base_page.click(self.locators.LOGOUT_BUTTON)
        log.info("Logout successful")

    def setup_jwt_login(self):
        """
        JWT 토큰을 사용한 로그인 설정.

        네트워크 요청에 Authorization 헤더가 자동으로 추가되므로 별도 처리 불필요.
        프론트엔드가 /auth/me를 호출하여 인증을 확인하고 메인 페이지로 전환될 때까지 대기.

        Note:
            - conftest.py의 web_page fixture에서 이미 Authorization 헤더가 추가됨
        """
        log.info("JWT 토큰을 사용하여 로그인 설정 중...")
        base_url = os.getenv("WEB_BASE_URL", "")

        # 메인 페이지로 이동
        # 네트워크 요청에 Authorization 헤더는 conftest.py의 web_page fixture에서 자동 추가됨
        self.base_page.navigate(base_url)
        self.base_page.wait_for_load_state("networkidle")

        # 프론트엔드가 /auth/me를 호출할 때까지 대기
        # 네트워크 요청에 Authorization 헤더가 자동으로 추가되므로 성공 응답을 받을 것임
        log.info("프론트엔드가 /auth/me를 호출하여 인증 확인 대기 중...")

        # 프론트엔드가 API 호출을 완료하고 메인 페이지로 전환될 때까지 대기
        # 메인 페이지가 보일 때까지 대기 (최대 self.timeout 동안)
        for _ in range(self.timeout // 200):  # 200ms 간격으로 체크
            # 메인 페이지가 보이는지 확인
            main_count = self.page.locator(self.locators.PAGE_MAIN).count()
            login_count = self.page.locator(self.locators.PAGE_LOGIN).count()

            if main_count > 0 and login_count == 0:
                log.info("✅ 메인 페이지 표시 확인됨. 로그인 성공!")
                return

            self.page.wait_for_timeout(200)

        # 타임아웃 전에 메인 페이지가 나타나지 않으면 강제로 확인
        log.info("메인 페이지 표시 대기 중...")
        self.base_page.is_visible(self.locators.PAGE_MAIN, timeout=self.timeout)
        log.info("✅ 메인 페이지 표시 확인됨. 로그인 성공!")
