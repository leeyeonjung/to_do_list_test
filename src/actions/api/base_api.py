"""requests를 사용한 API 테스트용 기본 API 클래스"""
import requests
from typing import Dict, Any, Optional
import logging

log = logging.getLogger(__name__)


class BaseAPI:
    """API 페이지 객체의 기본 클래스"""

    def __init__(self, base_url: str, headers: Optional[Dict[str, str]] = None):
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

    def get(self, endpoint: str, **kwargs) -> requests.Response:
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

    def post(self, endpoint: str, data: Optional[Any] = None,
             json: Optional[Dict] = None, **kwargs) -> requests.Response:
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

    def put(self, endpoint: str, data: Optional[Any] = None,
            json: Optional[Dict] = None, **kwargs) -> requests.Response:
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

    def delete(self, endpoint: str, **kwargs) -> requests.Response:
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

