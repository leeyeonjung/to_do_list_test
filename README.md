# Todo List Test Automation

POM(Page Object Model) 구조를 적용한 pytest 기반 테스트 자동화 프로젝트입니다.

## 프로젝트 구조

```
to_do_list_test/
├── .env                    # 환경 변수 설정 파일 (gitignore에 포함)
├── .gitignore             # Git 무시 파일 목록
├── conftest.py            # pytest 설정 및 fixture
├── pytest.ini             # pytest 설정
├── requirements.txt       # Python 패키지 의존성
├── pages/                 # Page Object Model 클래스
│   ├── api/               # API 테스트용 Base 클래스
│   │   └── base_api.py
│   └── web/               # Web 테스트용 Base 클래스
│       └── base_page.py
└── tests/                 # 테스트 파일
    ├── test_api.py        # API 테스트
    └── test_web.py        # Web 테스트
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

`.env` 파일에 다음 변수들을 설정하세요:

- `API_BASE_URL`: API 서버 기본 URL
- `WEB_BASE_URL`: Web 애플리케이션 기본 URL

## 실행 방법

### 전체 테스트 실행
```bash
pytest
```

### 특정 테스트만 실행
```bash
# API 테스트만
pytest tests/test_api.py

# Web 테스트만
pytest tests/test_web.py
```

### 마커를 사용한 테스트 실행
```bash
# API 테스트만
pytest -m api

# Smoke 테스트만
pytest -m smoke
```

### 병렬 실행
```bash
pytest -n auto
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

테스트 실행 후 `Result/test-reports/` 디렉토리에 HTML 리포트가 생성됩니다.

## Page Object Model 패턴

이 프로젝트는 POM 패턴을 사용하여 테스트 코드를 구조화합니다:

- **Base Classes**: 각 플랫폼(API, Web)에 대한 기본 클래스 제공
- **Page Objects**: 페이지별 로직을 캡슐화
- **Test Files**: 테스트 케이스만 포함

## 기술 스택

- **Testing Framework**: pytest
- **API Testing**: requests
- **Web Testing**: Playwright
- **Code Quality**: flake8

## 참고사항

- Web 테스트의 경우 Playwright 브라우저가 설치되어 있어야 합니다.
- API 테스트는 실제 API 서버가 실행 중이어야 합니다.

