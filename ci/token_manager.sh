#!/bin/bash

set -e

echo "========================================"
echo "🔄 CI Token Manager (pure bash version)"
echo "========================================"

JENKINS_URL="http://3.36.219.242:8080"

# Python 실행 경로 설정 (가상환경 우선, 없으면 시스템 python3)
if [ -n "$PYTHON" ] && [ -f "$PYTHON" ]; then
    PYTHON_CMD="$PYTHON"
elif [ -n "$VENV_PATH" ] && [ -f "$VENV_PATH/bin/python3" ]; then
    PYTHON_CMD="$VENV_PATH/bin/python3"
elif [ -f "venv/bin/python3" ]; then
    PYTHON_CMD="venv/bin/python3"
else
    PYTHON_CMD="python3"
fi

echo "[DEBUG] Using Python: $PYTHON_CMD"

# --- 0. ENV_FILE 검증 ------------------------------------
if [ -z "$ENV_FILE" ] || [ ! -f "$ENV_FILE" ]; then
  echo "❌ ENV_FILE not found: $ENV_FILE"
  exit 1
fi

# --- 1. BACKEND_BASE_URL 추출 ----------------------------
BACKEND_BASE_URL="$(
  grep -E '^BACKEND_BASE_URL=' "$ENV_FILE" | cut -d '=' -f2- \
    | sed 's/^"//;s/"$//' \
    | tr -d '\r' | tr -d '\n' | tr -d ' '
)"

echo "🌐 BACKEND_BASE_URL = $BACKEND_BASE_URL"

KAKAO_RESULT=$($PYTHON_CMD -c "
import sys
sys.path.insert(0, '.')
from src.utils.token_validator import validate_oauth_token
result = validate_oauth_token('$BACKEND_BASE_URL', '$KAKAO_ACCESS_TOKEN', '/api/auth/kakao')
print('True' if result else 'False')
")
echo "🔍 KAKAO_RESULT = $KAKAO_RESULT"
if [[ "$KAKAO_RESULT" == "True" ]]; then
    echo "🟢 Kakao Token is VALID"
else
    echo "🔴 Kakao Token is INVALID - Refreshing..."
    $PYTHON_CMD -c "
import sys
import json
sys.path.insert(0, '.')
from src.utils.token_validator import refresh_oauth_token
result = refresh_oauth_token('$BACKEND_BASE_URL', '$KAKAO_REFRESH_TOKEN', '/api/auth/kakao/refresh')
if result:
    with open('token.json', 'w') as f:
        json.dump(result, f)
    sys.exit(0)
else:
    sys.exit(1)
" || exit 1
    KAKAO_ACCESS=$(jq -r '.token // .accessToken // .access_token' token.json)
    KAKAO_REFRESH=$(jq -r '.refreshToken // .refresh_token' token.json)
    
    if [ -z "$KAKAO_ACCESS" ] || [ -z "$KAKAO_REFRESH" ]; then
        echo "❌ Failed to extract tokens from refresh response"
        exit 1
    fi
    
    curl -s -X POST \
        -u "$JENKINS_USER:$JENKINS_PASS" \
        -H "Content-Type: application/json" \
        -d "{ \"credentials\":{\"scope\":\"GLOBAL\", \"id\":\"KAKAO_ACCESS_TOKEN\", \"secret\":\"$KAKAO_ACCESS\", \"\\$class\":\"org.jenkinsci.plugins.plaincredentials.impl.StringCredentialsImpl\"} }" \
        "$JENKINS_URL/credentials/store/system/domain/_/credential/KAKAO_ACCESS_TOKEN" > /dev/null
    
    curl -s -X POST \
        -u "$JENKINS_USER:$JENKINS_PASS" \
        -H "Content-Type: application/json" \
        -d "{ \"credentials\":{\"scope\":\"GLOBAL\", \"id\":\"KAKAO_REFRESH_TOKEN\", \"secret\":\"$KAKAO_REFRESH\", \"\\$class\":\"org.jenkinsci.plugins.plaincredentials.impl.StringCredentialsImpl\"} }" \
        "$JENKINS_URL/credentials/store/system/domain/_/credential/KAKAO_REFRESH_TOKEN" > /dev/null
    
    echo "✅ Kakao tokens refreshed and updated"
fi

curl -X POST \
    -u "$USER:$PASS" \
    -H "Content-Type: application/json" \
    -d "{ \"credentials\":{\"scope\":\"GLOBAL\", \"id\":\"api_access_token\", \"secret\":\"$KAKAO_ACCESS\", \"\\$class\":\"org.jenkinsci.plugins.plaincredentials.impl.StringCredentialsImpl\"} }" \
    "$JENKINS_URL/credentials/store/system/domain/todolist_dev/credential/api_access_token"

curl -X POST \
    -u "$USER:$PASS" \
    -H "Content-Type: application/json" \
    -d "{ \"credentials\":{\"scope\":\"GLOBAL\", \"id\":\"api_refresh_token\", \"secret\":\"$KAKAO_REFRESH\", \"\\$class\":\"org.jenkinsci.plugins.plaincredentials.impl.StringCredentialsImpl\"} }" \
    "$JENKINS_URL/credentials/store/system/domain/todolist_dev/credential/api_refresh_token"



NAVER_RESULT=$($PYTHON_CMD -c "
import sys
sys.path.insert(0, '.')
from src.utils.token_validator import validate_oauth_token
result = validate_oauth_token('$BACKEND_BASE_URL', '$NAVER_ACCESS_TOKEN', '/api/auth/naver')
print('True' if result else 'False')
")
echo "🔍 NAVER_RESULT = $NAVER_RESULT"
if [[ "$NAVER_RESULT" == "True" ]]; then
    echo "🟢 Naver Token is VALID"
else
    echo "🔴 Naver Token is INVALID - Refreshing..."
    $PYTHON_CMD -c "
import sys
import json
sys.path.insert(0, '.')
from src.utils.token_validator import refresh_oauth_token
result = refresh_oauth_token('$BACKEND_BASE_URL', '$NAVER_REFRESH_TOKEN', '/api/auth/naver/refresh')
if result:
    with open('token.json', 'w') as f:
        json.dump(result, f)
    sys.exit(0)
else:
    sys.exit(1)
" || exit 1
    NAVER_ACCESS=$(jq -r '.token // .accessToken // .access_token' token.json)
    NAVER_REFRESH=$(jq -r '.refreshToken // .refresh_token' token.json)
    
    if [ -z "$NAVER_ACCESS" ] || [ -z "$NAVER_REFRESH" ]; then
        echo "❌ Failed to extract tokens from refresh response"
        exit 1
    fi
    
    curl -s -X POST \
        -u "$JENKINS_USER:$JENKINS_PASS" \
        -H "Content-Type: application/json" \
        -d "{ \"credentials\":{\"scope\":\"GLOBAL\", \"id\":\"NAVER_ACCESS_TOKEN\", \"secret\":\"$NAVER_ACCESS\", \"\\$class\":\"org.jenkinsci.plugins.plaincredentials.impl.StringCredentialsImpl\"} }" \
        "$JENKINS_URL/credentials/store/system/domain/_/credential/NAVER_ACCESS_TOKEN" > /dev/null
    
    curl -s -X POST \
        -u "$JENKINS_USER:$JENKINS_PASS" \
        -H "Content-Type: application/json" \
        -d "{ \"credentials\":{\"scope\":\"GLOBAL\", \"id\":\"NAVER_REFRESH_TOKEN\", \"secret\":\"$NAVER_REFRESH\", \"\\$class\":\"org.jenkinsci.plugins.plaincredentials.impl.StringCredentialsImpl\"} }" \
        "$JENKINS_URL/credentials/store/system/domain/_/credential/NAVER_REFRESH_TOKEN" > /dev/null
    
    echo "✅ Naver tokens refreshed and updated"
fi


JWT_RESULT=$($PYTHON_CMD -c "
import sys
sys.path.insert(0, '.')
from src.utils.token_validator import validate_jwt_token
result, _ = validate_jwt_token('$BACKEND_BASE_URL', '$JWT_TOKEN', '/api/auth/me')
print('True' if result else 'False')
")
echo "🔍 JWT_RESULT = $JWT_RESULT"
if [[ "$JWT_RESULT" == "True" ]]; then
    echo "🟢 JWT Token is VALID"
else
    echo "🔴 JWT Token is INVALID - Refreshing..."
    $PYTHON_CMD -c "
import sys
import json
sys.path.insert(0, '.')
from src.utils.token_validator import refresh_jwt_token
result = refresh_jwt_token('$BACKEND_BASE_URL', '$JWT_REFRESH_TOKEN', None, '/api/auth/refresh')
if result:
    with open('token.json', 'w') as f:
        json.dump(result, f)
    sys.exit(0)
else:
    sys.exit(1)
" || exit 1
    JWT_ACCESS=$(jq -r '.token // .accessToken // .access_token' token.json)
    JWT_REFRESH=$(jq -r '.refreshToken // .refresh_token' token.json)
    
    if [ -z "$JWT_ACCESS" ] || [ -z "$JWT_REFRESH" ]; then
        echo "❌ Failed to extract tokens from refresh response"
        exit 1
    fi
    
    curl -s -X POST \
        -u "$JENKINS_USER:$JENKINS_PASS" \
        -H "Content-Type: application/json" \
        -d "{ \"credentials\":{\"scope\":\"GLOBAL\", \"id\":\"JWT_TOKEN\", \"secret\":\"$JWT_ACCESS\", \"\\$class\":\"org.jenkinsci.plugins.plaincredentials.impl.StringCredentialsImpl\"} }" \
        "$JENKINS_URL/credentials/store/system/domain/_/credential/JWT_TOKEN" > /dev/null
    
    curl -s -X POST \
        -u "$JENKINS_USER:$JENKINS_PASS" \
        -H "Content-Type: application/json" \
        -d "{ \"credentials\":{\"scope\":\"GLOBAL\", \"id\":\"JWT_REFRESH_TOKEN\", \"secret\":\"$JWT_REFRESH\", \"\\$class\":\"org.jenkinsci.plugins.plaincredentials.impl.StringCredentialsImpl\"} }" \
        "$JENKINS_URL/credentials/store/system/domain/_/credential/JWT_REFRESH_TOKEN" > /dev/null
    
    echo "✅ JWT tokens refreshed and updated"
fi


echo "🟢 Jenkins Credential Update Completed"
exit 0