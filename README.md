# Todo List Test Automation

이 테스트 자동화 프로젝트는 **pytest와 POM(Page Object Model)** 구조를 기반으로 API·UI 레벨의 동작을 검증하도록 설계된 품질 보증 테스트 스택입니다.  
Dev 이미지가 배포되면 **Token Refresh 파이프라인이 자동 트리거**되어 최신 인증 상태를 유지하고, Refresh 단계가 성공하면 **API/UI 통합 테스트가 실행**되어 서비스의 엔드투엔드 품질을 검증하는 구조로 구성돼 있습니다.

---

## 🧩 기술 스택

- pytest / pytest-html / pytest-check  
- Playwright  
- requests  
- python-dotenv  
- Flake8  
- Jenkins / GitHub Actions  

---

## 🏗 Page Object Model (POM)

### 구성 요소
- **Actions**: 비즈니스 액션 (`src/actions/`)  
- **Locators**: 선택자 (`src/locators/`)  
- **Utils**: 공통 모듈 (`src/utils/`)  
- **Tests**: 실제 테스트 케이스 (`tests/`)  

---

## 🗂 프로젝트 구조

```
todolist_test/
├── .gitignore
├── .flake8
├── conftest.py
├── pytest.ini
├── requirements.txt
├── ci/
│   ├── Jenkinsfile.test
│   ├── Jenkinsfile.refresh
│   └── check_token_status.py
├── postman/
│   ├── README.md
│   ├── todolist_postman_collection.json
│   └── todolist_postman_environment.json
├── src/
│   ├── actions/
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
│       ├── env_loader.py
│       ├── health_check.py
│       └── jwt.py
├── tests/
│   ├── test_api.py
│   ├── test_login.py
│   └── test_web.py
└── Result/
```

---

## 🚀 CI/CD 파이프라인

### Jenkins 구성 개요
프로젝트는 운영·테스트 품질을 보장하기 위해 **두 개의 독립 파이프라인**을 제공합니다.

### 🧪 Jenkinsfile.test — 테스트 실행 파이프라인

- 최신 소스 체크아웃 및 venv 표준화  
- Playwright Chromium 설치  
- Jenkins Credential 기반 환경 변수/토큰 로드  
- 백엔드/웹 엔드포인트 ENV 파싱  
- API + UI 통합 테스트 실행  
- HTML 리포트 자동 아카이브  

### 🔄 Jenkinsfile.refresh — 토큰 갱신 파이프라인

- Token Manager 스크립트 실행 준비  
- 가상환경 생성 및 패키지 설치  
- JWT/Naver/Kakao 토큰 Credential 로드  
- ENV 파일에서 OAuth Client 정보 파싱  
- 만료 토큰 자동 갱신 및 Jenkins Credential 업데이트  

### 필요한 Jenkins Credentials
- `todolist_dev_env_test` (Secret file)  
- `JWT_TOKEN`, `JWT_REFRESH_TOKEN`  
- `KAKAO_ACCESS_TOKEN`, `KAKAO_REFRESH_TOKEN`  
- `NAVER_ACCESS_TOKEN`, `NAVER_REFRESH_TOKEN`  
- `KAKAO_REST_API_KEY`  
- `NAVER_CLIENT_ID`, `NAVER_CLIENT_SECRET`  
- `jenkins-admin`  

---

## 🧼 코드 품질 검사 (Flake8)

간단 검사:
```bash
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
```

전체 검사:
```bash
flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
```

---

## ⚙️ 설치 방법

### 1) 의존성 설치
```bash
pip install -r requirements.txt
```

### 2) Playwright 브라우저 설치
```bash
playwright install chromium
```

### 3) 환경 변수 설정
`.env` 파일 생성 후 값 입력  
(템플릿 `.env.example` 포함됨)

---

## 🌎 환경 변수 설정

### ✔ 로딩 규칙 (`env_loader.py`)
1. **Jenkins 환경** → ENV_FILE(Jenkins Credential)만 로드  
2. **로컬 환경** → 프로젝트 루트 `.env` 로드

### ✔ 필수 환경 변수 그룹
- **Web / Backend URL**
- **Kakao / Naver OAuth 토큰 및 Client 정보**
- **JWT 인증 정보**
- **브라우저 설정 (HEADLESS)**

---

## 📊 테스트 리포트

모든 실행 결과는 자동으로:

`Result/{YYYY-MM-DD_HH-MM-SS}/`  

에 HTML 리포트로 저장됩니다.

포함 내용:
- 통과/실패 요약  
- 실행 시간  
- 실행 로그  
- 오류 상세  

---

## 📮 Postman API 테스트

GUI 환경에서 API를 수동 테스트하고 싶다면 Postman Collection을 사용할 수 있습니다.

**📂 위치**: `postman/`  
**📘 가이드**: `postman/README.md`

### 제공 기능
- Health Check  
- Token 갱신  
- Kakao/Naver OAuth  
- Todo CRUD  

### 빠른 시작
1. Collection import  
2. Environment import  
3. 변수 입력  
4. API 실행  

---
