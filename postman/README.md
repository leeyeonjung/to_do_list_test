# 📮 Postman API Collection

이 폴더는 TodoList API를 Postman에서 테스트할 수 있는 Collection과 Environment 파일을 포함합니다.

## 📁 파일 구성

| 파일 | 설명 |
|------|------|
| `todolist_postman_collection.json` | API 요청 모음 및 테스트 스크립트 |
| `todolist_postman_environment.json` | 환경 변수 템플릿 |

## 🚀 빠른 시작

### 1단계: Collection Import

1. **Postman** 실행 (무료 계정 생성 필요)
2. **Import** 버튼 클릭
3. `todolist_postman_collection.json` 파일 선택
4. Import 완료

### 2단계: Environment Import

1. **Import** 버튼 클릭
2. `todolist_postman_environment.json` 파일 선택
3. Import 완료

### 3단계: Environment 활성화

1. 우측 상단 환경 드롭다운 클릭
2. **"TodoList Test Environment"** 선택

### 4단계: 환경 변수 설정

1. 우측 상단 환경 아이콘 (👁️) 클릭
2. **Edit** 클릭
3. **Current Value**에 실제 값 입력 후 **Save**

## 🔧 환경 변수 설정 가이드

### 📌 기본 설정 (필수)

| 변수 | 예시 값 | 설명 |
|------|---------|------|
| `BACKEND_BASE_URL` | `http://localhost:5000` | 백엔드 API 서버 URL |
| `WEB_BASE_URL` | `http://localhost:3000` | 웹 프론트엔드 URL |
| `TODO_ID` | (자동 저장) | Create Todo 실행 시 자동 설정 |

### 🟡 Kakao 설정 (Social Login 테스트용)

| 변수 | 설명 | 획득 방법 |
|------|------|----------|
| `KAKAO_REST_API_KEY` | REST API 키 | [Kakao Developers](https://developers.kakao.com/) |
| `KAKAO_ACCESS_TOKEN` | 액세스 토큰 | Refresh API 또는 OAuth 인증 |
| `KAKAO_REFRESH_TOKEN` | 리프레시 토큰 | OAuth 인증 시 획득 |

### 🟢 Naver 설정 (Social Login 테스트용)

| 변수 | 설명 | 획득 방법 |
|------|------|----------|
| `NAVER_CLIENT_ID` | 클라이언트 ID | [Naver Developers](https://developers.naver.com/) |
| `NAVER_CLIENT_SECRET` | 클라이언트 시크릿 | Naver Developers |
| `NAVER_ACCESS_TOKEN` | 액세스 토큰 | Refresh API 또는 OAuth 인증 |
| `NAVER_REFRESH_TOKEN` | 리프레시 토큰 | OAuth 인증 시 획득 |

### 🔵 JWT 설정 (Internal API용)

| 변수 | 설명 | 획득 방법 |
|------|------|----------|
| `JWT_TOKEN` | JWT 토큰 | Social Login 응답 또는 Refresh API |
| `JWT_REFRESH_TOKEN` | JWT 리프레시 토큰 | Social Login 응답 |

## 📂 Collection 구조

```
TodoList API Test Collection
├── 🏥 Health Check
│   ├── Backend Health Check (JSON)
│   └── Web Health Check (Text)
├── 🔑 Token Management
│   ├── Refresh JWT Token
│   ├── Validate JWT Token
│   ├── Refresh Kakao Token
│   ├── Validate Kakao Token
│   ├── Refresh Naver Token
│   └── Validate Naver Token
├── 🔐 Social Login
│   ├── Kakao Login
│   └── Naver Login
└── 📝 Todo CRUD
    ├── Get All Todos
    ├── Create Todo
    ├── Get Todo By ID
    ├── Update Todo
    ├── Delete Todo
    └── Verify Todo Deleted (404)
```

## 🎯 테스트 시나리오

### 시나리오 1: 서버 상태 확인

```
1. Health Check > Backend Health Check (JSON)
2. Health Check > Web Health Check (Text)
```

### 시나리오 2: 토큰 갱신 및 검증

```
1. Token Management > Refresh Kakao Token
   → KAKAO_ACCESS_TOKEN 자동 저장됨
2. Token Management > Validate Kakao Token
   → 유효성 확인
3. Token Management > Refresh JWT Token (옵션)
```

### 시나리오 3: 소셜 로그인 테스트

```
1. Social Login > Kakao Login
   → JWT_TOKEN, JWT_REFRESH_TOKEN 발급
2. Social Login > Naver Login
```

### 시나리오 4: Todo CRUD 테스트 (순서대로 실행)

```
1. Todo CRUD > Get All Todos
2. Todo CRUD > Create Todo
   → TODO_ID 자동 저장됨
3. Todo CRUD > Get Todo By ID
4. Todo CRUD > Update Todo
5. Todo CRUD > Delete Todo
6. Todo CRUD > Verify Todo Deleted (404)
```

## 💡 자동화 기능

### 🔄 자동 변수 저장

특정 API는 응답 데이터를 자동으로 Environment 변수에 저장합니다:

| API | 자동 저장 변수 |
|-----|---------------|
| **Refresh JWT Token** | `JWT_TOKEN`, `JWT_REFRESH_TOKEN` |
| **Refresh Kakao Token** | `KAKAO_ACCESS_TOKEN` |
| **Refresh Naver Token** | `NAVER_ACCESS_TOKEN` |
| **Create Todo** | `TODO_ID` |

### ✅ 자동 테스트 검증

모든 요청에는 자동 테스트 스크립트가 포함되어 있습니다:

- HTTP 상태 코드 검증
- 응답 데이터 구조 검증
- 필수 필드 존재 여부 확인
- 값 유효성 검증

Console에서 테스트 결과를 실시간으로 확인할 수 있습니다.

## 🏃 전체 테스트 실행

**Collection Runner** 사용:

1. Collection 우클릭 → **Run collection**
2. 실행할 폴더 선택
3. **Run** 버튼 클릭
4. 결과 리포트 확인

## 🆚 pytest vs Postman

| 구분 | pytest | Postman |
|------|--------|---------|
| **목적** | 자동화된 테스트 실행 (CI/CD) | 수동 테스트 및 디버깅 |
| **환경** | Python, CLI | GUI, 시각적 |
| **강점** | 자동화, 통합, 리포트 | 빠른 테스트, 디버깅 용이 |
| **용도** | 정기 테스트, 검증 | 개발 중 API 확인 |

두 도구는 상호 보완적으로 사용됩니다!

## 📌 주의사항

### 보안

- ⚠️ **실제 토큰 값이 포함된 Environment 파일은 Git에 올리지 마세요**
- 현재 `todolist_postman_environment.json`은 템플릿(빈 값)이므로 안전합니다
- `.gitignore`에 `*.postman_environment.local.json` 추가 권장

### 토큰 만료

- Access Token은 일정 시간 후 만료됩니다
- 만료 시 **Token Management** 폴더의 Refresh API로 갱신하세요
- Refresh Token도 만료되면 OAuth 인증을 다시 받아야 합니다

## 🔗 관련 문서

- [Postman 공식 문서](https://learning.postman.com/)
- [프로젝트 메인 README](../README.md)
- [pytest 테스트 코드](../tests/)

## 💬 문의

API 테스트 관련 문의사항은 이슈로 남겨주세요!

