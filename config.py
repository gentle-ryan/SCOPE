from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent
OUTPUTS_DIR = BASE_DIR / "outputs"

GEMINI_EMBED_MODEL = "models/gemini-embedding-001"

STEP5_MAX_TURN = 3
STEP5_BATCH_SIZE = 5
STEP5_EVENT_CONCURRENCY = 5
STEP5_MERGE_PREFIX_LEN = 5

STEP4_VERIFY_FAIL_THRESHOLD = 0.3
STEP4_MAX_RETRY = 2
