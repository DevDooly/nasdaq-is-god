import os
import logging
from dotenv import load_dotenv

def setup_logging():
    """애플리케이션의 로깅을 설정합니다."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("bot.log"),
            logging.StreamHandler()  # 터미널에도 로그를 출력
        ]
    )
    # 다른 모듈에서 사용할 수 있도록 최상위 로거를 반환
    return logging.getLogger("telegram_bot")

def load_environment():
    """'.env' 파일에서 환경 변수를 로드합니다."""
    # 이 파일의 상위 디렉토리(프로젝트 루트)에 .env 파일이 있다고 가정
    dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path)
        logging.info(".env 파일을 로드했습니다.")
    else:
        logging.warning(".env 파일을 찾을 수 없습니다. 환경 변수를 직접 설정해야 합니다.")

# 스크립트 로드 시 환경 변수와 로깅을 바로 설정
load_environment()
logger = setup_logging()
