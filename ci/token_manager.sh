#!/bin/bash

set -e

echo "========================================"
echo "🔄 CI Token Manager (pure bash version)"
echo "========================================"

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


# ============================================================
# 2. 토큰 검증 함수 (공통)
# ============================================================
validate_token() {
  PROVIDER=$1
  ACCESS=$2

  echo "🧪 Validating $PROVIDER access token..."

  RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" \
    -H "Authorization: Bearer $ACCESS" \
    "$BACKEND_BASE_URL/api/auth/$PROVIDER/me")

  if [ "$RESPONSE" = "200" ]; then
    echo "✅ $PROVIDER token VALID"
    return 0
  else
    echo "❌ $PROVIDER token INVALID ($RESPONSE)"
    return 1
  fi
}


# ============================================================
# 3. Refresh 함수
# ============================================================
refresh_token() {
  PROVIDER=$1
  REFRESH=$2

  echo "🔄 Refreshing $PROVIDER token..."

  RESULT=$(curl -s -X POST \
    -H "Content-Type: application/json" \
    -d "{\"refreshToken\":\"$REFRESH\"}" \
    "$BACKEND_BASE_URL/api/auth/$PROVIDER/refresh")

  NEW_ACCESS=$(echo "$RESULT" | jq -r ".accessToken // empty")
  NEW_REFRESH=$(echo "$RESULT" | jq -r ".refreshToken // empty")

  if [ -z "$NEW_ACCESS" ] || [ -z "$NEW_REFRESH" ]; then
    echo "❌ Failed to refresh $PROVIDER token"
    echo "$RESULT"
    return 1
  fi

  echo "👍 $PROVIDER token refreshed!"
  echo "$NEW_ACCESS|$NEW_REFRESH"
}


# ============================================================
# 4. Jenkins Credential 업데이트 함수
# ============================================================
update_credential() {
  ID=$1
  SECRET=$2

  echo "🔐 Updating Jenkins Credential: $ID"

  curl -s -X POST \
    -u "$JENKINS_USER:$JENKINS_PASS" \
    -H "Content-Type: application/json" \
    -d "{
       \"credentials\": {
         \"scope\": \"GLOBAL\",
         \"id\": \"$ID\",
         \"secret\": \"$SECRET\",
         \"\$class\": \"org.jenkinsci.plugins.plaincredentials.impl.StringCredentialsImpl\"
       }
     }" \
    "$JENKINS_URL/credentials/store/system/domain/_/credential/$ID" > /dev/null

  echo "✅ Updated: $ID"
}


# ============================================================
# 5. Kakao 검증 + 갱신
# ============================================================
if ! validate_token "kakao" "$KAKAO_ACCESS_TOKEN"; then
  REFRESH_RESULT=$(refresh_token "kakao" "$KAKAO_REFRESH_TOKEN") || true

  NEW_ACCESS=$(echo "$REFRESH_RESULT" | cut -d '|' -f1)
  NEW_REFRESH=$(echo "$REFRESH_RESULT" | cut -d '|' -f2)

  if [ -n "$NEW_ACCESS" ]; then
    update_credential "KAKAO_ACCESS_TOKEN" "$NEW_ACCESS"
    update_credential "KAKAO_REFRESH_TOKEN" "$NEW_REFRESH"
  fi
fi


# ============================================================
# 6. Naver 검증 + 갱신
# ============================================================
if ! validate_token "naver" "$NAVER_ACCESS_TOKEN"; then
  REFRESH_RESULT=$(refresh_token "naver" "$NAVER_REFRESH_TOKEN") || true

  NEW_ACCESS=$(echo "$REFRESH_RESULT" | cut -d '|' -f1)
  NEW_REFRESH=$(echo "$REFRESH_RESULT" | cut -d '|' -f2)

  if [ -n "$NEW_ACCESS" ]; then
    update_credential "NAVER_ACCESS_TOKEN" "$NEW_ACCESS"
    update_credential "NAVER_REFRESH_TOKEN" "$NEW_REFRESH"
  fi
fi


# ============================================================
# 7. JWT 검증 → 실패 시 Refresh
# ============================================================
echo "🧪 Validating JWT token..."

JWT_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  "$BACKEND_BASE_URL/api/auth/jwt/validate")

if [ "$JWT_STATUS" != "200" ]; then
  echo "❌ JWT invalid → refreshing..."

  JWT_RESULT=$(curl -s -X POST \
    -H "Content-Type: application/json" \
    -d "{\"refreshToken\":\"$JWT_REFRESH_TOKEN\"}" \
    "$BACKEND_BASE_URL/api/auth/jwt/refresh")

  NEW_JWT=$(echo "$JWT_RESULT" | jq -r ".accessToken // empty")
  NEW_JWT_REFRESH=$(echo "$JWT_RESULT" | jq -r ".refreshToken // empty")

  if [ -n "$NEW_JWT" ]; then
    update_credential "JWT_TOKEN" "$NEW_JWT"
    update_credential "JWT_REFRESH_TOKEN" "$NEW_JWT_REFRESH"
  fi
else
  echo "✅ JWT VALID"
fi


echo "========================================"
echo "🎉 All tokens validated & updated"
echo "========================================"
exit 0
