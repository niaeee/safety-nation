"""중앙 환경변수 설정. 모든 모듈은 여기서만 환경값을 읽는다."""
import os
from dotenv import load_dotenv

load_dotenv()

FLASK_ENV = os.getenv("FLASK_ENV", "development")
SECRET_KEY = os.getenv("SECRET_KEY", "")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"
SCHOOL_DATASET = os.getenv("SCHOOL_DATASET", "national").lower()  # national | ulsan

MAP_PROVIDER = os.getenv("MAP_PROVIDER", "osm").lower()  # osm | vworld
VWORLD_API_KEY = os.getenv("VWORLD_API_KEY", "")

KAKAO_API_KEY = os.getenv("KAKAO_API_KEY", "")
KMA_API_KEY = os.getenv("KMA_API_KEY", "")
DATA_GO_KR_API_KEY = os.getenv("DATA_GO_KR_API_KEY", "")
NEIS_API_KEY = os.getenv("NEIS_API_KEY", "")

AI_DRAFTER = os.getenv("AI_DRAFTER", "cli").lower()  # cli | sdk | template
CLAUDE_CLI_PATH = os.getenv("CLAUDE_CLI_PATH", "claude")
AI_DRAFT_TIMEOUT = int(os.getenv("AI_DRAFT_TIMEOUT", "60"))
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")
ANTHROPIC_MAX_TOKENS = int(os.getenv("ANTHROPIC_MAX_TOKENS", "2048"))
