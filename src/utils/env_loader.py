"""
환경 변수 로딩 유틸리티 모듈

로컬 환경과 Jenkins 환경에서 .env 파일을 순서대로 로드합니다.
1. ENV_FILE 환경 변수 (Jenkins credential을 통해 주입)
2. 로컬 환경: 프로젝트 루트의 /.env 파일
"""
import os
import logging
import re
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
    1. ENV_FILE 환경 변수 (Jenkins credential을 통해 주입) - 최우선
    2. 프로젝트 루트의 /.env 파일 (로컬 환경)
    
    ENV_FILE이 있으면 먼저 로드하고, 이어서 .env를 낮은 우선순위로 로드합니다.
    
    Returns:
        Optional[Path]: 로드된 환경 변수 파일의 경로, 없으면 None
    """
    project_root = get_project_root()
    
    # 1. ENV_FILE 환경 변수 확인 (Jenkins credential 우선)
    env_file_path = os.getenv("ENV_FILE")
    env_loaded_path = None
    if env_file_path:
        env_file = Path(env_file_path)
        if env_file.exists():
            load_dotenv(env_file, override=False)
            log.info(f"ENV_FILE 환경 변수에서 파일 로드 완료: {env_file}")
            env_loaded_path = env_file
        else:
            log.warning(f"ENV_FILE 환경 변수가 가리키는 파일이 존재하지 않습니다: {env_file_path}")
    
    # 2. 로컬 환경: 프로젝트 루트의 .env 파일 (후순위)
    local_env = project_root / ".env"
    if local_env.exists():
        load_dotenv(local_env, override=False)
        log.info(f"로컬 .env 파일 로드 완료: {local_env}")
        return env_loaded_path or local_env
    
    if env_loaded_path:
        return env_loaded_path
    
    log.warning("환경 변수 파일을 찾을 수 없습니다. (ENV_FILE 또는 .env)")
    return None


def get_env_path() -> Optional[Path]:
    """
    환경 변수 파일 경로를 우선순위에 따라 반환합니다.
    
    파일 쓰기 등의 용도로 사용할 때는 우선순위에 따라 하나의 파일 경로만 반환합니다.
    읽기용으로는 load_env_files()를 통해 환경 변수가 로드되어 있습니다.
    
    우선순위:
    1. ENV_FILE 환경 변수 (Jenkins credential을 통해 주입)
    2. 프로젝트 루트의 /.env 파일 (로컬 환경)
    
    Returns:
        Optional[Path]: 환경 변수 파일 경로, 없으면 None
    """
    # 1. ENV_FILE 환경 변수 확인 (Jenkins credential 우선)
    env_file_path = os.getenv("ENV_FILE")
    if env_file_path:
        env_file = Path(env_file_path)
        if env_file.exists():
            return env_file
    
    # 2. 로컬 환경: 프로젝트 루트의 .env 파일
    project_root = get_project_root()
    local_env = project_root / ".env"
    if local_env.exists():
        return local_env
    
    return None


def upsert_env_value(env_path: Path, key: str, value: str) -> None:
    """
    env 파일에 key=value를 업데이트하거나 추가합니다.
    
    Args:
        env_path: 환경 변수 파일 경로
        key: 환경 변수 키
        value: 환경 변수 값
    """
    if not env_path or not env_path.exists():
        log.error(f".env 파일 없음: {env_path}")
        return

    with open(env_path, "r", encoding="utf-8") as f:
        content = f.read()

    pattern = rf"^{re.escape(key)}=.*$"
    replacement = f"{key}={value}"

    if re.search(pattern, content, flags=re.MULTILINE):
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
    else:
        content += f"\n{replacement}\n"

    with open(env_path, "w", encoding="utf-8") as f:
        f.write(content)


# 모듈 로드 시 자동으로 환경 변수 파일 로드
_loaded_env_path = load_env_files()
