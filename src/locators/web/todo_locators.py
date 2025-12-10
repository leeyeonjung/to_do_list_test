"""웹 테스트용 할일 페이지 로케이터"""

# 입력/폼 영역
TITLE_INPUT = "#section-todo-form .form-input"
SAVE_BUTTON = "#section-todo-form .form-submit"

# 리스트 및 아이템
TODO_LIST = "#section-todo-list .todo-list"
TODO_ITEM = ".todo-item"
TODO_ITEM_FIRST = ".todo-item:first-child"

# 완료/삭제 컨트롤
COMPLETE_CHECKBOX = ".todo-item-checkbox input.checkbox-input"
COMPLETED_INDICATOR = ".todo-item.completed"
DELETE_BUTTON_FIRST = ".todo-item:first-child .todo-btn.todo-btn-delete"