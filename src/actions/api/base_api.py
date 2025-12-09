"""requests를 사용한 API 테스트용 기본 API 클래스"""
import requests
import logging

log = logging.getLogger(__name__)


class BaseAPI:
    """API 페이지 객체의 기본 클래스"""

    def __init__(self, base_url, headers=None):
        """
        BaseAPI 초기화.

        Args:
            base_url: API 기본 URL
            headers: 모든 요청에 포함할 선택적 헤더
        """
        self.base_url = base_url.rstrip('/')
        self.headers = headers or {}
        self.session = requests.Session()
        if self.headers:
            self.session.headers.update(self.headers)

    def get(self, endpoint):
        """
        GET 요청 전송.

        Args:
            endpoint: API 엔드포인트

        Returns:
            Response 객체
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        log.info(f"GET {url}")
        response = self.session.get(url)
        log.info(f"Response status: {response.status_code}")
        return response

    def post(self, endpoint, payload=None, **kwargs):
        """
        POST 요청 전송.

        Args:
            endpoint: API 엔드포인트
            payload: 요청 본문 JSON

        Returns:
            Response 객체
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        log.info(f"POST {url}")
        # payload 인자 또는 json 키워드 인자를 모두 허용한다.
        json_payload = kwargs.pop("json", payload)
        log.debug(f"Request data: {json_payload}")
        response = self.session.post(url, json=json_payload, **kwargs)
        log.info(f"Response status: {response.status_code}")
        return response

    def put(self, endpoint, payload=None, **kwargs):
        """
        PUT 요청 전송.

        Args:
            endpoint: API 엔드포인트
            payload: 요청 본문 JSON

        Returns:
            Response 객체
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        log.info(f"PUT {url}")
        json_payload = kwargs.pop("json", payload)
        log.debug(f"Request data: {json_payload}")
        response = self.session.put(url, json=json_payload, **kwargs)
        log.info(f"Response status: {response.status_code}")
        return response

    def delete(self, endpoint):
        """
        DELETE 요청 전송.

        Args:
            endpoint: API 엔드포인트

        Returns:
            Response 객체
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        log.info(f"DELETE {url}")
        response = self.session.delete(url)
        log.info(f"Response status: {response.status_code}")
        return response
        
        
class LoginAPI(BaseAPI):
    """소셜 로그인용 API 헬퍼"""

    def request_social_login(self, provider, access_token):
        url = f"{self.base_url}/api/auth/{provider}"
        res = self.session.post(
            url,
            json={"accessToken": access_token},
            headers={"Content-Type": "application/json"},
            timeout=5,
        )
        return res
