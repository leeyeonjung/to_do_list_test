# Todo List Test Automation

POM(Page Object Model) 구조를 적용한 pytest 기반 테스트 자동화 프로젝트입니다.

## 프로젝트 구조

```
todolist_test/
├── .env                    # 환경 변수 설정 파일 (로컬 개발용, gitignore에 포함)
├── .env-dev-test           # CI/CD 기본 환경 변수 파일 (gitignore에 포함)
├── .env.example            # 환경 변수 예제 파일
├── .gitignore              # Git 무시 파일 목록
├── conftest.py             # pytest 설정 및 fixture
├── pytest.ini              # pytest 설정
├── requirements.txt        # Python 패키지 의존성
├── ci/                     # CI/CD 설정
│   └── Jenkinsfile         # Jenkins 파이프라인 설정
├── src/                    # 소스 코드
│   ├── actions/            # 액션 클래스 (POM 패턴)
│   │   ├── api/            # API 테스트용 클래스
│   │   │   └── base_api.py
│   │   └── web/            # Web 테스트용 클래스
│   │       ├── auth_actions.py
│   │       ├── base_page.py
│   │       └── todo_actions.py
│   ├── locators/           # 페이지 로케이터
│   │   └── web/
│   │       ├── auth_locators.py
│   │       └── todo_locators.py
│   └── utils/              # 유틸리티 함수
│       ├── env_loader.py   # 환경 변수 로딩 유틸리티
│       └── token_validator.py  # 토큰 검증 및 갱신 유틸리티
├── tests/                  # 테스트 파일
│   ├── test_api.py         # API 테스트
│   ├── test_login.py       # 로그인 테스트 (Kakao/Naver OAuth)
│   └── test_web.py         # Web 테스트
└── Result/                 # 테스트 리포트 저장 디렉토리
```

## 설치 방법

1. 가상 환경 생성 및 활성화:
```bash
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
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
`.env` 파일을 생성하고 `.env.example`을 참고하여 설정합니다.

## 환경 변수 설정

### 환경 변수 로딩 우선순위

프로젝트는 다음 순서로 환경 변수를 로드합니다:

1. **ENV_FILE 환경 변수** (Jenkins credential을 통해 주입) - 최우선
2. **프로젝트 루트의 `.env` 파일** (로컬 환경)
3. **프로젝트 루트의 `.env-dev-test` 파일** (CI 기본값, Jenkins에서 ENV_FILE이 없을 때 fallback)

### 필수 환경 변수

#### Web Configuration
- `WEB_BASE_URL`: Web 애플리케이션 기본 URL (예: http://localhost:3000)

#### Backend Configuration
- `BACKEND_BASE_URL`: 백엔드 API 서버 기본 URL (예: http://localhost:5000)

#### OAuth Configuration
- `KAKAO_ACCESS_TOKEN`: Kakao OAuth 액세스 토큰
- `KAKAO_REFRESH_TOKEN`: Kakao OAuth 리프레시 토큰
- `KAKAO_REST_API_KEY`: Kakao REST API 키
- `NAVER_CLIENT_ID`: Naver OAuth 클라이언트 ID
- `NAVER_CLIENT_SECRET`: Naver OAuth 클라이언트 시크릿
- `NAVER_ACCESS_TOKEN`: Naver OAuth 액세스 토큰
- `NAVER_REFRESH_TOKEN`: Naver OAuth 리프레시 토큰

#### Web Browser Configuration
- `HEADLESS`: 브라우저 헤드리스 모드 설정 (true/false, 기본값: true)

#### JWT Configuration
- `JWT_SECRET`: JWT 시크릿 키
- `JWT_USER_ID`: JWT 사용자 ID (기본값: 1)
- `JWT_USER_EMAIL`: JWT 사용자 이메일 (선택)
- `JWT_USER_PROVIDER`: JWT 사용자 프로바이더 (기본값: test)
- `JWT_TOKEN`: JWT 토큰 (자동 갱신됨)
- `JWT_REFRESH_TOKEN`: JWT 리프레시 토큰 (선택)

## 실행 방법

### 전체 테스트 실행
```bash
pytest
```

### 특정 테스트만 실행
```bash
# API 테스트만
pytest tests/test_api.py

# 로그인 테스트만 (Kakao/Naver OAuth)
pytest tests/test_login.py

# Web 테스트만
pytest tests/test_web.py
```

### 테스트 옵션
```bash
# 첫 번째 실패 시 중단
pytest --maxfail=1

# HTML 리포트 생성
pytest --html=report.html

# 상세 로그 출력
pytest -v -s
```

## CI/CD

### Jenkins

프로젝트는 Jenkins 파이프라인을 통해 자동화된 테스트를 실행합니다.

**Jenkins Credentials 설정:**
- `todolist_dev_env_test`: 환경 변수 파일 (Secret file)
- `JWT_TOKEN`, `JWT_REFRESH_TOKEN`: JWT 토큰 (Secret text)
- `KAKAO_ACCESS_TOKEN`, `KAKAO_REFRESH_TOKEN`: Kakao OAuth 토큰 (Secret text)
- `NAVER_ACCESS_TOKEN`, `NAVER_REFRESH_TOKEN`: Naver OAuth 토큰 (Secret text)
- `jenkins-admin`: Jenkins 관리자 계정 (Username with password)

**파이프라인 단계:**
1. Python 환경 설정 (가상 환경 생성 및 패키지 설치)
2. 테스트 실행 (환경 변수 주입 및 pytest 실행)
3. 테스트 리포트 아카이브

**환경 변수 fallback:**
- Jenkins에서 `ENV_FILE` credential이 제공되지 않거나 파일이 존재하지 않을 경우, 워크스페이스의 `.env-dev-test` 파일을 자동으로 사용합니다.

### GitHub Actions

프로젝트에 GitHub Actions workflow가 설정되어 있어, push나 pull request 시 자동으로 flake8 린트 검사가 실행됩니다.

## 코드 품질 검사

### Flake8 실행
```bash
# 심각한 오류만 검사
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics

# 전체 검사 (복잡도 및 라인 길이 포함)
flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
```

## 테스트 리포트

테스트 실행 후 `Result/{YYYY-MM-DD_HH-MM-SS}/` 디렉토리에 HTML 리포트가 자동으로 생성됩니다.
각 테스트 실행마다 타임스탬프 기반의 새로운 디렉토리가 생성됩니다.

리포트는 다음 정보를 포함합니다:
- 테스트 실행 결과 (통과/실패)
- 실행 시간
- 로그 메시지
- 실패한 테스트의 상세 정보

## Page Object Model 패턴

이 프로젝트는 POM 패턴을 사용하여 테스트 코드를 구조화합니다:

- **Actions**: 페이지별 액션을 캡슐화한 클래스 (`src/actions/`)
  - `BaseAPI`: API 테스트용 기본 클래스
  - `BasePage`: Web 테스트용 기본 클래스
  - `AuthActions`: 인증 관련 액션
  - `TodoActions`: 할일 관리 액션
- **Locators**: 페이지 요소의 로케이터를 관리 (`src/locators/`)
- **Utils**: 공통 유틸리티 함수 (`src/utils/`)
  - `env_loader.py`: 환경 변수 로딩 및 관리
  - `token_validator.py`: JWT 및 OAuth 토큰 검증 및 갱신
- **Test Files**: 테스트 케이스만 포함 (`tests/`)

## 토큰 관리

프로젝트는 자동으로 토큰을 검증하고 갱신합니다:

- **JWT 토큰**: `ensure_valid_jwt_token()` 함수가 기존 토큰을 검증하고, 만료된 경우 새로 발급합니다.
- **OAuth 토큰 (Kakao/Naver)**: `ensure_valid_oauth_token()` 함수가 액세스 토큰을 검증하고, 만료된 경우 리프레시 토큰을 사용하여 갱신합니다.
- 갱신된 토큰은 자동으로 환경 변수 파일에 업데이트됩니다.

## 기술 스택

- **Testing Framework**: pytest, pytest-html, pytest-check
- **API Testing**: requests
- **Web Testing**: Playwright
- **Environment Management**: python-dotenv
- **Code Quality**: flake8
- **CI/CD**: Jenkins, GitHub Actions

## 참고사항

- Web 테스트의 경우 Playwright 브라우저가 설치되어 있어야 합니다.
- API 테스트는 실제 API 서버가 실행 중이어야 합니다.
- OAuth 테스트를 위해서는 해당 OAuth 서비스의 유효한 인증 정보가 필요합니다.
- JWT 토큰이 필요한 테스트의 경우, 토큰이 자동으로 발급되거나 `.env` 파일에 유효한 토큰을 설정해야 합니다.
- Jenkins 환경에서는 credential을 통해 환경 변수가 주입되며, 로컬 환경에서는 `.env` 파일을 사용합니다.
