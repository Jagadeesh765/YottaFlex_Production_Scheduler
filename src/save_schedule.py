
import sqlite3
import pandas as pd
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent

conn = sqlite3.connect(BASE / "database" / "yottaflex.db")

schedule = pd.read_csv(BASE / "outputs" / "operation_schedule.csv")
unscheduled = pd.read_csv(BASE / "outputs" / "unscheduled_operations.csv")

schedule.to_sql("ScheduledOperationResult", conn, if_exists="replace", index=False)
unscheduled.to_sql("UnscheduledOperationResult", conn, if_exists="replace", index=False)

print("Database save successful!")
print("Scheduled:", len(schedule))
print("Unscheduled:", len(unscheduled))

conn.close()
