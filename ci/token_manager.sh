#!/bin/bash

set -e

echo "========================================"
echo "🔄 CI Token Manager"
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

# --- 2. Kakao Token 검증 및 갱신 -------------------------
KAKAO_RESULT=$(BACKEND_BASE_URL="$BACKEND_BASE_URL" KAKAO_ACCESS_TOKEN="$KAKAO_ACCESS_TOKEN" $PYTHON_CMD -c "
import sys
import os
sys.path.insert(0, '.')
from src.utils.token_validator import validate_oauth_token
result = validate_oauth_token(os.environ['BACKEND_BASE_URL'], os.environ['KAKAO_ACCESS_TOKEN'], '/api/auth/kakao')
print('True' if result else 'False')
")
echo "🔍 KAKAO_RESULT = $KAKAO_RESULT"
if [[ "$KAKAO_RESULT" == "True" ]]; then
    echo "🟢 Kakao Token is VALID"
else
    echo "🔴 Kakao Token is INVALID - Refreshing..."
    BACKEND_BASE_URL="$BACKEND_BASE_URL" KAKAO_REFRESH_TOKEN="$KAKAO_REFRESH_TOKEN" $PYTHON_CMD -c "
import sys
import json
import os
sys.path.insert(0, '.')
from src.utils.token_validator import refresh_oauth_token
result = refresh_oauth_token(os.environ['BACKEND_BASE_URL'], os.environ['KAKAO_REFRESH_TOKEN'], '/api/auth/kakao/refresh')
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
    CREDENTIAL_XML=$(curl -s -X GET \
        -u "$JENKINS_USER:$JENKINS_PASS" \
        "$JENKINS_URL/credentials/store/system/domain/${CREDENTIAL_DOMAIN}/credential/KAKAO_ACCESS_TOKEN/config.xml")
    
    UPDATED_XML=$(echo "$CREDENTIAL_XML" | KAKAO_ACCESS="$KAKAO_ACCESS" $PYTHON_CMD -c "
import sys
import xml.etree.ElementTree as ET
import os
xml_str = sys.stdin.read()
root = ET.fromstring(xml_str)
secret_elem = root.find('secret')
if secret_elem is None:
    secret_elem = ET.SubElement(root, 'secret')
secret_elem.text = os.environ['KAKAO_ACCESS']
print(ET.tostring(root, encoding='unicode'))
")
    
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
    CREDENTIAL_XML=$(curl -s -X GET \
        -u "$JENKINS_USER:$JENKINS_PASS" \
        "$JENKINS_URL/credentials/store/system/domain/${CREDENTIAL_DOMAIN}/credential/KAKAO_REFRESH_TOKEN/config.xml")
    
    UPDATED_XML=$(echo "$CREDENTIAL_XML" | KAKAO_REFRESH="$KAKAO_REFRESH" $PYTHON_CMD -c "
import sys
import xml.etree.ElementTree as ET
import os
xml_str = sys.stdin.read()
root = ET.fromstring(xml_str)
secret_elem = root.find('secret')
if secret_elem is None:
    secret_elem = ET.SubElement(root, 'secret')
secret_elem.text = os.environ['KAKAO_REFRESH']
print(ET.tostring(root, encoding='unicode'))
")
    
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

# --- 3. Naver Token 검증 및 갱신 -------------------------
NAVER_RESULT=$(BACKEND_BASE_URL="$BACKEND_BASE_URL" NAVER_ACCESS_TOKEN="$NAVER_ACCESS_TOKEN" $PYTHON_CMD -c "
import sys
import os
sys.path.insert(0, '.')
from src.utils.token_validator import validate_oauth_token
result = validate_oauth_token(os.environ['BACKEND_BASE_URL'], os.environ['NAVER_ACCESS_TOKEN'], '/api/auth/naver')
print('True' if result else 'False')
")
echo "🔍 NAVER_RESULT = $NAVER_RESULT"
if [[ "$NAVER_RESULT" == "True" ]]; then
    echo "🟢 Naver Token is VALID"
else
    echo "🔴 Naver Token is INVALID - Refreshing..."
    
    # 이전 token.json 파일 제거 (혼동 방지)
    rm -f token.json
    
    # set -e의 영향을 받지 않도록 실행
    set +e
    # Python 스크립트 실행 및 에러 캡처
    BACKEND_BASE_URL="$BACKEND_BASE_URL" NAVER_REFRESH_TOKEN="$NAVER_REFRESH_TOKEN" $PYTHON_CMD -c "
import sys
import json
import os
import requests
sys.path.insert(0, '.')

try:
    backend_url = os.environ['BACKEND_BASE_URL']
    refresh_token = os.environ['NAVER_REFRESH_TOKEN']
    endpoint = '/api/auth/naver/refresh'
    
    url = f\"{backend_url.rstrip('/')}/{endpoint.lstrip('/')}\"
    payload = {\"refreshToken\": refresh_token}
    
    print(f'Making request to: {url}', file=sys.stderr)
    resp = requests.post(url, json=payload, timeout=10)
    
    print(f'Response status: {resp.status_code}', file=sys.stderr)
    
    if resp.status_code == 200:
        result = resp.json()
        print(f'Response keys: {list(result.keys())}', file=sys.stderr)
        
        # 토큰 키 확인 (다양한 형식 지원)
        token = result.get('token') or result.get('accessToken') or result.get('access_token')
        refresh_token_resp = result.get('refreshToken') or result.get('refresh_token')
        
        if not token or not refresh_token_resp:
            print('Error: Missing tokens in response', file=sys.stderr)
            print(f'token exists: {bool(token)}, refresh_token exists: {bool(refresh_token_resp)}', file=sys.stderr)
            print(f'Response: {json.dumps(result)}', file=sys.stderr)
            sys.exit(1)
        
        # token.json에 저장
        with open('token.json', 'w') as f:
            json.dump(result, f)
        
        print('Success: token.json created', file=sys.stderr)
        sys.exit(0)
    else:
        print(f'Error: HTTP {resp.status_code}: {resp.text}', file=sys.stderr)
        sys.exit(1)
        
except Exception as e:
    import traceback
    print(f'Error: {e}', file=sys.stderr)
    traceback.print_exc(file=sys.stderr)
    sys.exit(1)
" >/tmp/naver_refresh_output.txt 2>/tmp/naver_refresh_error.txt
    PYTHON_EXIT=$?
    set -e  # 다시 set -e 활성화
    
    echo "[DEBUG] Python exit code: $PYTHON_EXIT"
    
    if [ $PYTHON_EXIT -ne 0 ]; then
        echo "❌ Failed to refresh Naver token (exit code: $PYTHON_EXIT)"
        echo "[DEBUG] Python stdout:"
        cat /tmp/naver_refresh_output.txt 2>/dev/null || echo "(empty)"
        echo "[DEBUG] Python stderr:"
        cat /tmp/naver_refresh_error.txt 2>/dev/null || echo "(empty)"
        if [ -f "token.json" ]; then
            echo "[DEBUG] token.json contents:"
            cat token.json
        fi
        exit 1
    fi
    
    if [ ! -f "token.json" ]; then
        echo "❌ token.json file not found after refresh"
        echo "[DEBUG] Python stdout:"
        cat /tmp/naver_refresh_output.txt 2>/dev/null || echo "(empty)"
        echo "[DEBUG] Python stderr:"
        cat /tmp/naver_refresh_error.txt 2>/dev/null || echo "(empty)"
        exit 1
    fi
    
    echo "📄 Refresh response saved to token.json"
    echo "[DEBUG] Checking token.json content..."
    cat token.json | head -c 200
    echo ""
    
    NAVER_ACCESS=$(jq -r '.token // .accessToken // .access_token' token.json 2>/dev/null)
    NAVER_REFRESH=$(jq -r '.refreshToken // .refresh_token' token.json 2>/dev/null)
    
    echo "[DEBUG] NAVER_ACCESS extracted: ${NAVER_ACCESS:0:20}..."
    echo "[DEBUG] NAVER_REFRESH extracted: ${NAVER_REFRESH:0:20}..."
    
    if [ -z "$NAVER_ACCESS" ] || [ -z "$NAVER_REFRESH" ]; then
        echo "❌ Failed to extract tokens from refresh response"
        echo "[DEBUG] token.json full contents:"
        cat token.json
        exit 1
    fi
    
    echo "✅ Extracted NAVER_ACCESS and NAVER_REFRESH tokens"
    
    echo "📤 Updating NAVER_ACCESS_TOKEN credential..."
    CREDENTIAL_XML=$(curl -s -X GET \
        -u "$JENKINS_USER:$JENKINS_PASS" \
        "$JENKINS_URL/credentials/store/system/domain/${CREDENTIAL_DOMAIN}/credential/NAVER_ACCESS_TOKEN/config.xml")
    
    if [ -z "$CREDENTIAL_XML" ] || echo "$CREDENTIAL_XML" | grep -q "Error"; then
        echo "❌ Failed to fetch NAVER_ACCESS_TOKEN credential XML"
        echo "Debug: Response: $CREDENTIAL_XML"
        exit 1
    fi
    
    UPDATED_XML=$(echo "$CREDENTIAL_XML" | NAVER_ACCESS="$NAVER_ACCESS" $PYTHON_CMD -c "
import sys
import xml.etree.ElementTree as ET
import os
try:
    xml_str = sys.stdin.read()
    root = ET.fromstring(xml_str)
    secret_elem = root.find('secret')
    if secret_elem is None:
        secret_elem = ET.SubElement(root, 'secret')
    secret_elem.text = os.environ['NAVER_ACCESS']
    print(ET.tostring(root, encoding='unicode'))
except Exception as e:
    print(f'Error: {e}', file=sys.stderr)
    sys.exit(1)
" 2>/tmp/py_error.txt)
    PYTHON_EXIT=$?
    
    if [ $PYTHON_EXIT -ne 0 ]; then
        echo "❌ Failed to update XML for NAVER_ACCESS_TOKEN"
        echo "Debug: Python error:"
        cat /tmp/py_error.txt
        exit 1
    fi
    
    if [ -z "$UPDATED_XML" ]; then
        echo "❌ UPDATED_XML is empty"
        exit 1
    fi
    
    echo "$UPDATED_XML" > /tmp/naver_access_token.xml
    HTTP_CODE=$(curl -s -w "%{http_code}" -o /tmp/curl_response.txt -X POST \
        -u "$JENKINS_USER:$JENKINS_PASS" \
        -H "Content-Type: application/xml" \
        --data-binary @/tmp/naver_access_token.xml \
        "$JENKINS_URL/credentials/store/system/domain/${CREDENTIAL_DOMAIN}/credential/NAVER_ACCESS_TOKEN/config.xml")
    
    if [ "$HTTP_CODE" != "200" ] && [ "$HTTP_CODE" != "201" ] && [ "$HTTP_CODE" != "302" ]; then
        echo "❌ Failed to update NAVER_ACCESS_TOKEN (HTTP $HTTP_CODE)"
        echo "Debug: Response:"
        cat /tmp/curl_response.txt
        exit 1
    fi
    
    echo "✅ NAVER_ACCESS_TOKEN credential updated successfully"
    
    echo "📤 Updating NAVER_REFRESH_TOKEN credential..."
    CREDENTIAL_XML=$(curl -s -X GET \
        -u "$JENKINS_USER:$JENKINS_PASS" \
        "$JENKINS_URL/credentials/store/system/domain/${CREDENTIAL_DOMAIN}/credential/NAVER_REFRESH_TOKEN/config.xml")
    
    if [ -z "$CREDENTIAL_XML" ] || echo "$CREDENTIAL_XML" | grep -q "Error"; then
        echo "❌ Failed to fetch NAVER_REFRESH_TOKEN credential XML"
        echo "Debug: Response: $CREDENTIAL_XML"
        exit 1
    fi
    
    UPDATED_XML=$(echo "$CREDENTIAL_XML" | NAVER_REFRESH="$NAVER_REFRESH" $PYTHON_CMD -c "
import sys
import xml.etree.ElementTree as ET
import os
try:
    xml_str = sys.stdin.read()
    root = ET.fromstring(xml_str)
    secret_elem = root.find('secret')
    if secret_elem is None:
        secret_elem = ET.SubElement(root, 'secret')
    secret_elem.text = os.environ['NAVER_REFRESH']
    print(ET.tostring(root, encoding='unicode'))
except Exception as e:
    print(f'Error: {e}', file=sys.stderr)
    sys.exit(1)
" 2>/tmp/py_error.txt)
    PYTHON_EXIT=$?
    
    if [ $PYTHON_EXIT -ne 0 ]; then
        echo "❌ Failed to update XML for NAVER_REFRESH_TOKEN"
        echo "Debug: Python error:"
        cat /tmp/py_error.txt
        exit 1
    fi
    
    if [ -z "$UPDATED_XML" ]; then
        echo "❌ UPDATED_XML is empty"
        exit 1
    fi
    
    echo "$UPDATED_XML" > /tmp/naver_refresh_token.xml
    HTTP_CODE=$(curl -s -w "%{http_code}" -o /tmp/curl_response.txt -X POST \
        -u "$JENKINS_USER:$JENKINS_PASS" \
        -H "Content-Type: application/xml" \
        --data-binary @/tmp/naver_refresh_token.xml \
        "$JENKINS_URL/credentials/store/system/domain/${CREDENTIAL_DOMAIN}/credential/NAVER_REFRESH_TOKEN/config.xml")
    
    if [ "$HTTP_CODE" != "200" ] && [ "$HTTP_CODE" != "201" ] && [ "$HTTP_CODE" != "302" ]; then
        echo "❌ Failed to update NAVER_REFRESH_TOKEN (HTTP $HTTP_CODE)"
        echo "Debug: Response:"
        cat /tmp/curl_response.txt
        exit 1
    fi
    
    echo "✅ NAVER_REFRESH_TOKEN credential updated successfully"
    
    echo "✅ Naver tokens refreshed and updated"
fi

# --- 4. JWT Token 검증 및 갱신 -------------------------
JWT_RESULT=$(BACKEND_BASE_URL="$BACKEND_BASE_URL" JWT_TOKEN="$JWT_TOKEN" $PYTHON_CMD -c "
import sys
import os
sys.path.insert(0, '.')
from src.utils.token_validator import validate_jwt_token
result, _ = validate_jwt_token(os.environ['BACKEND_BASE_URL'], os.environ['JWT_TOKEN'], '/api/auth/me')
print('True' if result else 'False')
")
echo "🔍 JWT_RESULT = $JWT_RESULT"
if [[ "$JWT_RESULT" == "True" ]]; then
    echo "🟢 JWT Token is VALID"
else
    echo "🔴 JWT Token is INVALID - Refreshing..."
    BACKEND_BASE_URL="$BACKEND_BASE_URL" JWT_REFRESH_TOKEN="$JWT_REFRESH_TOKEN" $PYTHON_CMD -c "
import sys
import json
import os
sys.path.insert(0, '.')
from src.utils.token_validator import refresh_jwt_token
result = refresh_jwt_token(os.environ['BACKEND_BASE_URL'], os.environ['JWT_REFRESH_TOKEN'], None, '/api/auth/refresh')
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
    CREDENTIAL_XML=$(curl -s -X GET \
        -u "$JENKINS_USER:$JENKINS_PASS" \
        "$JENKINS_URL/credentials/store/system/domain/${CREDENTIAL_DOMAIN}/credential/JWT_TOKEN/config.xml")
    
    UPDATED_XML=$(echo "$CREDENTIAL_XML" | JWT_ACCESS="$JWT_ACCESS" $PYTHON_CMD -c "
import sys
import xml.etree.ElementTree as ET
import os
xml_str = sys.stdin.read()
root = ET.fromstring(xml_str)
secret_elem = root.find('secret')
if secret_elem is None:
    secret_elem = ET.SubElement(root, 'secret')
secret_elem.text = os.environ['JWT_ACCESS']
print(ET.tostring(root, encoding='unicode'))
")
    
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
    CREDENTIAL_XML=$(curl -s -X GET \
        -u "$JENKINS_USER:$JENKINS_PASS" \
        "$JENKINS_URL/credentials/store/system/domain/${CREDENTIAL_DOMAIN}/credential/JWT_REFRESH_TOKEN/config.xml")
    
    UPDATED_XML=$(echo "$CREDENTIAL_XML" | JWT_REFRESH="$JWT_REFRESH" $PYTHON_CMD -c "
import sys
import xml.etree.ElementTree as ET
import os
xml_str = sys.stdin.read()
root = ET.fromstring(xml_str)
secret_elem = root.find('secret')
if secret_elem is None:
    secret_elem = ET.SubElement(root, 'secret')
secret_elem.text = os.environ['JWT_REFRESH']
print(ET.tostring(root, encoding='unicode'))
")
    
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
