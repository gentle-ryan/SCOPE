import uuid
from pathlib import Path
from config import OUTPUTS_DIR


def generate_run_id() -> str:
    return str(uuid.uuid4())


def get_run_dir(run_id: str) -> Path:
    run_dir = OUTPUTS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def get_pdf_dir(run_id: str) -> Path:
    d = get_run_dir(run_id) / "pdf"
    d.mkdir(exist_ok=True)
    return d


def get_report_dir(run_id: str) -> Path:
    d = get_run_dir(run_id) / "report"
    d.mkdir(exist_ok=True)
    return d
