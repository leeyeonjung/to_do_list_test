"""Playwright를 사용한 웹 테스트"""
import pytest_check as check

from src.actions.web.auth_actions import AuthActions
from src.actions.web.todo_actions import TodoActions
from src.locators.web import auth_locators


def test_add_todo(web_page):
    """새 할일 추가 테스트"""
    auth = AuthActions(web_page)
    auth.setup_jwt_login()
    todo_page = TodoActions(web_page)
    todo_page.add_todo("Web Test Todo")
    check.is_true(todo_page.view_todos())


def test_view_todos(web_page):
    """할일 리스트 조회 테스트"""
    auth = AuthActions(web_page)
    auth.setup_jwt_login()
    todo_page = TodoActions(web_page)
    check.is_true(todo_page.view_todos())


def test_complete_todo(web_page):
    """할일 완료 처리 테스트"""
    auth = AuthActions(web_page)
    auth.setup_jwt_login()
    todo_page = TodoActions(web_page)
    todo_page.complete_todo()
    check.is_true(todo_page.verify_todo_completed())


def test_delete_todo(web_page):
    """할일 삭제 테스트"""
    auth = AuthActions(web_page)
    auth.setup_jwt_login()
    todo_page = TodoActions(web_page)
    initial_count = todo_page.get_todo_count()
    todo_page.delete_todo()
    final_count = todo_page.get_todo_count()
    check.equal(final_count, initial_count - 1)


def test_cancel_delete_todo(web_page):
    """할일 삭제 취소 테스트"""
    auth = AuthActions(web_page)
    auth.setup_jwt_login()
    todo_page = TodoActions(web_page)
    initial_count = todo_page.get_todo_count()
    todo_page.cancel_delete_todo()
    final_count = todo_page.get_todo_count()
    check.equal(final_count, initial_count)


def test_logout_redirects_to_login(web_page):
    """로그아웃 시 로그인 페이지로 리다이렉트 확인"""
    auth = AuthActions(web_page)
    auth.setup_jwt_login()
    check.is_true(auth.verify_logged_in())

    auth.logout()

    is_login_page = auth.base_page.is_visible(auth_locators.PAGE_LOGIN)
    check.is_true(is_login_page)