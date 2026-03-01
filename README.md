# My Money Dashboard

Personal finance dashboard built with Streamlit.

## Project Purpose
- Track expenses: understand where money is being spent.
- Track cashflow and account allocation: see where assets are stored.
- Plan ahead: compare budget vs actual and improve decisions.

## Roadmap
Build in small vertical slices, with each step as a clean git stopping point.

1. Data contract freeze  
- Goal: define and enforce canonical transaction schema (types, transfer rules, required columns).
- Commit: `define canonical transaction schema and validation checks`
- Stop when: app still runs and schema is documented in code/README.

2. Account balance engine (core)  
- Goal: compute running balance per account from transactions.
- Commit: `add running balance calculation per account`
- Stop when: generated dataframe includes `account`, `date`, `balance`.

3. Account views in UI  
- Goal: show where assets are stored.
- Commit: `add account balance timeline and allocation charts`
- Stop when: dashboard shows current allocation + account balance timeline.

4. Transfer integrity pass  
- Goal: make transfer handling robust and prevent KPI double-counting.
- Commit: `normalize transfer handling in metrics and charts`
- Stop when: totals reconcile across account-level and global cashflow views.

5. Budget data model  
- Goal: add `budgets.csv` and loader/helpers.
- Commit: `add budget model and budget data loader`
- Stop when: budget data loads with schema validation.

6. Budget vs actual MVP UI  
- Goal: show variance between category budgets and actual expenses.
- Commit: `add budget vs actual variance dashboard`
- Stop when: table + chart show over/under-spend by category.

7. Planning v1  
- Goal: add a simple end-of-month projection.
- Commit: `add basic monthly spend projection`
- Stop when: projected spend vs budget is visible for decision-making.

## Current Capability
- Imports and normalizes raw CSV exports into canonical `data/transactions.csv`.
- Enforces canonical transaction schema and validation checks in transform pipeline.
- Provides a Streamlit dashboard with:
  - timeline filters (`YTD`, `FYTD`, `Last 1/3/6/12M`, `MTD`, `All Time`, custom range)
  - type filter (`Income`, `Expense`, `Transfer`)
  - KPI cards (income, expenses, net)
  - monthly income vs expense chart
  - spending by category chart
  - transaction log table

## Canonical Transaction Schema
The cleaned dataset (`data/transactions.csv`) contains:
- `datetime` (`datetime64[ns]`)
- `type` (`Income` / `Expense` / `Transfer`)
- `amount` (positive numeric value)
- `category` (string)
- `account` (string)
- `notes` (string, may be empty)
- `date` (`YYYY-MM-DD`)
- `month` (1-12)
- `year` (4-digit year)
- `day` (1-31)
- `signed_amount` (Income positive, Expense negative, Transfer 0)
- `is_opening_balance` (boolean)
