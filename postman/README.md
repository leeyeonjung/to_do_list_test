# 📮 Postman API Collection

이 폴더는 TodoList API를 Postman에서 테스트할 수 있는 Collection과 Environment 파일을 포함합니다.

---

## 📁 파일 구성

| 파일 | 설명 |
|------|------|
| `todolist_postman_collection.json` | API 요청 모음 및 테스트 스크립트 |
| `todolist_postman_environment.json` | 환경 변수 템플릿 |

---

## 🚀 빠른 시작

### 1) Collection Import
1. Postman 실행 → **Import**
2. `todolist_postman_collection.json` 선택 후 Import

### 2) Environment Import
1. **Import**
2. `todolist_postman_environment.json` 선택 후 Import

### 3) Environment 활성화
우측 상단 환경 드롭다운에서 **TodoList Test Environment** 선택

### 4) 환경 변수 설정
환경 아이콘(👁️) → **Edit** → Current Value 입력 후 **Save**

---

## 🔧 환경 변수 설정 가이드

### 📌 기본 설정

| 변수 | 예시 값 | 설명 |
|------|---------|------|
| `BACKEND_BASE_URL` | `http://localhost:5000` | 백엔드 API 서버 |
| `WEB_BASE_URL` | `http://localhost:3000` | 웹 프론트 URL |
| `TODO_ID` | 자동 설정 | Create Todo 시 저장 |

### Kakao 설정

| 변수 | 설명 |
|------|------|
| `KAKAO_REST_API_KEY` | REST API 키 |
| `KAKAO_ACCESS_TOKEN` | 액세스 토큰 |
| `KAKAO_REFRESH_TOKEN` | 리프레시 토큰 |

### Naver 설정

| 변수 | 설명 |
|------|------|
| `NAVER_CLIENT_ID` | 클라이언트 ID |
| `NAVER_CLIENT_SECRET` | 시크릿 키 |
| `NAVER_ACCESS_TOKEN` | 액세스 토큰 |
| `NAVER_REFRESH_TOKEN` | 리프레시 토큰 |

### JWT 설정

| 변수 | 설명 |
|------|------|
| `JWT_TOKEN` | JWT 토큰 |
| `JWT_REFRESH_TOKEN` | 리프레시 토큰 |

---

## 📂 Collection 구조

```
TodoList API Test Collection
├── Health Check
├── Token Management
├── Social Login
└── Todo CRUD
```

---

## 🎯 테스트 시나리오

### 시나리오 1: 서버 상태 확인
- Backend Health Check  
- Web Health Check  

### 시나리오 2: 토큰 갱신·검증
- Refresh Token  
- Validate Token  

### 시나리오 3: 소셜 로그인
- Kakao Login  
- Naver Login  

### 시나리오 4: Todo CRUD 흐름
- Get All → Create → Get By ID → Update → Delete → Verify Deleted

---

## 💡 자동화 기능

| API | 자동 저장 변수 |
|-----|----------------|
| Refresh JWT Token | `JWT_TOKEN`, `JWT_REFRESH_TOKEN` |
| Refresh Kakao Token | `KAKAO_ACCESS_TOKEN` |
| Refresh Naver Token | `NAVER_ACCESS_TOKEN` |
| Create Todo | `TODO_ID` |

---

## 🏃 Collection Runner 실행
1. Collection 우클릭 → **Run collection**  
2. 원하는 폴더 선택  
3. Run 실행  

---

## 🔗 관련 문서
- 프로젝트 메인 README  
- 테스트 코드 (`tests/`)  

