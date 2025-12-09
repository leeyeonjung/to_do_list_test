# Todo List Test Automation

POM(Page Object Model) 구조를 적용한 pytest 기반 테스트 자동화 프로젝트입니다.

## 프로젝트 구조

```
todolist_test/
├── .gitignore
├── .flake8
├── conftest.py             # pytest 설정 및 fixture (헬스 체크/HTML 리포트 경로 설정)
├── pytest.ini              # pytest 설정
├── requirements.txt        # Python 패키지 의존성
├── ci/
│   ├── Jenkinsfile.test    # 테스트 실행 파이프라인
│   ├── Jenkinsfile.refresh # 토큰 갱신 파이프라인
│   └── check_token_status.py
├── src/
│   ├── actions/            # 액션 클래스 (POM 패턴)
│   │   ├── api/
│   │   │   └── base_api.py
│   │   └── web/
│   │       ├── auth_actions.py
│   │       ├── base_page.py
│   │       └── todo_actions.py
│   ├── locators/
│   │   └── web/
│   │       ├── auth_locators.py
│   │       └── todo_locators.py
│   └── utils/
│       ├── env_loader.py   # 환경 변수 로딩 유틸리티
│       ├── health_check.py # 백/프론트 헬스 체크 유틸
│       └── jwt.py          # Playwright JWT 주입/헤더 설정
├── tests/
│   ├── test_api.py         # API 테스트
│   ├── test_login.py       # Kakao/Naver OAuth 테스트
│   └── test_web.py         # Web 테스트
└── Result/                 # pytest HTML 리포트 저장 디렉토리
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
`.env` 파일을 생성해 필요한 값을 채워 넣습니다. (현재 리포지토리에 `.env.example`이 포함 되어 있습습니다.)

## 환경 변수 설정

### 환경 변수 로딩 우선순위

프로젝트는 다음 순서로 환경 변수를 로드합니다 (`src/utils/env_loader.py`):

1. **ENV_FILE 환경 변수**(Jenkins credential 파일 경로) - 최우선
2. **프로젝트 루트의 `.env` 파일**(존재할 경우 후순위로 병합)

### 필수 환경 변수

#### Web Configuration
- `WEB_BASE_URL`: Web 애플리케이션 기본 URL

#### Backend Configuration
- `BACKEND_BASE_URL`: 백엔드 API 서버 기본 URL

#### OAuth Configuration
- `KAKAO_ACCESS_TOKEN`: Kakao OAuth 액세스 토큰
- `KAKAO_REFRESH_TOKEN`: Kakao OAuth 리프레시 토큰
- `KAKAO_REST_API_KEY`: Kakao REST API 키
- `NAVER_CLIENT_ID`: Naver OAuth 클라이언트 ID
- `NAVER_CLIENT_SECRET`: Naver OAuth 클라이언트 시크릿
- `NAVER_ACCESS_TOKEN`: Naver OAuth 액세스 토큰
- `NAVER_REFRESH_TOKEN`: Naver OAuth 리프레시 토큰

#### Web Browser Configuration
- `HEADLESS`: 브라우저 헤드리스 모드 설정 (`true`/`false`, 기본값: `true`)

#### JWT Configuration
- `JWT_TOKEN`: JWT 토큰
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

두 개의 파이프라인이 제공됩니다.

- `ci/Jenkinsfile.test`: 최신 크리덴셜로 가상환경 생성 → 의존성 설치/Playwright 설치 → `ENV_FILE`에서 `BACKEND_BASE_URL`을 추출해 주입하고 JWT/소셜 토큰을 환경 변수로 주입 → pytest 실행 → `Result/**/*.html` 아카이브
- `ci/Jenkinsfile.refresh`: 토큰 갱신 전용 잡. 가상환경 구성 후 `ci/check_token_status.py`를 실행해 JWT/Kakao/Naver 토큰을 갱신하고 Jenkins 크리덴셜(`todolist_dev` 도메인)에 업데이트.

**Jenkins Credentials 예시:**
- `todolist_dev_env_test`: ENV_FILE로 전달되는 환경 변수 파일 (Secret file, `BACKEND_BASE_URL` 포함)
- `JWT_TOKEN`, `JWT_REFRESH_TOKEN`: JWT 토큰 (Secret text)
- `KAKAO_ACCESS_TOKEN`, `KAKAO_REFRESH_TOKEN`: Kakao OAuth 토큰 (Secret text)
- `NAVER_ACCESS_TOKEN`, `NAVER_REFRESH_TOKEN`: Naver OAuth 토큰 (Secret text)
- `KAKAO_REST_API_KEY`, `NAVER_CLIENT_ID`, `NAVER_CLIENT_SECRET`: 소셜 갱신에 필요
- `jenkins-admin`: Jenkins 기본 인증 계정 (Username with password)

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

- 로그인 테스트는 `KAKAO_ACCESS_TOKEN`, `NAVER_ACCESS_TOKEN` 환경변수를 사용해 소셜 로그인 API를 호출하고, 응답의 `token`, `refreshToken` 키를 검증합니다 (`tests/test_login.py`).
- Jenkins 환경에서는 `ci/check_token_status.py`와 `Jenkinsfile.refresh`를 통해 JWT/Kakao/Naver 토큰을 주기적으로 갱신해 크리덴셜 스토어에 반영할 수 있습니다.
- 로컬/CI 테스트 실행 시에는 유효한 JWT/소셜 토큰을 `.env` 또는 Jenkins 크리덴셜을 통해 주입해야 합니다.

## 기술 스택

- **Testing Framework**: pytest, pytest-html, pytest-check
- **API Testing**: requests
- **Web Testing**: Playwright
- **Environment Management**: python-dotenv
- **Code Quality**: flake8
- **CI/CD**: Jenkins, GitHub Actions

## 참고사항

- `conftest.py`가 테스트 시작 시 백엔드(`BACKEND_BASE_URL`)/프론트엔드(`WEB_BASE_URL`)의 `/health` 엔드포인트를 체크합니다. 응답이 기대 형태가 아니면 테스트를 중단합니다.
- Web 테스트를 위해서는 Playwright 브라우저가 설치되어 있어야 합니다 (`playwright install chromium`).
- API 테스트는 실제 API 서버가 동작 중이어야 합니다.
- OAuth/JWT 테스트에는 유효한 토큰이 필요하며 자동 갱신 로직은 CI 토큰 매니저(`Jenkinsfile.refresh`)에 한정됩니다.
