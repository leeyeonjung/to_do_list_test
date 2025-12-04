# Todo List Test Automation

POM(Page Object Model) 구조를 적용한 pytest 기반 테스트 자동화 프로젝트입니다.

## 프로젝트 구조

```
to_do_list_test/
├── .env                    # 환경 변수 설정 파일 (gitignore에 포함)
├── .env.example           # 환경 변수 예제 파일
├── .gitignore             # Git 무시 파일 목록
├── conftest.py            # pytest 설정 및 fixture
├── pytest.ini             # pytest 설정
├── requirements.txt       # Python 패키지 의존성
├── src/                   # 소스 코드
│   ├── actions/           # 액션 클래스 (POM 패턴)
│   │   ├── api/           # API 테스트용 클래스
│   │   │   └── base_api.py
│   │   └── web/           # Web 테스트용 클래스
│   │       ├── auth_actions.py
│   │       ├── base_page.py
│   │       └── todo_actions.py
│   ├── locators/          # 페이지 로케이터
│   │   └── web/
│   │       ├── auth_locators.py
│   │       └── todo_locators.py
│   └── utils/             # 유틸리티 함수
│       └── token_validator.py
├── tests/                 # 테스트 파일
│   ├── test_api.py        # API 테스트
│   ├── test_login.py      # 로그인 테스트
│   └── test_web.py        # Web 테스트
└── Result/                # 테스트 리포트 저장 디렉토리
```

## 설치 방법

1. 가상 환경 생성 및 활성화:
```bash
python -m venv venv
venv\Scripts\activate  # Windows
```

2. 패키지 설치:
```bash
pip install -r requirements.txt
```

3. Playwright 브라우저 설치:
```bash
playwright install chromium
```

4. 환경 변수 설정:
`.env` 파일을 생성하고 `env.example`을 참고하여 설정합니다.

## 환경 변수 설정

`.env` 파일을 생성하고 `env.example`을 참고하여 다음 변수들을 설정하세요:

### Web Configuration
- `WEB_BASE_URL`: Web 애플리케이션 기본 URL (예: http://localhost:3000)

### Backend Configuration
- `BACKEND_BASE_URL`: 백엔드 API 서버 기본 URL (예: http://localhost:5000)

### OAuth Configuration
- `KAKAO_ACCESS_TOKEN`: Kakao OAuth 액세스 토큰
- `KAKAO_REFRESH_TOKEN`: Kakao OAuth 리프레시 토큰
- `KAKAO_REST_API_KEY`: Kakao REST API 키
- `NAVER_CLIENT_ID`: Naver OAuth 클라이언트 ID
- `NAVER_CLIENT_SECRET`: Naver OAuth 클라이언트 시크릿
- `NAVER_ACCESS_TOKEN`: Naver OAuth 액세스 토큰
- `NAVER_REFRESH_TOKEN`: Naver OAuth 리프레시 토큰

### Web Browser Configuration
- `HEADLESS`: 브라우저 헤드리스 모드 설정 (true/false)

### JWT Configuration
- `WEB_TEST_JWT_TOKEN`: Web 테스트용 JWT 토큰
- `WEB_TEST_JWT_USER`: Web 테스트용 JWT 사용자
- `JWT_SECRET`: JWT 시크릿 키
- `JWT_USER_ID`: JWT 사용자 ID
- `JWT_USER_EMAIL`: JWT 사용자 이메일
- `JWT_USER_PROVIDER`: JWT 사용자 프로바이더 (기본값: test)

## 실행 방법

### 전체 테스트 실행
```bash
pytest
```

### 특정 테스트만 실행
```bash
# API 테스트만
pytest tests/test_api.py

# 로그인 테스트만
pytest tests/test_login.py

# Web 테스트만
pytest tests/test_web.py
```

## 코드 품질 검사

### Flake8 실행
```bash
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
```

### GitHub Actions
프로젝트에 GitHub Actions workflow가 설정되어 있어, push나 pull request 시 자동으로 flake8 린트 검사가 실행됩니다.

## 테스트 리포트

테스트 실행 후 `Result/{YYYY-MM-DD_HH-MM-SS}/` 디렉토리에 HTML 리포트가 생성됩니다.
각 테스트 실행마다 타임스탬프 기반의 새로운 디렉토리가 생성됩니다.

## Page Object Model 패턴

이 프로젝트는 POM 패턴을 사용하여 테스트 코드를 구조화합니다:

- **Actions**: 페이지별 액션을 캡슐화한 클래스 (`src/actions/`)
- **Locators**: 페이지 요소의 로케이터를 관리 (`src/locators/`)
- **Base Classes**: 각 플랫폼(API, Web)에 대한 기본 클래스 제공
- **Utils**: 공통 유틸리티 함수 (`src/utils/`)
- **Test Files**: 테스트 케이스만 포함 (`tests/`)

## 기술 스택

- **Testing Framework**: pytest, pytest-html, pytest-check
- **API Testing**: requests
- **Web Testing**: Playwright
- **Environment Management**: python-dotenv
- **JWT**: PyJWT
- **Code Quality**: flake8

## 참고사항

- Web 테스트의 경우 Playwright 브라우저가 설치되어 있어야 합니다.
- API 테스트는 실제 API 서버가 실행 중이어야 합니다.
- OAuth 테스트를 위해서는 해당 OAuth 서비스의 인증 정보가 필요합니다.
- JWT 토큰이 필요한 테스트의 경우 `.env` 파일에 유효한 토큰을 설정해야 합니다.