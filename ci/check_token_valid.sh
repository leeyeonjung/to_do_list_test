#!/bin/bash
set -e

# ========================================
# 0. 기본 환경 설정
# ========================================

WORKSPACE_DIR="${WORKSPACE:-$(pwd)}"
PYTHON="${WORKSPACE_DIR}/venv/bin/python"

echo "=== 0. Python 가상환경 확인 ==="
if [ ! -f "$PYTHON" ]; then
    echo "❌ Python 가상환경이 없습니다. Jenkinsfile에서 venv 생성 단계를 먼저 실행하세요."
    exit 1
fi

# Python 모듈 경로
export PYTHONPATH="${WORKSPACE_DIR}:${PYTHONPATH}"


# ========================================
# 1. 현재 토큰 상태 확인 (Kakao + Naver)
# ========================================

echo "=== 1. Token Check (NAVER & KAKAO) ==="

RESULT=$($PYTHON "${WORKSPACE_DIR}/src/utils/check_social_token.py")
echo "Token Check Result: $RESULT"

if [[ "$RESULT" == "VALID" ]]; then
    echo "🟢 All tokens valid"
    exit 0
fi

echo "🔴 Token INVALID → Refresh required"


# ========================================
# 1.2 우선순위 기반 환경 변수 로딩
# ========================================
# Jenkins Credential → ENV_FILE → 로컬 .env 순

echo "=== 1.2 Load Jenkins Credentials → ENV → Local ==="

# Jenkins Credential 최우선
J_BACKEND_URL="${BACKEND_BASE_URL}"
J_KAKAO_ACCESS="${KAKAO_ACCESS_TOKEN}"
J_KAKAO_REFRESH="${KAKAO_REFRESH_TOKEN}"
J_NAVER_ACCESS="${NAVER_ACCESS_TOKEN}"
J_NAVER_REFRESH="${NAVER_REFRESH_TOKEN}"

# ENV_FILE 기본 경로 (Jenkins secretFile 또는 로컬 .env)
BASE_ENV_FILE="${ENV_FILE:-${WORKSPACE_DIR}/.env}"

echo "ENV FILE LOAD PATH: $BASE_ENV_FILE"

# 로컬 .env 로딩 보조 함수
get_from_envfile() {
    local key="$1"
    if [ -f "$BASE_ENV_FILE" ]; then
        grep "^${key}=" "$BASE_ENV_FILE" | cut -d '=' -f2- | sed 's/^"//;s/"$//'
    fi
}

# 값 채우기 (우선순위 적용)
KAKAO_ACCESS_TOKEN="${J_KAKAO_ACCESS:-$(get_from_envfile KAKAO_ACCESS_TOKEN)}"
KAKAO_REFRESH_TOKEN="${J_KAKAO_REFRESH:-$(get_from_envfile KAKAO_REFRESH_TOKEN)}"
NAVER_ACCESS_TOKEN="${J_NAVER_ACCESS:-$(get_from_envfile NAVER_ACCESS_TOKEN)}"
NAVER_REFRESH_TOKEN="${J_NAVER_REFRESH:-$(get_from_envfile NAVER_REFRESH_TOKEN)}"

if [ -z "$BACKEND_BASE_URL" ]; then
    BACKEND_BASE_URL="$(grep '^BACKEND_BASE_URL=' "$ENV_FILE" | cut -d '=' -f2- | sed 's/^"//;s/"$//')"
fi

export BACKEND_BASE_URL
echo "Loaded BACKEND_BASE_URL: $BACKEND_BASE_URL"

export KAKAO_ACCESS_TOKEN
export KAKAO_REFRESH_TOKEN
export NAVER_ACCESS_TOKEN
export NAVER_REFRESH_TOKEN

echo "Loaded BACKEND_BASE_URL: $BACKEND_BASE_URL"


# ========================================
# 1.5 임시 ENV_FILE 생성 (validator가 읽을 값)
# ========================================

WORKING_ENV_FILE="$(mktemp /tmp/env.XXXXXX)"
echo "=== 1.5 Creating temporary ENV_FILE: $WORKING_ENV_FILE ==="

{
    echo "BACKEND_BASE_URL=${BACKEND_BASE_URL}"
    echo "KAKAO_ACCESS_TOKEN=${KAKAO_ACCESS_TOKEN}"
    echo "KAKAO_REFRESH_TOKEN=${KAKAO_REFRESH_TOKEN}"
    echo "NAVER_ACCESS_TOKEN=${NAVER_ACCESS_TOKEN}"
    echo "NAVER_REFRESH_TOKEN=${NAVER_REFRESH_TOKEN}"
} > "$WORKING_ENV_FILE"

export ENV_FILE="$WORKING_ENV_FILE"


# ========================================
# 2. Token Refresh 실행
# ========================================

echo "=== 2. Refreshing Tokens ==="

for provider in "kakao" "naver"; do
    echo "🔄 Refreshing ${provider}..."
    
    # validate & refresh endpoints 자동 구성
    VALIDATE_EP="/api/auth/${provider}"
    REFRESH_EP="/api/auth/${provider}/refresh"

    $PYTHON "${WORKSPACE_DIR}/src/utils/token_validator.py" \
        --provider "${provider}" \
        --backend-base-url "${BACKEND_BASE_URL}" \
        --env-path "${ENV_FILE}" \
        --validate-endpoint "${VALIDATE_EP}" \
        --refresh-endpoint "${REFRESH_EP}" \
        || true
done


# ========================================
# 3. 갱신된 토큰 읽기
# ========================================

echo "=== 3. Reading Updated Tokens ==="

get_env_value() {
    local key="$1"
    grep "^${key}=" "$ENV_FILE" | cut -d '=' -f2- | sed 's/^"//;s/"$//'
}

KAKAO_ACCESS_TOKEN_NEW=$(get_env_value "KAKAO_ACCESS_TOKEN")
KAKAO_REFRESH_TOKEN_NEW=$(get_env_value "KAKAO_REFRESH_TOKEN")
NAVER_ACCESS_TOKEN_NEW=$(get_env_value "NAVER_ACCESS_TOKEN")
NAVER_REFRESH_TOKEN_NEW=$(get_env_value "NAVER_REFRESH_TOKEN")


# fallback (값 없으면 기존 유지)
KAKAO_ACCESS_TOKEN="${KAKAO_ACCESS_TOKEN_NEW:-$KAKAO_ACCESS_TOKEN}"
KAKAO_REFRESH_TOKEN="${KAKAO_REFRESH_TOKEN_NEW:-$KAKAO_REFRESH_TOKEN}"
NAVER_ACCESS_TOKEN="${NAVER_ACCESS_TOKEN_NEW:-$NAVER_ACCESS_TOKEN}"
NAVER_REFRESH_TOKEN="${NAVER_REFRESH_TOKEN_NEW:-$NAVER_REFRESH_TOKEN}"


# ========================================
# 4. Jenkins Credential 업데이트
# ========================================

echo "=== 4. Updating Jenkins Credentials ==="

update_cred() {
    local id="$1"
    local val="$2"

    if [ -z "$val" ]; then
        echo "⚠️  Skip updating $id (empty value)"
        return
    fi

    curl -X POST \
        -u "${JENKINS_USER}:${JENKINS_PASS}" \
        -H "Content-Type: application/json" \
        -d "{\"credentials\":{\"scope\":\"GLOBAL\",\"id\":\"${id}\",\"secret\":\"${val}\",\"\\\$class\":\"org.jenkinsci.plugins.plaincredentials.impl.StringCredentialsImpl\"}}" \
        "${JENKINS_URL}/credentials/store/system/domain/todolist_dev/credential/${id}/update" \
        -f -s -o /dev/null \
        && echo "✅ Updated: $id" \
        || echo "❌ Failed: $id"
}

update_cred "KAKAO_ACCESS_TOKEN" "$KAKAO_ACCESS_TOKEN"
update_cred "KAKAO_REFRESH_TOKEN" "$KAKAO_REFRESH_TOKEN"
update_cred "NAVER_ACCESS_TOKEN" "$NAVER_ACCESS_TOKEN"
update_cred "NAVER_REFRESH_TOKEN" "$NAVER_REFRESH_TOKEN"

echo "✅ Jenkins credential update completed"


# ========================================
# 5. Cleanup
# ========================================

rm -f "$WORKING_ENV_FILE"

echo "✅ Token refresh complete"
exit 0
