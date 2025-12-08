#!/bin/bash

set -e

echo "========================================"
echo "🔄 CI Token Manager
echo "========================================"

JENKINS_URL="http://3.36.219.242:8080"

# Credential domain 설정 (환경 변수 우선, 없으면 기본값 todolist_dev)
CREDENTIAL_DOMAIN="${CREDENTIAL_DOMAIN:-todolist_dev}"

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
    
    echo "📤 Updating KAKAO_ACCESS_TOKEN credential..."
    # credential 정보 가져오기
    CREDENTIAL_XML=$(curl -s -X GET \
        -u "$JENKINS_USER:$JENKINS_PASS" \
        "$JENKINS_URL/credentials/store/system/domain/${CREDENTIAL_DOMAIN}/credential/KAKAO_ACCESS_TOKEN/config.xml")
    
    # XML에서 secret 값만 업데이트 (Python 사용)
    UPDATED_XML=$(echo "$CREDENTIAL_XML" | $PYTHON_CMD -c "
import sys
import xml.etree.ElementTree as ET
xml_str = sys.stdin.read()
root = ET.fromstring(xml_str)
secret_elem = root.find('secret')
if secret_elem is None:
    secret_elem = ET.SubElement(root, 'secret')
secret_elem.text = sys.argv[1]
print(ET.tostring(root, encoding='unicode'))
" "$KAKAO_ACCESS")
    
    # credential 업데이트
    HTTP_CODE=$(curl -s -w "%{http_code}" -o /tmp/curl_response.txt -X POST \
        -u "$JENKINS_USER:$JENKINS_PASS" \
        -H "Content-Type: application/xml" \
        -d "$UPDATED_XML" \
        "$JENKINS_URL/credentials/store/system/domain/${CREDENTIAL_DOMAIN}/credential/KAKAO_ACCESS_TOKEN/config.xml")
    
    if [ "$HTTP_CODE" != "200" ] && [ "$HTTP_CODE" != "201" ] && [ "$HTTP_CODE" != "302" ]; then
        echo "❌ Failed to update KAKAO_ACCESS_TOKEN (HTTP $HTTP_CODE)"
        cat /tmp/curl_response.txt
        exit 1
    fi
    
    echo "📤 Updating KAKAO_REFRESH_TOKEN credential..."
    # credential 정보 가져오기
    CREDENTIAL_XML=$(curl -s -X GET \
        -u "$JENKINS_USER:$JENKINS_PASS" \
        "$JENKINS_URL/credentials/store/system/domain/${CREDENTIAL_DOMAIN}/credential/KAKAO_REFRESH_TOKEN/config.xml")
    
    # XML에서 secret 값만 업데이트
    UPDATED_XML=$(echo "$CREDENTIAL_XML" | $PYTHON_CMD -c "
import sys
import xml.etree.ElementTree as ET
xml_str = sys.stdin.read()
root = ET.fromstring(xml_str)
secret_elem = root.find('secret')
if secret_elem is None:
    secret_elem = ET.SubElement(root, 'secret')
secret_elem.text = sys.argv[1]
print(ET.tostring(root, encoding='unicode'))
" "$KAKAO_REFRESH")
    
    # credential 업데이트
    HTTP_CODE=$(curl -s -w "%{http_code}" -o /tmp/curl_response.txt -X POST \
        -u "$JENKINS_USER:$JENKINS_PASS" \
        -H "Content-Type: application/xml" \
        -d "$UPDATED_XML" \
        "$JENKINS_URL/credentials/store/system/domain/${CREDENTIAL_DOMAIN}/credential/KAKAO_REFRESH_TOKEN/config.xml")
    
    if [ "$HTTP_CODE" != "200" ] && [ "$HTTP_CODE" != "201" ] && [ "$HTTP_CODE" != "302" ]; then
        echo "❌ Failed to update KAKAO_REFRESH_TOKEN (HTTP $HTTP_CODE)"
        cat /tmp/curl_response.txt
        exit 1
    fi
    
    echo "✅ Kakao tokens refreshed and updated"
fi



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
    
    echo "📤 Updating NAVER_ACCESS_TOKEN credential..."
    # credential 정보 가져오기
    CREDENTIAL_XML=$(curl -s -X GET \
        -u "$JENKINS_USER:$JENKINS_PASS" \
        "$JENKINS_URL/credentials/store/system/domain/${CREDENTIAL_DOMAIN}/credential/NAVER_ACCESS_TOKEN/config.xml")
    
    # XML에서 secret 값만 업데이트
    UPDATED_XML=$(echo "$CREDENTIAL_XML" | $PYTHON_CMD -c "
import sys
import xml.etree.ElementTree as ET
xml_str = sys.stdin.read()
root = ET.fromstring(xml_str)
secret_elem = root.find('secret')
if secret_elem is None:
    secret_elem = ET.SubElement(root, 'secret')
secret_elem.text = sys.argv[1]
print(ET.tostring(root, encoding='unicode'))
" "$NAVER_ACCESS")
    
    # credential 업데이트
    HTTP_CODE=$(curl -s -w "%{http_code}" -o /tmp/curl_response.txt -X POST \
        -u "$JENKINS_USER:$JENKINS_PASS" \
        -H "Content-Type: application/xml" \
        -d "$UPDATED_XML" \
        "$JENKINS_URL/credentials/store/system/domain/${CREDENTIAL_DOMAIN}/credential/NAVER_ACCESS_TOKEN/config.xml")
    
    if [ "$HTTP_CODE" != "200" ] && [ "$HTTP_CODE" != "201" ] && [ "$HTTP_CODE" != "302" ]; then
        echo "❌ Failed to update NAVER_ACCESS_TOKEN (HTTP $HTTP_CODE)"
        cat /tmp/curl_response.txt
        exit 1
    fi
    
    echo "📤 Updating NAVER_REFRESH_TOKEN credential..."
    # credential 정보 가져오기
    CREDENTIAL_XML=$(curl -s -X GET \
        -u "$JENKINS_USER:$JENKINS_PASS" \
        "$JENKINS_URL/credentials/store/system/domain/${CREDENTIAL_DOMAIN}/credential/NAVER_REFRESH_TOKEN/config.xml")
    
    # XML에서 secret 값만 업데이트
    UPDATED_XML=$(echo "$CREDENTIAL_XML" | $PYTHON_CMD -c "
import sys
import xml.etree.ElementTree as ET
xml_str = sys.stdin.read()
root = ET.fromstring(xml_str)
secret_elem = root.find('secret')
if secret_elem is None:
    secret_elem = ET.SubElement(root, 'secret')
secret_elem.text = sys.argv[1]
print(ET.tostring(root, encoding='unicode'))
" "$NAVER_REFRESH")
    
    # credential 업데이트
    HTTP_CODE=$(curl -s -w "%{http_code}" -o /tmp/curl_response.txt -X POST \
        -u "$JENKINS_USER:$JENKINS_PASS" \
        -H "Content-Type: application/xml" \
        -d "$UPDATED_XML" \
        "$JENKINS_URL/credentials/store/system/domain/${CREDENTIAL_DOMAIN}/credential/NAVER_REFRESH_TOKEN/config.xml")
    
    if [ "$HTTP_CODE" != "200" ] && [ "$HTTP_CODE" != "201" ] && [ "$HTTP_CODE" != "302" ]; then
        echo "❌ Failed to update NAVER_REFRESH_TOKEN (HTTP $HTTP_CODE)"
        cat /tmp/curl_response.txt
        exit 1
    fi
    
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
    
    echo "📤 Updating JWT_TOKEN credential..."
    # credential 정보 가져오기
    CREDENTIAL_XML=$(curl -s -X GET \
        -u "$JENKINS_USER:$JENKINS_PASS" \
        "$JENKINS_URL/credentials/store/system/domain/${CREDENTIAL_DOMAIN}/credential/JWT_TOKEN/config.xml")
    
    # XML에서 secret 값만 업데이트
    UPDATED_XML=$(echo "$CREDENTIAL_XML" | $PYTHON_CMD -c "
import sys
import xml.etree.ElementTree as ET
xml_str = sys.stdin.read()
root = ET.fromstring(xml_str)
secret_elem = root.find('secret')
if secret_elem is None:
    secret_elem = ET.SubElement(root, 'secret')
secret_elem.text = sys.argv[1]
print(ET.tostring(root, encoding='unicode'))
" "$JWT_ACCESS")
    
    # credential 업데이트
    HTTP_CODE=$(curl -s -w "%{http_code}" -o /tmp/curl_response.txt -X POST \
        -u "$JENKINS_USER:$JENKINS_PASS" \
        -H "Content-Type: application/xml" \
        -d "$UPDATED_XML" \
        "$JENKINS_URL/credentials/store/system/domain/${CREDENTIAL_DOMAIN}/credential/JWT_TOKEN/config.xml")
    
    if [ "$HTTP_CODE" != "200" ] && [ "$HTTP_CODE" != "201" ] && [ "$HTTP_CODE" != "302" ]; then
        echo "❌ Failed to update JWT_TOKEN (HTTP $HTTP_CODE)"
        cat /tmp/curl_response.txt
        exit 1
    fi
    
    echo "📤 Updating JWT_REFRESH_TOKEN credential..."
    # credential 정보 가져오기
    CREDENTIAL_XML=$(curl -s -X GET \
        -u "$JENKINS_USER:$JENKINS_PASS" \
        "$JENKINS_URL/credentials/store/system/domain/${CREDENTIAL_DOMAIN}/credential/JWT_REFRESH_TOKEN/config.xml")
    
    # XML에서 secret 값만 업데이트
    UPDATED_XML=$(echo "$CREDENTIAL_XML" | $PYTHON_CMD -c "
import sys
import xml.etree.ElementTree as ET
xml_str = sys.stdin.read()
root = ET.fromstring(xml_str)
secret_elem = root.find('secret')
if secret_elem is None:
    secret_elem = ET.SubElement(root, 'secret')
secret_elem.text = sys.argv[1]
print(ET.tostring(root, encoding='unicode'))
" "$JWT_REFRESH")
    
    # credential 업데이트
    HTTP_CODE=$(curl -s -w "%{http_code}" -o /tmp/curl_response.txt -X POST \
        -u "$JENKINS_USER:$JENKINS_PASS" \
        -H "Content-Type: application/xml" \
        -d "$UPDATED_XML" \
        "$JENKINS_URL/credentials/store/system/domain/${CREDENTIAL_DOMAIN}/credential/JWT_REFRESH_TOKEN/config.xml")
    
    if [ "$HTTP_CODE" != "200" ] && [ "$HTTP_CODE" != "201" ] && [ "$HTTP_CODE" != "302" ]; then
        echo "❌ Failed to update JWT_REFRESH_TOKEN (HTTP $HTTP_CODE)"
        cat /tmp/curl_response.txt
        exit 1
    fi
    
    echo "✅ JWT tokens refreshed and updated"
fi


echo "🟢 Jenkins Credential Update Completed"
exit 0