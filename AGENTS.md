# Repository Guidelines

## Project Structure & Module Organization
- `app.py`: Main Streamlit dashboard entrypoint.
- `src/transform.py`: Raw CSV ingestion and normalization pipeline; writes `data/transactions.csv`.
- `src/helpers.py`: Shared data-loading utilities (including Streamlit cache).
- `data/raw/`: Drop source exports here (`*.csv`).
- `data/transactions.csv`: Canonical cleaned dataset consumed by the app.
- `pages/`: Reserved for multi-page Streamlit views.

Keep business logic in `src/` and keep UI code in `app.py` (or `pages/` as the app grows).

## Build, Test, and Development Commands
- `uv sync`: Install and lock dependencies from `pyproject.toml` / `uv.lock`.
- `uv run streamlit run app.py`: Launch the dashboard locally.
- `uv run python src/transform.py`: Rebuild/append the master transactions dataset from `data/raw/*.csv`.
- `uv run python main.py`: Minimal runtime sanity check.

Run transform before launching the app if raw files changed.

## Coding Style & Naming Conventions
- Python 3.12+, 4-space indentation, UTF-8.
- Use `snake_case` for functions/variables, `UPPER_SNAKE_CASE` for module constants (for example `MASTER_CSV`).
- Prefer small, single-purpose functions in `src/`.
- Add type hints on public functions and return values where practical.
- Keep comments brief and intent-focused (explain why, not obvious syntax).
- Write code comments in a concise teaching style: assume a learner with rudimentary Python knowledge, explain key Streamlit/pandas decisions, and avoid overly verbose commentary.

## Testing Guidelines
- No automated test suite is committed yet.
- For new logic in `src/`, add `pytest` tests under `tests/` using `test_<module>.py` naming.
- Minimum expectation for data transforms: validate column mapping, datetime parsing, and `signed_amount` behavior.
- Before opening a PR, manually verify:
  - `uv run python src/transform.py`
  - `uv run streamlit run app.py`

## Commit & Pull Request Guidelines
- Current history uses short, plain-English commit subjects (for example: `initial project setup`).
- Prefer concise, imperative subjects under ~72 chars, one concern per commit.
- PRs should include:
  - What changed and why.
  - Any data/model assumptions.
  - UI screenshots/GIFs for dashboard changes.
  - Steps used to validate locally.

## Security & Configuration Tips
- Do not commit personal financial exports beyond intended sample data.
- Treat `data/raw/` as sensitive input; redact before sharing.
