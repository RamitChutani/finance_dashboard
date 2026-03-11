# Repository Guidelines

This file provides context for agentic coding agents operating in this repository.

## Project Structure & Module Organization

```
finance_dashboard/
├── app.py                    # Main Streamlit dashboard entrypoint (UI layer)
├── main.py                   # Minimal runtime sanity check
├── src/
│   ├── transform.py          # Raw CSV ingestion and normalization (ETL)
│   ├── helpers.py            # Shared data-loading utilities (with Streamlit cache)
│   └── balance.py            # Account balance computation engine
├── data/
│   ├── raw/                  # Drop source exports here (*.csv)
│   └── transactions.csv      # Canonical cleaned dataset
├── pages/                    # Reserved for multi-page Streamlit views
├── tests/                    # pytest test suite (add tests here)
└── docs/
    └── WORKLOG.md            # Session continuity context
```

**Architecture Principles:**
- Business logic in `src/` (testable, reusable)
- UI code in `app.py` or `pages/` (presentation only)
- Data pipeline (`transform.py`) runs independently of the dashboard

---

## Build, Test, and Development Commands

### Dependencies & Environment
```bash
uv sync              # Install and lock dependencies from pyproject.toml / uv.lock
```

### Running the Application
```bash
uv run streamlit run app.py     # Launch the dashboard locally
uv run python main.py           # Minimal runtime sanity check (validates balance engine)
```

### Data Pipeline
```bash
uv run python src/transform.py  # Rebuild/append master transactions from data/raw/*.csv
# Run transform BEFORE launching app if raw files changed
```

### Testing
```bash
uv run pytest                   # Run all tests
uv run pytest tests/            # Run all tests in tests/ directory
uv run pytest tests/test_foo.py # Run specific test file
uv run pytest tests/test_foo.py::test_bar  # Run a single test function
uv run pytest -k "transform"    # Run tests matching keyword "transform"
uv run pytest -v               # Verbose output (shows each test name)
uv run pytest --tb=short       # Shorter traceback format
```

### Code Quality (when configured)
```bash
uv run ruff check .            # Lint all Python files
uv run ruff check src/transform.py  # Lint specific file
uv run ruff format .           # Format code (if ruff format is added)
```

---

## Coding Style & Naming Conventions

### General Rules
- **Python 3.12+**, 4-space indentation, UTF-8 encoding
- Use `snake_case` for functions, variables, and file names
- Use `UPPER_SNAKE_CASE` for module-level constants (e.g., `MASTER_CSV`, `ALLOWED_TYPES`)
- Use `PascalCase` only for class names (if classes are introduced)
- Keep lines under ~100 characters (soft limit)

### Imports Organization
Order imports with a blank line between each group:
1. Standard library (`pathlib`, `re`, `datetime`)
2. Third-party packages (`pandas`, `streamlit`, `plotly`)
3. Local application imports (`from src.balance import ...`)

```python
# Good example
import pandas as pd
from pathlib import Path

import streamlit as st
import plotly.express as px

from src.helpers import load_data, load_account_balances
from src.balance import build_account_balance_timeline
```

### Type Hints
- Add type hints on **all public functions** (parameters and return values)
- Use built-in types (`list`, `dict`, `str`) or `typing` module for complex types
- Prefer `pd.DataFrame` over generic `Any` for DataFrame returns

```python
# Good
def load_data() -> pd.DataFrame:
def get_preset_range(preset: str, anchor_date, min_date) -> tuple[date, date]:

# Avoid
def load_data():  # No type hints
def get_preset_range(preset, anchor_date, min_date):  # Incomplete hints
```

### Function Design
- Prefer **small, single-purpose functions** (one idea per function)
- Keep functions under ~50 lines when possible
- Private functions start with underscore: `_validate_columns(df)`
- Document the **why**, not the obvious: explain business rules, not syntax

### Comments Style
- Brief, intent-focused comments explaining **why**, not obvious **what**
- Write for a learner with rudimentary Python knowledge
- Avoid overly verbose commentary
- Example from codebase:
```python
# Lean transfer integrity checks based on source-app export rules.
has_transfer_arrow = df["account"].astype(str).str.contains("->", regex=False)
```

### Docstrings
- Use triple-quoted strings for module-level and public function docs
- Follow simple format: purpose, parameters (if non-obvious), returns
- Keep concise; one paragraph preferred

```python
def clean_raw(df: pd.DataFrame) -> pd.DataFrame:
    """Validate and normalize raw export DataFrame to canonical schema."""
```

---

## Error Handling

### Validation Functions
- Use **fail-fast** validation for input contracts (raise early with clear messages)
- Raise descriptive `ValueError` with details (e.g., `f"Missing column(s): {missing}"`)
- Validate at module boundaries (raw input, canonical schema)

```python
def validate_raw_columns(df: pd.DataFrame) -> None:
    required_raw = set(RAW_TO_CANONICAL_COLS.keys())
    missing = sorted(required_raw - set(df.columns))
    if missing:
        raise ValueError(f"Raw file is missing required column(s): {missing}")
```

### Runtime Errors
- Let exceptions propagate for unexpected failures (crash early, fix properly)
- Use guard clauses for expected empty states
- Provide clear user-facing messages in Streamlit UI

```python
# Guard clause pattern in app.py
if df.empty:
    st.warning("No transactions found. Run the transform step and reload.")
    st.stop()
```

### File Operations
- Create parent directories before writing: `MASTER_CSV.parent.mkdir(parents=True, exist_ok=True)`
- Use `Path` objects instead of string concatenation for paths

---

## Streamlit-Specific Patterns

### Page Configuration
- Set `st.set_page_config()` **before** any widget or text rendering
- Use `layout="wide"` for dashboards requiring full-width charts

```python
st.set_page_config(page_title="Finance Dashboard", layout="wide")
```

### Caching
- Use `@st.cache_data` for expensive data loading operations
- Return copies from cached functions to prevent mutation:

```python
@st.cache_data
def load_data() -> pd.DataFrame:
    df = pd.read_csv(MASTER_CSV)
    return df

# In app.py, always copy before editing
df = load_data()
df = df.copy()  # Critical: prevent cache mutation
```

### Widget Ordering
- Define sidebar controls **before** using filtered data
- Single source of truth: one filtered DataFrame for the entire view

### UI Components
- Use `st.metric()` for key numbers
- Use `st.columns()` for layout grid
- Use `st.plotly_chart(..., width="stretch")` for responsive charts
- Add `st.divider()` to visually separate sections

---

## Testing Guidelines

### Test Organization
- Place tests in `tests/` directory
- Name test files: `test_<module>.py` (e.g., `test_transform.py`)
- Name test functions: `test_<description>()` (e.g., `test_clean_raw_validates_columns()`)

### Test Scope for Data Transforms
Minimum coverage:
1. **Column mapping**: verify raw columns map to canonical names correctly
2. **Datetime parsing**: ensure date formats are handled (including mixed formats)
3. **signed_amount behavior**: income/expense signs are correct

```python
def test_signed_amount_income_is_positive():
    df = pd.DataFrame({
        "datetime": ["2024-01-01"],
        "type": ["Income"],
        "amount": [1000],
        ...
    })
    result = clean_raw(df)
    assert result["signed_amount"].iloc[0] == 1000

def test_signed_amount_expense_is_negative():
    df = pd.DataFrame({
        "datetime": ["2024-01-01"],
        "type": ["Expense"],
        "amount": [500],
        ...
    })
    result = clean_raw(df)
    assert result["signed_amount"].iloc[0] == -500
```

### Validation Test Cases
- Test error paths: missing columns, invalid types, null values
- Test edge cases: empty DataFrame, single row, duplicate handling

### Running Tests Before Commit
```bash
uv run pytest tests/ -v
uv run python src/transform.py
uv run python main.py
```

---

## Commit & Pull Request Guidelines

### Commit Messages
- Use short, plain-English subjects (e.g., `add account balance timeline`)
- Imperative mood: "add feature" not "added feature"
- Under ~72 characters
- One concern per commit

### PR Requirements
- What changed and why
- Any data/model assumptions
- UI screenshots/GIFs for dashboard changes
- Steps to validate locally

---

## Session Continuity Workflow

### End of Session
1. Run quick checks:
   ```bash
   uv run python src/transform.py
   uv run python main.py
   ```
2. Commit the distinct update
3. Append entry to `docs/WORKLOG.md`:
   - What changed
   - What is next
   - Blockers/questions

### Start of Session
1. Check recent history: `git log --oneline -n 10`
2. Check status: `git status`
3. Read `README.md` and latest `docs/WORKLOG.md` entry
4. Then start implementation

---

## Security & Configuration

- **Do not commit** personal financial exports beyond sample data
- Treat `data/raw/` as sensitive input; redact before sharing
- Never log or expose API keys/secrets in code
- Use environment variables for any credentials (not hardcoded)
