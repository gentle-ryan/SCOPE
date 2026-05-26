# SCOPE

**Scenario-based Operational Pipeline for Ethics Impact Assessment**

SCOPE is an automated pipeline that takes a PDF describing an AI system and produces a structured ethics impact assessment. It extracts the system's operational workflows, generates failure events per entity, simulates multi-stakeholder scenarios, and maps outcomes to Korea's 10-principle AI ethics framework — outputting structured JSON at every stage.

> **Live demo:** [scope.snu.ac.kr](https://scope.snu.ac.kr)

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

| Stage | Description |
|---|---|
| **Document Parsing** | Extracts and structures text from the uploaded PDF |
| **Workflow & Entity Extraction** | Identifies 5 operational stages, agents, and data objects |
| **Entity Role Refinement** | Assigns detailed roles to each entity via RAG + self-refine |
| **Event Generation & Verification** | Generates failure events per entity (Normal/Slip/Mistake taxonomy); verifies with RAG |
| **Scenario Simulation** | BFS-based multi-agent propagation; merges into coherent narratives |
| **Ethics Impact Analysis** | Maps scenarios to positive/negative impacts under 10 ethics codes; grades scale, scope, likelihood, resolvability |

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
# Edit .env: set GEMINI_API_KEY=...
```

---

## Usage

```bash
# Run full pipeline (Korean output)
python run.py path/to/document.pdf

# Run full pipeline (English output)
python run.py path/to/document.pdf --lang en

# Resume an interrupted run
python run.py --resume <run_id>

# Re-run from a specific step
python run.py --resume <run_id> --from-step event_verify
```

Outputs are written to `outputs/<run_id>/`.

### Export report to Markdown

```bash
# Print to stdout
python export_markdown.py outputs/<run_id>/impact_report.json

# Save to file
python export_markdown.py outputs/<run_id>/impact_report.json -o report.md
```

---

## Output: `impact_report.json`

```json
{
  "total_system_report": {
    "ethics_assessment": [
      {
        "code": "1",
        "name": "Human Rights Protection",
        "positives": [
          {
            "keyword": "Equal treatment in automated decision-making",
            "impact": "...",
            "evidence_scenario": "Scenario#12, Scenario#34",
            "scale":      { "grade": "Large",    "reason": "..." },
            "scope":      { "grade": "Long-term", "reason": "..." },
            "likelihood": { "grade": "High",      "reason": "..." }
          }
        ],
        "negatives": [
          {
            "keyword": "Autonomy infringement through over-reliance",
            "impact": "...",
            "scale":         { "grade": "Severe",   "reason": "..." },
            "scope":         { "grade": "Long-term", "reason": "..." },
            "likelihood":    { "grade": "Moderate",  "reason": "..." },
            "resolvability": { "grade": "Moderate",  "reason": "..." }
          }
        ],
        "not_found": [
          {
            "item": "Grievance procedure for algorithmic decisions",
            "description": "...",
            "recommendation": "..."
          }
        ]
      }
    ]
  }
}
```

10 ethics codes are assessed: Human Rights, Privacy, Diversity, Non-maleficence, Public Good, Solidarity, Data Governance, Accountability, User Safety, Transparency.

---

## Tech stack

- **Orchestration**: [LangGraph](https://github.com/langchain-ai/langgraph) `StateGraph`
- **LLM**: Google Gemini via `google-genai` SDK
- **PDF parsing**: `pymupdf4llm` + Gemini vision for scanned pages
- **Vector store**: ChromaDB with `gemini-embedding-001`

---

## Citation

Coming soon.
