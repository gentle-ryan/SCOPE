from dataclasses import dataclass, field


@dataclass
class BranchState:
    branch_id: str
    event_id: int = 0
    wf_id: int = 0
    history: list[dict] = field(default_factory=list)
    # history item: {"type": "event"|"action"|"effect", "entity": str, "content": str}
    is_terminated: bool = False
    termination_reason: str = "none"  # none | infeasible | acausal | concluded | duplicate
