# Final Validation Record

## Latest execution
Command: `python src/schedule_engine.py`

- Production orders processed: 500
- Total operations in input: 10,000
- Scheduled operations: 780
- Unscheduled operations: 9,220
- Scheduling rate: 7.80%

Unscheduled reason counts:
- Insufficient material: 5,580
- Previous operation was not scheduled: 3,458
- No available calendar slot: 182

Database persistence command: `python src/save_schedule.py`
Result: Database save successful; 780 scheduled and 9,220 unscheduled.

## Interpretation
The low scheduling rate is heavily affected by the synthetic demonstration BOM and inventory. It is not evidence that a real factory can only schedule 7.8% of its work. The candidate should explain this limitation and should not alter inventory/BOM values merely to create an artificially high scheduling rate.

## Remaining validation before operational use
- Confirm whether nominal operation processing time is per-piece or per-batch.
- Validate the machine-to-operation compatibility mapping.
- Obtain a real BOM and material reservation rules.
- Obtain worker/skill/shift availability to enforce labor constraints.
- Confirm whether due dates are hard constraints or scheduling priorities.
- Expand and validate changeover matrix coverage.
