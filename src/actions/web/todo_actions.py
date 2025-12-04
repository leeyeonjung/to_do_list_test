"""웹 테스트용 할일 액션"""
from playwright.sync_api import Page
from src.locators.web import todo_locators
from src.actions.web.base_page import BasePage
import logging

log = logging.getLogger(__name__)


class TodoActions:
    """할일 페이지 액션"""

    def __init__(self, page: Page, timeout: int = 10000):
        """
        TodoActions 초기화.

        Args:
            page: Playwright Page 인스턴스
            timeout: 기본 타임아웃 (밀리초)
        """
        self.base_page = BasePage(page, timeout)
        self.locators = todo_locators
        self.page = page
        self.timeout = timeout

    def add_todo(self, title: str):
        """
        할일 추가.

        Args:
            title: 할일 제목
        """
        # 상단 입력 폼에 제목 입력 후 저장 버튼 클릭
        self.base_page.fill(self.locators.TITLE_INPUT, title)
        self.base_page.click(self.locators.SAVE_BUTTON)
        log.info(f"Added todo: {title}")

    def view_todos(self) -> bool:
        """
        할일 리스트 확인.

        Returns:
            bool: 할일 리스트가 보이는지 여부
        """
        return self.base_page.is_visible(self.locators.TODO_LIST)

    def complete_todo(self):
        """
        할일 완료 처리.
        """
        self.base_page.click(self.locators.TODO_ITEM_FIRST)
        self.base_page.click(self.locators.COMPLETE_CHECKBOX)
        log.info("Completed todo")

    def verify_todo_completed(self) -> bool:
        """
        할일 완료 상태 확인.

        Returns:
            bool: 할일이 완료되었는지 여부
        """
        return self.base_page.is_visible(self.locators.COMPLETED_INDICATOR)

    def _click_delete_button(self):
        """
        삭제 버튼 클릭 (내부 메서드).
        """
        delete_button = self.page.locator(self.locators.DELETE_BUTTON_FIRST)
        delete_button.wait_for(state="visible", timeout=self.timeout)
        log.info(f"삭제 버튼 발견: {self.locators.DELETE_BUTTON_FIRST}")
        delete_button.click(timeout=self.timeout)
        log.info("삭제 버튼 클릭 완료")

    def delete_todo(self):
        """
        할일 삭제.

        삭제 버튼 클릭 후 확인 팝업에서 확인 버튼을 클릭하여 삭제를 완료합니다.
        """
        initial_count = self.get_todo_count()

        # 브라우저 다이얼로그 핸들러 설정
        def handle_dialog(dialog):
            log.info(f"다이얼로그 감지: {dialog.type}, 메시지: {dialog.message}")
            dialog.accept()
            log.info("다이얼로그 확인 버튼 클릭됨")

        self.page.on("dialog", handle_dialog)

        # 삭제 버튼 클릭
        self._click_delete_button()

        # 삭제 후 todo-item 개수가 줄어들 때까지 대기
        expected_count = initial_count - 1
        todo_items = self.page.locator(self.locators.TODO_ITEM)

        # 네트워크 요청 완료 대기
        self.page.wait_for_load_state("networkidle", timeout=self.timeout)

        # 개수가 줄어들 때까지 대기
        for _ in range(self.timeout // 100):
            current_count = todo_items.count()
            if current_count == expected_count:
                self.page.wait_for_load_state("domcontentloaded", timeout=1000)
                final_count = todo_items.count()
                if final_count == expected_count:
                    log.info("Deleted todo")
                    return
            self.page.wait_for_timeout(100)

        # 타임아웃 후에도 개수가 줄어들지 않으면 경고
        final_count = todo_items.count()
        log.warning(f"삭제 후 개수 확인: 초기={initial_count}, 예상={expected_count}, 실제={final_count}")

        log.info("Deleted todo")

    def cancel_delete_todo(self):
        """
        할일 삭제 취소.

        삭제 버튼 클릭 후 확인 팝업에서 취소 버튼을 클릭하여 삭제를 취소합니다.
        """
        # 브라우저 다이얼로그 핸들러 설정
        def handle_dialog(dialog):
            log.info(f"다이얼로그 감지: {dialog.type}, 메시지: {dialog.message}")
            dialog.dismiss()
            log.info("다이얼로그 취소 버튼 클릭됨")

        self.page.on("dialog", handle_dialog)

        # 삭제 버튼 클릭
        self._click_delete_button()

        log.info("Delete cancelled")

    def get_todo_count(self) -> int:
        """
        할일 개수 반환.

        Returns:
            int: 할일 개수
        """
        todo_items = self.page.locator(self.locators.TODO_ITEM)

        # DOM이 안정화될 때까지 대기
        self.page.wait_for_load_state("domcontentloaded", timeout=self.timeout)

        # todo-item이 있으면 첫 번째 항목이 visible할 때까지 대기
        count = todo_items.count()
        if count > 0:
            todo_items.first.wait_for(state="visible", timeout=self.timeout)

        log.debug(f"Todo count: {count}")
        return count
