import json
from .branch_state import BranchState


def format_single_history(branch: BranchState) -> str:
    """단일 BranchState의 history를 프롬프트의 {branch_history} 변수용 JSON 문자열로 변환."""
    return json.dumps(branch.history, ensure_ascii=False, indent=2)
