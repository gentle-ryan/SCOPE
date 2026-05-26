# SCOPE

**Scenario-based Operational Pipeline for Ethics Impact Assessment**

SCOPE is an automated pipeline that takes a PDF describing an AI system and produces a structured ethics impact assessment. It extracts the system's operational workflows, generates failure events per entity, simulates multi-stakeholder scenarios, and maps outcomes to Korea's 10-principle AI ethics framework — outputting structured JSON at every stage.

> **Live demo:** [scope.snu.ac.kr](https://scope.snu.ac.kr) *(ACL 2025 System Demonstration)*

---

## Pipeline

```
PDF
 └─ parse_node            →  parsed.md
 └─ workflow_entity_node  →  workflows.json, entities.json
 └─ entity_role_node      →  entity_roles.json, stakeholder_agents.json
 └─ event_verify_node     →  verified_events.json
 └─ sim_node              →  merged_scenarios.md
 └─ impact_node           →  impact_report.json
```

| Stage | Output | Description |
|---|---|---|
| **Document Parsing** | `parsed.md` | Extracts and structures text from the uploaded PDF |
| **Workflow & Entity Extraction** | `workflows.json`, `entities.json` | Identifies 5 operational stages, agents, and data objects |
| **Entity Role Refinement** | `entity_roles.json`, `stakeholder_agents.json` | Assigns detailed roles to each entity via RAG + self-refine |
| **Event Generation & Verification** | `verified_events.json` | Generates failure events per entity (Normal/Slip/Mistake taxonomy); verifies with RAG |
| **Scenario Simulation** | `merged_scenarios.md` | BFS-based multi-agent propagation; merges into coherent narratives |
| **Ethics Impact Analysis** | `impact_report.json` | Maps scenarios to positive/negative impacts under 10 ethics codes; grades scale, scope, likelihood, resolvability |

Each stage checkpoints to disk — if a run is interrupted, re-running resumes from where it left off.

---

## Setup

**Requirements:** Python 3.11+, a [Gemini API key](https://aistudio.google.com/)

```bash
git clone https://github.com/gentle-ryan/scope.git
cd scope

python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
# Edit .env and set GEMINI_API_KEY=...
```

---

## Usage

```bash
# Run full pipeline (Korean output)
python run.py path/to/document.pdf

# Run full pipeline (English output)
python run.py path/to/document.pdf --lang en

# Custom run ID
python run.py path/to/document.pdf --run-id my-run-001

# Resume an interrupted run
python run.py --resume <run_id>

# Re-run from a specific step (re-runs that step and all following steps)
python run.py --resume <run_id> --from-step event_verify
```

Outputs are written to `outputs/<run_id>/`.

---

## Output format

### `workflows.json`
```json
[
  {
    "id": 1,
    "type": "Data Collection, Preprocessing & Validation",
    "description": "..."
  },
  ...
]
```

### `verified_events.json`
```json
[
  {
    "event_id": 1,
    "workflow_id": 1,
    "entity": { "entity_name": "Data Curator", "entity_type": "agent" },
    "property": "Rule-based Mistake",
    "event_description": "..."
  },
  ...
]
```

### `impact_report.json`
```json
{
  "total_system_report": {
    "ethics_assessment": [
      {
        "code": "1",
        "name": "Human Rights Protection",
        "positives": [
          {
            "keyword": "...",
            "impact": "...",
            "scale":       { "grade": "Large",     "reason": "..." },
            "scope":       { "grade": "Long-term",  "reason": "..." },
            "likelihood":  { "grade": "High",       "reason": "..." }
          }
        ],
        "negatives": [
          {
            "keyword": "...",
            "impact": "...",
            "scale":         { "grade": "Severe",   "reason": "..." },
            "scope":         { "grade": "Long-term", "reason": "..." },
            "likelihood":    { "grade": "Moderate",  "reason": "..." },
            "resolvability": { "grade": "Moderate",  "reason": "..." }
          }
        ],
        "not_found": [
          {
            "item": "...",
            "description": "...",
            "recommendation": "..."
          }
        ]
      },
      ...
    ]
  }
}
```

---

## Configuration

| Variable in `config.py` | Default | Description |
|---|---|---|
| `STEP5_MAX_TURN` | 3 | Scenario simulation BFS depth |
| `STEP5_BATCH_SIZE` | 5 | Events processed per BFS batch |
| `STEP5_EVENT_CONCURRENCY` | 5 | Parallel scenario threads |
| `STEP4_VERIFY_FAIL_THRESHOLD` | 0.3 | Acceptable event verification failure rate |

---

## Models used

All calls go through `services/llm_client.py`. Three Gemini model tiers:

| Tier | Default model | Used for |
|---|---|---|
| `FLASH_MODEL` | `gemini-2.0-flash` | Main generation, self-refine |
| `LITE_MODEL` | `gemini-2.0-flash-lite` | Verification, dedup, grading |
| `PRO_MODEL` | `gemini-2.5-pro` | Selective high-stakes calls |

Override via environment variables `FLASH_MODEL`, `LITE_MODEL`, `PRO_MODEL`.

---

## Tech stack

- **Orchestration**: [LangGraph](https://github.com/langchain-ai/langgraph) `StateGraph`
- **LLM**: Google Gemini via `google-genai` SDK
- **PDF parsing**: `pymupdf4llm` + Gemini vision for scanned pages
- **Vector store**: ChromaDB with `gemini-embedding-001`
- **Deduplication**: cosine similarity on Gemini embeddings (threshold 0.85)

---

## Citation

```bibtex
@inproceedings{scope2025,
  title     = {SCOPE: Scenario-based Operational Pipeline for Ethics Impact Assessment},
  booktitle = {Proceedings of ACL 2025 System Demonstrations},
  year      = {2025},
}
```
