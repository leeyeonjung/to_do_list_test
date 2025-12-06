#!/bin/bash
set -e

# Jenkins workspace 경로 (Jenkinsfile에서 설정된 WORKSPACE_DIR 사용)
WORKSPACE_DIR="${WORKSPACE:-$(pwd)}"
PYTHON="${WORKSPACE_DIR}/venv/bin/python"

echo "=== 0. Python 가상환경 확인 ==="
if [ ! -f "$PYTHON" ]; then
    echo "❌ Python 가상환경이 없습니다. Jenkinsfile의 Setup 단계를 먼저 실행하세요."
    exit 1
fi

echo "=== 1. Token Check (NAVER & KAKAO) ==="
RESULT=$($PYTHON "${WORKSPACE_DIR}/src/utils/check_social_token.py")

echo "Token Check Result: $RESULT"

if [[ "$RESULT" == "VALID" ]]; then
    echo "🟢 All tokens (NAVER & KAKAO) are VALID"
    exit 0
fi

echo "🔴 Token INVALID → Refreshing tokens and updating Jenkins credentials..."

# 환경 변수 설정
export BACKEND_BASE_URL="${BACKEND_BASE_URL:-http://localhost:5000}"
JENKINS_URL="${JENKINS_URL:-http://localhost:8080}"
JENKINS_USER="${JENKINS_USER}"
JENKINS_PASS="${JENKINS_PASS}"
JENKINS_DOMAIN="${JENKINS_DOMAIN:-todolist_dev}"

# ENV_FILE 확인 (Jenkinsfile에서 주입되는 .env-dev-test 같은 파일)
ENV_FILE="${ENV_FILE:-${WORKSPACE_DIR}/.env}"
if [ ! -f "$ENV_FILE" ]; then
    echo "⚠️  ENV_FILE not found: $ENV_FILE"
    echo "   Using environment variables directly"
    ENV_FILE=""
fi

# 네이버와 카카오 토큰 갱신
echo "=== 2. Refreshing Tokens ==="
for provider in "naver" "kakao"; do
    echo "🔄 Refreshing ${provider} token..."
    if [ -n "$ENV_FILE" ]; then
        $PYTHON "${WORKSPACE_DIR}/src/utils/token_validator.py" \
            --provider "${provider}" \
            --backend-base-url "${BACKEND_BASE_URL}" \
            --env-path "${ENV_FILE}" || true
    else
        $PYTHON "${WORKSPACE_DIR}/src/utils/token_validator.py" \
            --provider "${provider}" \
            --backend-base-url "${BACKEND_BASE_URL}" || true
    fi
done

# 갱신된 토큰 읽기
echo "=== 3. Reading Updated Tokens ==="
if [ -n "$ENV_FILE" ] && [ -f "$ENV_FILE" ]; then
    # ENV_FILE에서 토큰 값 추출 함수
    get_env_value() {
        local key=$1
        grep "^${key}=" "$ENV_FILE" | cut -d '=' -f2- | sed 's/^"//;s/"$//' | head -1
    }
    
    KAKAO_ACCESS_TOKEN_NEW=$(get_env_value "KAKAO_ACCESS_TOKEN")
    KAKAO_REFRESH_TOKEN_NEW=$(get_env_value "KAKAO_REFRESH_TOKEN")
    NAVER_ACCESS_TOKEN_NEW=$(get_env_value "NAVER_ACCESS_TOKEN")
    NAVER_REFRESH_TOKEN_NEW=$(get_env_value "NAVER_REFRESH_TOKEN")
    
    # ENV_FILE에서 읽은 값이 있으면 사용, 없으면 환경 변수 사용
    KAKAO_ACCESS_TOKEN="${KAKAO_ACCESS_TOKEN_NEW:-${KAKAO_ACCESS_TOKEN}}"
    KAKAO_REFRESH_TOKEN="${KAKAO_REFRESH_TOKEN_NEW:-${KAKAO_REFRESH_TOKEN}}"
    NAVER_ACCESS_TOKEN="${NAVER_ACCESS_TOKEN_NEW:-${NAVER_ACCESS_TOKEN}}"
    NAVER_REFRESH_TOKEN="${NAVER_REFRESH_TOKEN_NEW:-${NAVER_REFRESH_TOKEN}}"
else
    # ENV_FILE이 없으면 환경 변수에서 직접 사용 (이미 Jenkinsfile에서 export됨)
    echo "   Using tokens from environment variables"
fi

# Jenkins credential 업데이트 함수
update_jenkins_credential() {
    local credential_id=$1
    local secret=$2
    
    if [ -z "$secret" ]; then
        return 0
    fi
    
    curl -X POST \
        -u "${JENKINS_USER}:${JENKINS_PASS}" \
        -H "Content-Type: application/json" \
        -d "{\"credentials\":{\"scope\":\"GLOBAL\",\"id\":\"${credential_id}\",\"secret\":\"${secret}\",\"\\\$class\":\"org.jenkinsci.plugins.plaincredentials.impl.StringCredentialsImpl\"}}" \
        "${JENKINS_URL}/credentials/store/system/domain/${JENKINS_DOMAIN}/credential/${credential_id}/update" \
        -f -s -o /dev/null && echo "✅ ${credential_id} updated" || echo "⚠️  ${credential_id} update failed"
}

# Jenkins credentials 업데이트
if [ -n "$JENKINS_USER" ] && [ -n "$JENKINS_PASS" ]; then
    echo "=== 4. Updating Jenkins Credentials ==="
    
    update_jenkins_credential "KAKAO_ACCESS_TOKEN" "$KAKAO_ACCESS_TOKEN"
    update_jenkins_credential "KAKAO_REFRESH_TOKEN" "$KAKAO_REFRESH_TOKEN"
    update_jenkins_credential "NAVER_ACCESS_TOKEN" "$NAVER_ACCESS_TOKEN"
    update_jenkins_credential "NAVER_REFRESH_TOKEN" "$NAVER_REFRESH_TOKEN"
    
    echo "✅ Jenkins credentials update completed"
else
    echo "⚠️  Jenkins credentials not updated (JENKINS_USER or JENKINS_PASS not set)"
fi

echo "✅ Token refresh process completed"
exit 0
