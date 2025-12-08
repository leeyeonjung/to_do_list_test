#!/bin/bash

set -e

echo "========================================"
echo "🔄 CI Token Manager (pure bash version)"
echo "========================================"

JENKINS_URL="http://3.36.219.242:8080"

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

KAKAO_RESULT=$(python3 src/utils/token_validator.py validate_oauth_token "$BACKEND_BASE_URL" "$KAKAO_ACCESS_TOKEN" "/api/auth/kakao")
echo "🔍 KAKAO_RESULT = $KAKAO_RESULT"
if [[ "$KAKAO_RESULT" == "True" ]]; then
    echo "🟢 Token is VALID"
    exit 0
else
    echo "🔴 Kakao Token is INVALID"
    REFRESH_KAKAO_RESULT=$(python3 src/utils/token_validator.py refresh_oauth_token "$BACKEND_BASE_URL" "$KAKAO_REFRESH_TOKEN" "/api/auth/kakao/refresh")
    KAKAO_ACCESS=$(jq -r '.access_token' token.json)
    KAKAO_REFRESH=$(jq -r '.refresh_token' token.json)  
    exit 1
fi

curl -X POST \
    -u "$USER:$PASS" \
    -H "Content-Type: application/json" \
    -d "{ \"credentials\":{\"scope\":\"GLOBAL\", \"id\":\"api_access_token\", \"secret\":\"$KAKAO_ACCESS\", \"\\$class\":\"org.jenkinsci.plugins.plaincredentials.impl.StringCredentialsImpl\"} }" \
    "$JENKINS_URL/credentials/store/system/domain/_/credential/api_access_token"

curl -X POST \
    -u "$USER:$PASS" \
    -H "Content-Type: application/json" \
    -d "{ \"credentials\":{\"scope\":\"GLOBAL\", \"id\":\"api_refresh_token\", \"secret\":\"$KAKAO_REFRESH\", \"\\$class\":\"org.jenkinsci.plugins.plaincredentials.impl.StringCredentialsImpl\"} }" \
    "$JENKINS_URL/credentials/store/system/domain/_/credential/api_refresh_token"



NAVER_RESULT=$(python3 src/utils/token_validator.py validate_oauth_token "$BACKEND_BASE_URL" "$NAVER_ACCESS_TOKEN" "/api/auth/naver")
echo "🔍NAVER_RESULT = $NAVER_RESULT"
if [[ "$NAVER_RESULT" == "True" ]]; then
    echo "🟢 Naver Token is VALID"
    exit 0
else
    echo "🔴 Naver Token is INVALID"
    REFRESH_NAVER_RESULT=$(python3 src/utils/token_validator.py refresh_oauth_token "$BACKEND_BASE_URL" "$NAVER_REFRESH_TOKEN" "/api/auth/naver/refresh")
    NAVER_ACCESS=$(jq -r '.access_token' token.json)
    NAVER_REFRESH=$(jq -r '.refresh_token' token.json)  
    exit 1
fi

curl -X POST \
    -u "$USER:$PASS" \
    -H "Content-Type: application/json" \
    -d "{ \"credentials\":{\"scope\":\"GLOBAL\", \"id\":\"api_access_token\", \"secret\":\"$NAVER_ACCESS\", \"\\$class\":\"org.jenkinsci.plugins.plaincredentials.impl.StringCredentialsImpl\"} }" \
    "$JENKINS_URL/credentials/store/system/domain/_/credential/api_access_token"

curl -X POST \
    -u "$USER:$PASS" \
    -H "Content-Type: application/json" \
    -d "{ \"credentials\":{\"scope\":\"GLOBAL\", \"id\":\"api_refresh_token\", \"secret\":\"$NAVER_REFRESH\", \"\\$class\":\"org.jenkinsci.plugins.plaincredentials.impl.StringCredentialsImpl\"} }" \
    "$JENKINS_URL/credentials/store/system/domain/_/credential/api_refresh_token"


JWT_RESULT=$(python3 src/utils/token_validator.py validate_jwt_token "$BACKEND_BASE_URL" "$JWT_TOKEN" "/api/auth/jwt")
echo "🔍JWT_RESULT = $JWT_RESULT"
if [[ "$JWT_RESULT" == "True" ]]; then
    echo "🟢 JWT Token is VALID"
    exit 0
else
    echo "🔴 JWT Token is INVALID"
    REFRESH_JWT_RESULT=$(python3 src/utils/token_validator.py refresh_jwt_token "$BACKEND_BASE_URL" "$JWT_REFRESH_TOKEN" "/api/auth/jwt/refresh")
    JWT_ACCESS=$(jq -r '.access_token' token.json)
    JWT_REFRESH=$(jq -r '.refresh_token' token.json)  
    exit 1
fi

curl -X POST \
    -u "$USER:$PASS" \
    -H "Content-Type: application/json" \
    -d "{ \"credentials\":{\"scope\":\"GLOBAL\", \"id\":\"api_access_token\", \"secret\":\"$NAVER_ACCESS\", \"\\$class\":\"org.jenkinsci.plugins.plaincredentials.impl.StringCredentialsImpl\"} }" \
    "$JENKINS_URL/credentials/store/system/domain/_/credential/api_access_token"

curl -X POST \
    -u "$USER:$PASS" \
    -H "Content-Type: application/json" \
    -d "{ \"credentials\":{\"scope\":\"GLOBAL\", \"id\":\"api_refresh_token\", \"secret\":\"$NAVER_REFRESH\", \"\\$class\":\"org.jenkinsci.plugins.plaincredentials.impl.StringCredentialsImpl\"} }" \
    "$JENKINS_URL/credentials/store/system/domain/_/credential/api_refresh_token"


echo "🟢 Jenkins Credential Update Completed"
exit 0