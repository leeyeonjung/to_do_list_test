"""requests를 사용한 API 테스트"""
import pytest_check as check


def test_get_todos(api_client):
    """모든 할일 조회 테스트"""
    response = api_client.get("/api/todos")
    status_ok = response.status_code == 200
    check.equal(response.status_code, 200)
    if not status_ok:
        return

    check.is_true(isinstance(response.json(), list))


def test_create_todo(api_client):
    """새 할일 생성 테스트"""
    todo_data = {
        "title": "Test Todo",
        "description": "This is a test todo",
        "completed": False
    }
    response = api_client.post("/api/todos", json=todo_data)
    status_ok = response.status_code in [200, 201]
    check.is_in(response.status_code, [200, 201])
    if not status_ok:
        return

    data = response.json()
    check.equal(data["title"], todo_data["title"])


def test_get_todo_by_id(api_client):
    """ID로 할일 조회 테스트"""
    # 할일 생성
    todo_data = {"title": "Test Todo", "completed": False}
    create_response = api_client.post("/api/todos", json=todo_data)
    create_ok = create_response.status_code in [200, 201]
    check.is_in(create_response.status_code, [200, 201])
    if not create_ok:
        return

    todo_id = create_response.json().get("id")

    # ID로 조회
    response = api_client.get(f"/api/todos/{todo_id}")
    status_ok = response.status_code == 200
    check.equal(response.status_code, 200)
    if not status_ok:
        return

    check.equal(response.json()["id"], todo_id)


def test_update_todo(api_client):
    """할일 수정 테스트"""
    # 할일 생성
    todo_data = {"title": "Original Todo", "completed": False}
    create_response = api_client.post("/api/todos", json=todo_data)
    create_ok = create_response.status_code in [200, 201]
    check.is_in(create_response.status_code, [200, 201])
    if not create_ok:
        return

    todo_id = create_response.json().get("id")

    # 할일 수정
    update_data = {"title": "Updated Todo", "completed": True}
    response = api_client.put(f"/api/todos/{todo_id}", json=update_data)
    status_ok = response.status_code == 200
    check.equal(response.status_code, 200)
    if not status_ok:
        return

    check.equal(response.json()["title"], update_data["title"])


def test_delete_todo(api_client):
    """할일 삭제 테스트"""
    # 할일 생성
    todo_data = {"title": "Todo to Delete", "completed": False}
    create_response = api_client.post("/api/todos", json=todo_data)
    create_ok = create_response.status_code in [200, 201]
    check.is_in(create_response.status_code, [200, 201])
    if not create_ok:
        return

    todo_id = create_response.json().get("id")

    # 할일 삭제
    response = api_client.delete(f"/api/todos/{todo_id}")
    delete_ok = response.status_code in [200, 204]
    check.is_in(response.status_code, [200, 204])
    if not delete_ok:
        return

    # 삭제 확인
    get_response = api_client.get(f"/api/todos/{todo_id}")
    check.equal(get_response.status_code, 404)
