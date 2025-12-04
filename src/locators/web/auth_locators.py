"""웹 테스트용 인증/레이아웃 로케이터"""

# App.js - 메인 페이지(로그인 후)
PAGE_MAIN = "#page-main"
MAIN_CONTAINER = "#main-container"

# Login.js - 로그인 페이지
PAGE_LOGIN = "#page-login"

# UserProfile.js - 유저 프로필 섹션
USER_PROFILE_SECTION = "#section-user-profile"

# 로그인 후 확인용 요소 (인증 성공 시 노출되는 영역들)
USER_MENU = USER_PROFILE_SECTION  # 프로필 섹션이 곧 사용자 메뉴 역할
LOGOUT_BUTTON = "#btn-logout, .logout-button"
