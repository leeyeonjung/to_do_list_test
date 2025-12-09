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

    def get(self, endpoint, **kwargs):
        """
        GET 요청 전송.

        Args:
            endpoint: API 엔드포인트
            **kwargs: requests.get에 대한 추가 인자

        Returns:
            Response 객체
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        log.info(f"GET {url}")
        response = self.session.get(url, **kwargs)
        log.info(f"Response status: {response.status_code}")
        return response

    def post(self, endpoint, data=None, json=None, **kwargs):
        """
        POST 요청 전송.

        Args:
            endpoint: API 엔드포인트
            data: 요청 본문에 전송할 데이터
            json: 요청 본문에 전송할 JSON 데이터
            **kwargs: requests.post에 대한 추가 인자

        Returns:
            Response 객체
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        log.info(f"POST {url}")
        log.debug(f"Request data: {data or json}")
        response = self.session.post(url, data=data, json=json, **kwargs)
        log.info(f"Response status: {response.status_code}")
        return response

    def put(self, endpoint, data=None, json=None, **kwargs):
        """
        PUT 요청 전송.

        Args:
            endpoint: API 엔드포인트
            data: 요청 본문에 전송할 데이터
            json: 요청 본문에 전송할 JSON 데이터
            **kwargs: requests.put에 대한 추가 인자

        Returns:
            Response 객체
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        log.info(f"PUT {url}")
        log.debug(f"Request data: {data or json}")
        response = self.session.put(url, data=data, json=json, **kwargs)
        log.info(f"Response status: {response.status_code}")
        return response

    def delete(self, endpoint, **kwargs):
        """
        DELETE 요청 전송.

        Args:
            endpoint: API 엔드포인트
            **kwargs: requests.delete에 대한 추가 인자

        Returns:
            Response 객체
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        log.info(f"DELETE {url}")
        response = self.session.delete(url, **kwargs)
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
