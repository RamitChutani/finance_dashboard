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
- Fixed transaction duplication in transform dedupe logic (canonical normalization + stable dedupe keys).
- Fixed date range edge-case crash in Streamlit custom date filter.
- Added lean transfer format validation rules (`Transfer` requires `from->to`; non-transfer forbids `->`).
- Added Groww opening balance entry (`2088.39` on `2025-04-09`) to local transaction data.

### Validation
- Commands run:
  - `python -m py_compile app.py src/helpers.py src/transform.py`
  - `python src/transform.py`
  - `python -m py_compile main.py src/balance.py src/helpers.py`
  - `python main.py`
  - `python -m py_compile app.py`
  - `python src/transform.py`
  - `python main.py`
- Result:
  - pass

### Next Step
- Step 5: add budget data model (`budgets.csv` + loader) with simple schema validation.

### Blockers / Questions
- None.
