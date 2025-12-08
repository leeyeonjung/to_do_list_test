#!/bin/bash
set -e

echo "=== 0. Python venv 확인 ==="
PYTHON="${WORKSPACE}/venv/bin/python"
if [ ! -f "$PYTHON" ]; then
    echo "❌ Python venv not found"
    exit 1
fi

export PYTHONPATH="${WORKSPACE}:${PYTHONPATH}"

echo "=== 1. Token Check (NAVER & KAKAO) ==="
RESULT=$($PYTHON src/utils/check_social_token.py || true)
echo "Token Check Result: $RESULT"

if [[ "$RESULT" == "VALID" ]]; then
    echo "🟢 All tokens valid"
    exit 0
fi

echo "🔴 Token INVALID → Refresh required"

echo "=== 1. Load Credentials (ENV_FILE는 기본값만) ==="
BASE_ENV_FILE="$ENV_FILE"

get_from_env() {
    grep "^$1=" "$BASE_ENV_FILE" | cut -d '=' -f2- | sed 's/^"//;s/"$//'
}

# Jenkins credentials가 항상 우선!!!
KAKAO_ACCESS_TOKEN="${KAKAO_ACCESS_TOKEN}"
KAKAO_REFRESH_TOKEN="${KAKAO_REFRESH_TOKEN}"
NAVER_ACCESS_TOKEN="${NAVER_ACCESS_TOKEN}"
NAVER_REFRESH_TOKEN="${NAVER_REFRESH_TOKEN}"

# BACKEND URL만 ENV에서 읽음
BACKEND_BASE_URL="$(grep -E '^BACKEND_BASE_URL=' "$ENV_FILE" | cut -d '=' -f2- | tr -d '"')"

echo "BACKEND_BASE_URL = $BACKEND_BASE_URL"

TMP_ENV=$(mktemp /tmp/env.XXXXXX)
cat <<EOF > "$TMP_ENV"
BACKEND_BASE_URL=${BACKEND_BASE_URL}
KAKAO_ACCESS_TOKEN=${KAKAO_ACCESS_TOKEN}
KAKAO_REFRESH_TOKEN=${KAKAO_REFRESH_TOKEN}
NAVER_ACCESS_TOKEN=${NAVER_ACCESS_TOKEN}
NAVER_REFRESH_TOKEN=${NAVER_REFRESH_TOKEN}
EOF

export ENV_FILE="$TMP_ENV"

echo "=== 2. Refresh Tokens ==="

$PYTHON src/utils/token_validator.py --provider kakao \
    --backend-base-url "$BACKEND_BASE_URL" \
    --env-path "$ENV_FILE" || true

$PYTHON src/utils/token_validator.py --provider naver \
    --backend-base-url "$BACKEND_BASE_URL" \
    --env-path "$ENV_FILE" || true


echo "=== 3. Read Updated Tokens ==="
get_tmp() {
    grep "^$1=" "$ENV_FILE" | cut -d '=' -f2-
}

NEW_KAKAO_ACCESS=$(get_tmp KAKAO_ACCESS_TOKEN)
NEW_KAKAO_REFRESH=$(get_tmp KAKAO_REFRESH_TOKEN)
NEW_NAVER_ACCESS=$(get_tmp NAVER_ACCESS_TOKEN)
NEW_NAVER_REFRESH=$(get_tmp NAVER_REFRESH_TOKEN)

echo "=== 4. Update Jenkins Credentials ==="

update_cred() {
    local id="$1"
    local value="$2"

    if [ -z "$value" ]; then
        echo "⚠️ $id new value empty → skip"
        return
    fi

    curl -X POST \
        -u "$JENKINS_USER:$JENKINS_PASS" \
        -H "Content-Type: application/json" \
        -d "{\"credentials\":{\"scope\":\"GLOBAL\",\"id\":\"${id}\",\"secret\":\"${value}\",\"$class\":\"org.jenkinsci.plugins.plaincredentials.impl.StringCredentialsImpl\"}}" \
        "$JENKINS_URL/credentials/store/system/domain/todolist_dev/credential/${id}/submitUpdate" \
        -s -f || true
}

update_cred "KAKAO_ACCESS_TOKEN" "$NEW_KAKAO_ACCESS"
update_cred "KAKAO_REFRESH_TOKEN" "$NEW_KAKAO_REFRESH"
update_cred "NAVER_ACCESS_TOKEN" "$NEW_NAVER_ACCESS"
update_cred "NAVER_REFRESH_TOKEN" "$NEW_NAVER_REFRESH"

echo "✅ Token refresh complete"
