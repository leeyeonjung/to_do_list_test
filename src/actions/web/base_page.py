"""Playwright를 사용한 웹 테스트용 기본 페이지 클래스"""
import logging

log = logging.getLogger(__name__)


class BasePage:
    """웹 페이지 객체의 기본 클래스"""

    def __init__(self, page):
        """
        BasePage 초기화.

        Args:
            page: Playwright Page 인스턴스
        """
        self.page = page

    def find_element(self, selector):
        """
        요소 찾기.

        Args:
            selector: CSS 선택자 또는 XPath

        Returns:
            Locator 객체
        """
        element = self.page.locator(selector).first
        element.wait_for(state="visible")
        log.debug(f"Element found: {selector}")
        return element

    def click(self, selector):
        """
        요소 클릭.

        Args:
            selector: CSS 선택자 또는 XPath
        """
        element = self.find_element(selector)
        element.click()
        log.info(f"Clicked on element: {selector}")

    def fill(self, selector, text):
        """
        입력 필드에 텍스트 입력.

        Args:
            selector: CSS 선택자 또는 XPath
            text: 입력할 텍스트
        """
        element = self.find_element(selector)
        element.fill(text)
        log.info(f"Filled element {selector} with text: {text}")

    def is_visible(self, selector, timeout=None):
        """
        요소가 보이는지 확인.

        Args:
            selector: CSS 선택자 또는 XPath

        Returns:
            요소가 보이면 True, 그렇지 않으면 False
        """
        element = self.page.locator(selector).first
        
        # 요소가 보이는지 확인
        if element.count() == 0:
            return False
        
        element.wait_for(state="visible")
        return True

    def navigate(self, url):
        """
        URL로 이동.

        Args:
            url: 이동할 URL
        """
        self.page.goto(url)
        log.info(f"Navigated to: {url}")

    def wait_for_load_state(self, state="load"):
        """
        페이지 로드 상태 대기.

        Args:
            state: 대기할 로드 상태 (load, domcontentloaded, networkidle)
        """
        self.page.wait_for_load_state(state)
        log.debug(f"Page load state: {state}")
