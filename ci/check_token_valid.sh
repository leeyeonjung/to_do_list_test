#!/bin/bash
set -e

echo "=== 0. Python 가상환경 확인 ==="
PYTHON="${WORKSPACE}/venv/bin/python"
if [ ! -f "$PYTHON" ]; then
    echo "❌ Python venv not found"
    exit 1
fi

# 🔥 src 패키지 인식을 위한 PYTHONPATH 설정
export PYTHONPATH="${WORKSPACE}:${PYTHONPATH}"

echo "=== 1. Token Check (NAVER & KAKAO) ==="
RESULT=$($PYTHON src/utils/check_social_token.py || true)
echo "Token Check Result: $RESULT"

if [[ "$RESULT" == "VALID" ]]; then
    echo "🟢 All tokens valid"
    exit 0
fi

echo "🔴 Token INVALID → Refresh required"

echo "=== 1.2 Load Jenkins Credentials → ENV → Local ==="
BASE_ENV_FILE="$ENV_FILE"

# ENV 파서
get_from_env() {
    grep "^$1=" "$BASE_ENV_FILE" | cut -d '=' -f2- | sed 's/^"//;s/"$//'
}

# Token 로드
KAKAO_ACCESS_TOKEN="${KAKAO_ACCESS_TOKEN:-$(get_from_env KAKAO_ACCESS_TOKEN)}"
KAKAO_REFRESH_TOKEN="${KAKAO_REFRESH_TOKEN:-$(get_from_env KAKAO_REFRESH_TOKEN)}"
NAVER_ACCESS_TOKEN="${NAVER_ACCESS_TOKEN:-$(get_from_env NAVER_ACCESS_TOKEN)}"
NAVER_REFRESH_TOKEN="${NAVER_REFRESH_TOKEN:-$(get_from_env NAVER_REFRESH_TOKEN)}"

# Load BACKEND_BASE_URL
BACKEND_BASE_URL_RAW="$(grep -E '^[[:space:]]*BACKEND_BASE_URL=' "$ENV_FILE" | sed 's/^[[:space:]]*//')"
BACKEND_BASE_URL="${BACKEND_BASE_URL_RAW#BACKEND_BASE_URL=}"

# Normalize (remove quotes, CR, LF, whitespace)
BACKEND_BASE_URL="$(echo "$BACKEND_BASE_URL" \
    | sed 's/^"//;s/"$//' \
    | tr -d '\r' \
    | tr -d '\n' \
    | tr -d ' ')"

echo "Normalized BACKEND_BASE_URL: '$BACKEND_BASE_URL'"

echo "=== 1.5 Creating temporary ENV_FILE ==="
TMP_ENV=$(mktemp /tmp/env.XXXXXX)

cat <<EOF > "$TMP_ENV"
BACKEND_BASE_URL=${BACKEND_BASE_URL}
KAKAO_ACCESS_TOKEN=${KAKAO_ACCESS_TOKEN}
KAKAO_REFRESH_TOKEN=${KAKAO_REFRESH_TOKEN}
NAVER_ACCESS_TOKEN=${NAVER_ACCESS_TOKEN}
NAVER_REFRESH_TOKEN=${NAVER_REFRESH_TOKEN}
EOF

export ENV_FILE="$TMP_ENV"

echo "=== 2. Refreshing Tokens ==="

# KAKAO
$PYTHON src/utils/token_validator.py \
    --provider kakao \
    --backend-base-url "$BACKEND_BASE_URL" \
    --env-path "$ENV_FILE" || true

# NAVER
$PYTHON src/utils/token_validator.py \
    --provider naver \
    --backend-base-url "$BACKEND_BASE_URL" \
    --env-path "$ENV_FILE" || true

echo "=== 3. Reading Updated Tokens ==="
get_tmp() {
    grep "^$1=" "$ENV_FILE" | cut -d '=' -f2-
}

KAKAO_ACCESS_TOKEN_NEW=$(get_tmp KAKAO_ACCESS_TOKEN)
KAKAO_REFRESH_TOKEN_NEW=$(get_tmp KAKAO_REFRESH_TOKEN)
NAVER_ACCESS_TOKEN_NEW=$(get_tmp NAVER_ACCESS_TOKEN)
NAVER_REFRESH_TOKEN_NEW=$(get_tmp NAVER_REFRESH_TOKEN)

echo "=== 4. Updating Jenkins Credentials ==="

# 🔥 Jenkins Credential API: updateSubmit 사용
update_cred() {
    local id="$1"
    local val="$2"

    if [ -n "$val" ]; then
        curl -X POST \
            -u "$JENKINS_USER:$JENKINS_PASS" \
            -H "Content-Type: application/json" \
            -d "{\"credentials\": {\"scope\":\"GLOBAL\",\"id\":\"${id}\",\"secret\":\"${val}\",\"description\":\"Updated from Jenkins job\",\"$class\": \"org.jenkinsci.plugins.plaincredentials.impl.StringCredentialsImpl\"}}" \
            "$JENKINS_URL/credentials/store/system/domain/todolist_dev/credential/${id}/updateSubmit" -s -f || true
    fi
}

update_cred "KAKAO_ACCESS_TOKEN" "$KAKAO_ACCESS_TOKEN_NEW"
update_cred "KAKAO_REFRESH_TOKEN" "$KAKAO_REFRESH_TOKEN_NEW"
update_cred "NAVER_ACCESS_TOKEN"  "$NAVER_ACCESS_TOKEN_NEW"
update_cred "NAVER_REFRESH_TOKEN" "$NAVER_REFRESH_TOKEN_NEW"

echo "✅ Token refresh complete"
