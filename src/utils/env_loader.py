"""
환경 변수 로딩 유틸리티 모듈

환경에 따라 적절한 .env 파일을 로드합니다.
- Jenkins 환경: ENV_FILE 환경 변수 (Jenkins credential)만 사용
- 로컬 환경: 프로젝트 루트의 .env 파일만 사용
"""
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

log = logging.getLogger(__name__)


def get_project_root():
    """
    프로젝트 루트 디렉토리 경로 반환
    
    Returns:
        Path: 프로젝트 루트 디렉토리 경로
    """
    # 이 파일의 위치에서 프로젝트 루트까지의 경로 계산
    # src/utils/env_loader.py -> 프로젝트 루트
    current_file = Path(__file__).resolve()
    return current_file.parent.parent.parent


def load_env_files():
    """
    환경에 따라 적절한 환경 변수 파일 로드
    
    로드 규칙:
    1. ENV_FILE 환경 변수가 있으면 (Jenkins 환경)
       → ENV_FILE만 로드하고 종료 (로컬 .env 무시)
    2. ENV_FILE이 없으면 (로컬 개발 환경)
       → 프로젝트 루트의 .env 파일 로드
    
    Returns:
        Optional[Path]: 로드된 환경 변수 파일 경로, 없으면 None
    """
    project_root = get_project_root()
    log.debug(f"프로젝트 루트 경로: {project_root}")
    
    # Jenkins 환경: ENV_FILE 로드
    env_file_path = os.getenv("ENV_FILE")
    env_loaded_path = None
    if env_file_path:
        env_file = Path(env_file_path)
        log.debug(f"ENV_FILE 환경변수 감지: {env_file_path}")
        if env_file.exists():
            load_dotenv(env_file, override=False)
            log.info(f"ENV_FILE 환경 변수에서 파일 로드 완료: {env_file}")
            env_loaded_path = env_file
        else:
            log.warning(f"ENV_FILE 환경 변수가 가리키는 파일이 존재하지 않습니다: {env_file_path}")
    else:
        log.debug("ENV_FILE 환경변수 없음")
    
    # ENV_FILE이 로드되었으면 로컬 .env 무시하고 종료
    if env_loaded_path:
        log.debug("ENV_FILE이 로드되었으므로 로컬 .env 파일 무시")
        log.debug(f"BACKEND_BASE_URL: {os.getenv('BACKEND_BASE_URL')}")
        log.debug(f"WEB_BASE_URL: {os.getenv('WEB_BASE_URL')}")
        return env_loaded_path
    
    # 로컬 환경: .env 파일 로드
    local_env = project_root / ".env"
    log.debug(f"로컬 .env 파일 경로 확인 중: {local_env}")
    log.debug(f"파일 존재 여부: {local_env.exists()}")
    
    if local_env.exists():
        load_dotenv(local_env, override=False)
        log.info(f"로컬 .env 파일 로드 완료: {local_env}")
        log.debug(f"BACKEND_BASE_URL: {os.getenv('BACKEND_BASE_URL')}")
        log.debug(f"WEB_BASE_URL: {os.getenv('WEB_BASE_URL')}")
        return local_env
    
    log.warning("환경 변수 파일을 찾을 수 없습니다")
    return None