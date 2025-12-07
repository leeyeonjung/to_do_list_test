"""
환경 변수 로딩 유틸리티 모듈

로컬 환경과 Jenkins 환경에서 .env 파일을 순서대로 로드합니다.
1. 로컬 환경: 프로젝트 루트의 /.env 파일
2. Jenkins 환경: credential을 통해 주입받은 .env-dev-test 파일
"""
import logging
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

log = logging.getLogger(__name__)


def get_project_root() -> Path:
    """
    프로젝트 루트 디렉토리 경로를 반환합니다.
    
    Returns:
        Path: 프로젝트 루트 디렉토리 경로
    """
    # 이 파일의 위치에서 프로젝트 루트까지의 경로 계산
    # src/utils/env_loader.py -> 프로젝트 루트
    current_file = Path(__file__).resolve()
    return current_file.parent.parent.parent


def load_env_files() -> Optional[Path]:
    """
    환경 변수 파일을 순서대로 로드합니다.
    
    우선순위:
    1. 프로젝트 루트의 /.env 파일 (로컬 환경) - 먼저 로드
    2. 프로젝트 루트의 /.env-dev-test 파일 (Jenkins 환경) - 나중에 로드하여 덮어씀
    
    두 파일이 모두 존재하는 경우, .env-dev-test의 값이 .env의 값을 덮어씁니다.
    
    Returns:
        Optional[Path]: 마지막으로 로드된 환경 변수 파일의 경로, 없으면 None
    """
    project_root = get_project_root()
    loaded_path = None
    
    # 1. 로컬 환경: 프로젝트 루트의 .env 파일 (먼저 로드)
    local_env = project_root / ".env"
    if local_env.exists():
        load_dotenv(local_env, override=False)
        log.info(f"로컬 .env 파일 로드 완료: {local_env}")
        loaded_path = local_env
    
    # 2. Jenkins 환경: 프로젝트 루트의 .env-dev-test 파일 (나중에 로드하여 덮어씀)
    jenkins_env = project_root / ".env-dev-test"
    if jenkins_env.exists():
        load_dotenv(jenkins_env, override=True)
        log.info(f"Jenkins .env-dev-test 파일 로드 완료 (기존 값 덮어씀): {jenkins_env}")
        loaded_path = jenkins_env
    
    if loaded_path is None:
        log.warning("환경 변수 파일을 찾을 수 없습니다. (.env 또는 .env-dev-test)")
    
    return loaded_path


def get_env_path() -> Optional[Path]:
    """
    환경 변수 파일 경로를 우선순위에 따라 반환합니다.
    
    파일 쓰기 등의 용도로 사용할 때는 우선순위에 따라 하나의 파일 경로만 반환합니다.
    읽기용으로는 load_env_files()를 통해 두 파일이 모두 로드되어 있습니다.
    
    우선순위:
    1. 프로젝트 루트의 /.env 파일 (로컬 환경)
    2. 프로젝트 루트의 /.env-dev-test 파일 (Jenkins 환경)
    
    Returns:
        Optional[Path]: 환경 변수 파일 경로, 없으면 None
    """
    project_root = get_project_root()
    
    # 1. 로컬 환경: 프로젝트 루트의 .env 파일
    local_env = project_root / ".env"
    if local_env.exists():
        return local_env
    
    # 2. Jenkins 환경: 프로젝트 루트의 .env-dev-test 파일
    jenkins_env = project_root / ".env-dev-test"
    if jenkins_env.exists():
        return jenkins_env
    
    return None


# 모듈 로드 시 자동으로 환경 변수 파일 로드
_loaded_env_path = load_env_files()
