# Todo List Test Automation

본 프로젝트는 Web 서비스 배포 파이프라인에 테스트 자동화를 통합하여  
코드 변경부터 운영 배포까지의 전 과정을 QA 관점에서 안정적으로 검증하기 위해 설계된 테스트 자동화 프로젝트입니다.

테스트는 pytest + Page Object Model(POM) 기반으로 API 및 Web UI 레벨에서 수행되며,  
인증 토큰 갱신을 테스트 코드와 분리해 파이프라인 레벨에서 관리함으로써 외부 인증 상태 변화로 인한 불안정성을 최소화했습니다.

---

## 📌 핵심 포인트

- 배포 후 자동 테스트 트리거: Dev 배포 → Token Refresh → API/UI E2E 테스트
- 인증 관리 책임 분리: 토큰 갱신은 별도 파이프라인에서 처리, 테스트 코드는 검증에 집중
- 유지보수성: POM 구조로 UI 변경에 강한 코드 구성
- 추적 가능성: pytest-html 리포트 및 Jenkins 아카이브로 실행 이력 관리

---

## 🧭 목차

- [🎬 실행 결과](#-실행-결과)
- [🗺 파이프라인 구성도](#-파이프라인-구성도)
- [🔁 동작 흐름](#-동작-흐름)
- [🧩 기술 스택](#-기술-스택)
- [⚙️ Quick Start](#quick-start)
- [🌎 Environment Variables](#-environment-variables)
- [🗂 프로젝트 구조](#-프로젝트-구조)
- [🏗 테스트 코드 설계 (POM)](#-테스트-코드-설계-pom)
- [🚀 Jenkins 파이프라인 구성](#-jenkins-파이프라인-구성)
- [📊 테스트 리포트](#-테스트-리포트)
- [📮 Postman API 테스트](#-postman-api-테스트)
- [🔗 참고 링크](#-참고-링크)

---

## 🎬 실행 결과

- 파이프라인 실행 영상

https://github.com/user-attachments/assets/55f1d85b-0fa9-4bcb-a511-4af79b46bdc9

- Test Report 예시 ([Link](https://htmlpreview.github.io/?https://github.com/leeyeonjung/to_do_list_test/blob/main/Result/2025-12-15_14-10-45/report_2025-12-15_14-10-45.html))
<img width="640" height="289" alt="todolist_Report" src="https://github.com/user-attachments/assets/3d433d3a-2582-4752-9b2c-ccb842f308cf" />


---

## 🗺 파이프라인 구성도
<img width="512" height="340" alt="todolist" src="https://github.com/user-attachments/assets/8ff1fe7a-1701-4413-9ee3-4961781911c9" />



---

## 🔁 동작 흐름

1. App Source Repository 코드 변경  
2. GitHub Webhook → Jenkins Controller 트리거  
3. Application Pipeline (`todolist_deploy`) 실행  
4. Test 환경 Docker 이미지 빌드 및 배포  
5. Token Refresh Pipeline (`todolist_refresh_tokens`) 실행  
6. Jenkins Credentials 인증 정보 갱신  
7. Test Pipeline (`todolist_test`)에서 API / Web UI 테스트 실행  
8. 테스트 성공 시 Production 환경 배포  
9. 테스트 결과 Jenkins 아카이브 관리  

---

## 🧩 기술 스택
| 구분 | 기술 |
|---|---|
| Test Framework | pytest, pytest-check, pytest-html |
| Web Automation | Playwright |
| API Test | requests |
| Config | python-dotenv |
| Quality | Flake8 |
| CI/CD | Jenkins, GitHub Actions |

---

<a name="quick-start"></a>
## ⚙️ Quick Start
```bash
pip install -r requirements.txt
playwright install chromium
pytest -v
```

---

## 🌎 Environment Variables
| 그룹 | KEY | 용도 |
|---|---|---|
| Web | `WEB_BASE_URL` | Web 서비스 Base URL |
| Backend | `BACKEND_BASE_URL` | Backend(API) Base URL |
| Browser | `HEADLESS` | Playwright Headless 실행 여부 (`true/false`) |
| Kakao OAuth | `KAKAO_REST_API_KEY` | Kakao OAuth Client Key |
| Kakao OAuth | `KAKAO_ACCESS_TOKEN` | Kakao Access Token |
| Kakao OAuth | `KAKAO_REFRESH_TOKEN` | Kakao Refresh Token |
| Naver OAuth | `NAVER_CLIENT_ID` | Naver Client ID |
| Naver OAuth | `NAVER_CLIENT_SECRET` | Naver Client Secret |
| Naver OAuth | `NAVER_ACCESS_TOKEN` | Naver Access Token |
| Naver OAuth | `NAVER_REFRESH_TOKEN` | Naver Refresh Token |
| Web Test (Playwright) | `WEB_TEST_JWT_TOKEN` | Web UI 테스트용 JWT(Playwright 로그인/세션 용) |
| Web Test (Playwright) | `WEB_TEST_JWT_USER` | Web UI 테스트용 사용자 식별 정보 |
| Test User | `JWT_USER_ID` | 테스트 사용자 ID |
| Test User | `JWT_USER_EMAIL` | 테스트 사용자 이메일 |
| Test User | `JWT_USER_PROVIDER` | 테스트 사용자 Provider (`test` 등) |
| JWT/Auth | `JWT_SECRET` | JWT 서명/검증용 Secret |
| JWT/Auth | `JWT_TOKEN` | JWT Access Token |
| JWT/Auth | `JWT_REFRESH_TOKEN` | JWT Refresh Token |

---

## 🗂 프로젝트 구조

```text
todolist_test/
├── .github/                          # GitHub Actions 설정
│   └── workflows/                    # 워크플로우 정의 폴더
│       └── lint.yml                  # 코드 린트(Flake8 등) 자동 실행 워크플로우
├── ci/                               # Jenkins 파이프라인/토큰 관련
│   ├── jenkinsfile.refresh           # 토큰 갱신 파이프라인
│   ├── jenkinsfile.test              # 테스트 실행 파이프라인
│   └── check_token_status.py         # 토큰 상태 점검 스크립트
├── postman/                          # Postman 수동 API 테스트
│   ├── README.md                     # 사용 가이드
│   ├── todolist_postman_collection.json   # 요청 모음(컬렉션)
│   └── todolist_postman_environment.json  # 환경 변수 템플릿
├── src/                              # 재사용 코드(POM)
│   ├── actions/                      # 동작 정의(API/UI 액션)
│   │   ├── api/
│   │   │   └── base_api.py           # API 공통 요청 베이스
│   │   └── web/
│   │       ├── auth_actions.py       # 인증/로그인 액션
│   │       ├── base_page.py          # 공통 페이지 베이스
│   │       └── todo_actions.py       # Todo 화면 액션
│   ├── locators/                     # UI 선택자 모음
│   │   └── web/
│   │       ├── auth_locators.py      # 인증 화면 선택자
│   │       └── todo_locators.py      # Todo 화면 선택자
│   └── utils/                        # 공통 유틸
│       ├── env_loader.py             # 환경 변수 로딩
│       ├── health_check.py           # 상태 점검
│       └── jwt.py                    # JWT 유틸
├── tests/                            # 테스트 시나리오
│   ├── test_api.py                   # API 테스트
│   ├── test_login.py                 # 로그인 테스트
│   └── test_web.py                   # Web UI 테스트
├── Result/                           # 테스트 결과/리포트 저장
├── conftest.py                       # pytest 공통 fixture
├── pytest.ini                        # pytest 설정
├── .flake8                           # 린트 규칙
├── .gitignore                        # 제외 파일 목록
└── requirements.txt                  # 의존성 목록
```

---

## 🏗 테스트 코드 설계 (POM)

POM 구조를 적용하여 UI 변경에 강한 테스트 코드 구조를 유지했습니다.  
또한 인증 관리를 파이프라인으로 분리해 각 책임을 명확히 했습니다.

- 인증 상태 관리 → Token Refresh Pipeline
- 테스트 검증 로직 → Test Pipeline

### 구성 요소

- Actions: 비즈니스 동작 정의 (`src/actions/`)  
- Locators: UI 선택자 관리 (`src/locators/`)  
- Utils: 환경·토큰 공통 모듈 (`src/utils/`)  
- Tests: 테스트 시나리오 (`tests/`)  

---

## 🚀 Jenkins 파이프라인 구성
- Jenkins: http://3.36.219.242:8080 (ID: guest / PW: guest)
(상세 링크 하단 [🔗 참고 링크](#-참고-링크) 참조)

### 🔹 Application Pipeline (`todolist_deploy`)
- main 브랜치 변경 감지  
- Test 환경 Docker 이미지 빌드 및 배포  
- 테스트 성공 시 Production 환경 배포  

### 🔹 Token Refresh Pipeline (`todolist_refresh_tokens`)
- 테스트 전 인증 토큰 유효성 점검  
- JWT / Kakao / Naver 토큰 자동 갱신  
- Jenkins Credentials 중앙 관리  

### 🔹 Test Pipeline (`todolist_test`)
- 최신 인증 정보 기반 API / Web UI 테스트 실행  
- Headless Web UI 테스트  
- HTML 리포트 생성 및 Jenkins 아카이브  

---

## 📊 테스트 리포트

- 저장 위치  
  `Result/{YYYY-MM-DD_HH-MM-SS}/`

- 제공 정보  
  - 통과 / 실패 요약  
  - 실행 시간  
  - 오류 상세  

---
## 📮 Postman API 테스트

- 📂 폴더: [`postman/`](https://github.com/leeyeonjung/to_do_list_test/tree/main/postman)
- 📘 가이드: [`postman/README.md`](https://github.com/leeyeonjung/to_do_list_test/blob/main/postman/README.md)
- 🧾 컬렉션: [`todolist_postman_collection.json`](https://github.com/leeyeonjung/to_do_list_test/blob/main/postman/todolist_postman_collection.json)
- 🌎 환경 템플릿: [`todolist_postman_environment.json`](https://github.com/leeyeonjung/to_do_list_test/blob/main/postman/todolist_postman_environment.json)

---

## 🔗 참고 링크

- App Source Repository: https://github.com/leeyeonjung/to_do_list_app  
- Jenkins: http://3.36.219.242:8080 (ID: guest / PW: guest)  
  - `todolist_deploy`: http://3.36.219.242:8080/view/todolist/job/todolist_deploy/  
  - `todolist_refresh_tokens`: http://3.36.219.242:8080/view/todolist/job/todolist_refresh_tokens/  
  - `todolist_test`: http://3.36.219.242:8080/view/todolist/job/todolist_test/

