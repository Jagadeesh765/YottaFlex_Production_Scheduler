# YottaFlex Production Scheduler

A locally runnable production scheduling prototype built with Python, Pandas, SQLite and Streamlit. It assigns routing operations to eligible active machines, observes machine working calendars, checks demo material availability, accounts for product-to-product changeover rules, and produces CSV reports and a dashboard.

## Features
- Production-order prioritization by priority, due date and planned start date.
- Routing sequence enforcement within each order.
- Machine eligibility mapping and active-machine filtering.
- Machine-calendar slot allocation with non-overlapping bookings.
- Capacity-aware processing-time estimate for machines whose capacity unit is `PCS_PER_HOUR`.
- Product-transition changeover lookup.
- Demo BOM/inventory availability checks and in-run inventory reservation tracking.
- SQLite persistence and Streamlit dashboard.

## Requirements
- Python 3.10+
- Packages in `requirements.txt`

## Setup (Windows PowerShell)
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python src/schedule_engine.py
python src/save_schedule.py
python -m streamlit run dashboard/app.py
```
Open the local Streamlit URL printed in the terminal.

## Outputs
The scheduling engine writes CSV results under `outputs/`. The save script updates the SQLite database at `database/yottaflex.db`. The dashboard reads the saved scheduling results.

## Validation performed
The engine was run against the included synthetic dataset (500 orders / 10,000 operations). The latest run scheduled 780 operations and marked 9,220 unscheduled. The unscheduled reasons are written to `outputs/unscheduled_operations.csv`. This is a constraint-driven prototype result, not a claim that all orders can be manufactured.

## Assumptions and limitations
1. The included BOM is demonstration data generated for this project; it is not a verified factory bill of materials. Material shortage results must not be interpreted as real inventory conclusions.
2. Machine capacity is recorded as pieces per hour. The scheduler estimates capacity-based run time as `order_quantity / capacity * 60` and uses the larger of that estimate and the supplied nominal operation processing time. The source data does not state whether nominal processing time is per-piece or per-batch, so this is an explicit conservative modeling assumption that should be confirmed with the data owner.
3. The changeover matrix uses `TYPE_A`/`TYPE_B` labels, while the machine master uses physical machine types. The implementation therefore matches changeovers by the available from-product/to-product pair; the supplied matrix contains only a small number of transitions.
4. No worker/labor availability dataset is supplied. Labor shift capacity is therefore not enforced and must be added when worker/skill/shift data becomes available.
5. Due dates influence order priority but are not a hard feasibility constraint in this version.
6. Inventory reservations are tracked during a scheduling run; source inventory CSV quantities are not permanently decremented.
7. Machine routing compatibility is controlled by `MACHINE_MAPPING` in `src/schedule_engine.py` and should be validated with manufacturing stakeholders.

## Project structure
- `data/` synthetic input CSV files
- `src/` scheduling engine, data utilities and material checker
- `database/` SQLite schema and local database
- `dashboard/` Streamlit dashboard
- `outputs/` generated schedules and reports
- `docs/` supporting documentation
- `tests/` test area

## Responsible use of AI
AI assistance was used for debugging, code review, implementation suggestions and documentation support. The candidate must include the complete prompts submitted to every AI tool used, review the final code, and be prepared to explain and validate the scheduling logic. See `docs/AI_USAGE_DISCLOSURE_TEMPLATE.md` and complete it with the candidate's own full prompt history before submission.
