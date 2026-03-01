# Worklog

Use this file to preserve context between sessions.

## Entry Template
### Date
`YYYY-MM-DD`

### Summary
- What changed in this session.

### Validation
- Commands run:
  - `uv run python src/transform.py`
  - `uv run python main.py`
  - `uv run streamlit run app.py` (if UI was checked)
- Result:
  - pass/fail and short notes

### Next Step
- The single next task to start with in the next session.

### Blockers / Questions
- Open issues or decisions needed.

---

## 2026-03-01
### Summary
- Added roadmap and capability documentation to `README.md`.
- Redesigned dashboard filters to timeline-based presets/custom range.
- Added teaching-style comments in key files.
- Added canonical schema + validation checks to transform pipeline.
- Added account balance engine to compute transfer-aware running balances per account.
- Added dashboard account views: running balance timeline and period-end allocation.

### Validation
- Commands run:
  - `python -m py_compile app.py src/helpers.py src/transform.py`
  - `python src/transform.py`
  - `python -m py_compile main.py src/balance.py src/helpers.py`
  - `python main.py`
  - `python -m py_compile app.py`
- Result:
  - pass

### Next Step
- Step 4: transfer integrity pass to avoid KPI/chart double-counting edge cases.

### Blockers / Questions
- None.
