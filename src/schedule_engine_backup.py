
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

MACHINE_MAPPING = {
    "Inspection": ["CNC"],
    "Packaging": ["Packaging"],
    "Assembly": ["Assembly"],
    "Painting": ["Painting"],
    "Drilling": ["CNC"],
    "Welding": ["Welding"],
    "Cutting": ["CNC"],
}


def load_data():
    files = [
        "production_orders",
        "operations",
        "machines",
        "machine_calendar",
        "routings",
        "products",
        "inventory_lots",
        "materials",
        "changeover_matrix",
    ]

    return {
        name: pd.read_csv(DATA_DIR / f"{name}.csv")
        for name in files
    }


def prepare_calendars(calendar_df):
    calendars = {}

    calendar_df = calendar_df.copy()
    calendar_df["calendar_date"] = pd.to_datetime(
        calendar_df["calendar_date"]
    )

    for _, row in calendar_df.iterrows():

        if int(row["is_working_day"]) != 1:
            continue

        day = row["calendar_date"].date()
        machine_id = row["machine_id"]

        start = datetime.combine(
            day,
            datetime.strptime(
                row["shift_start"], "%H:%M"
            ).time()
        )

        available_minutes = int(row["available_minutes"])

        end = start + timedelta(minutes=available_minutes)

        shift_end = datetime.combine(
            day,
            datetime.strptime(
                row["shift_end"], "%H:%M"
            ).time()
        )

        effective_end = min(end, shift_end)

        if effective_end > start:
            calendars.setdefault(machine_id, []).append({
                "start": start,
                "end": effective_end
            })

    for machine_id in calendars:
        calendars[machine_id].sort(
            key=lambda x: x["start"]
        )

    return calendars


def find_slot(
    machine_id,
    earliest_start,
    duration,
    calendars,
    machine_bookings
):

    bookings = sorted(
        machine_bookings.get(machine_id, []),
        key=lambda x: x["start"]
    )

    for shift in calendars.get(machine_id, []):

        candidate = max(
            shift["start"],
            earliest_start
        )

        shift_end = shift["end"]

        if candidate >= shift_end:
            continue

        for booking in bookings:

            if booking["end"] <= candidate:
                continue

            if booking["start"] >= shift_end:
                break

            proposed_end = candidate + timedelta(
                minutes=duration
            )

            if proposed_end <= booking["start"]:
                break

            candidate = max(
                candidate,
                booking["end"]
            )

        proposed_end = candidate + timedelta(
            minutes=duration
        )

        if proposed_end <= shift_end:
            return candidate, proposed_end

    return None, None


def schedule_operations(data):

    orders = data["production_orders"].copy()
    operations = data["operations"].copy()
    machines = data["machines"].copy()

    calendars = prepare_calendars(
        data["machine_calendar"]
    )

    machines = machines[
        machines["status"].astype(str).str.upper() == "ACTIVE"
    ].copy()

    machine_bookings = {}

    scheduled_rows = []
    unscheduled_rows = []
    order_completion = {}

    orders["planned_start_date"] = pd.to_datetime(
        orders["planned_start_date"]
    )

    orders["due_date"] = pd.to_datetime(
        orders["due_date"]
    )

    # Higher numerical priority is scheduled first.
    orders = orders.sort_values(
        ["priority", "due_date", "planned_start_date"],
        ascending=[False, True, True]
    )

    # Store total booked minutes for workload balancing.
    machine_workload = {
        machine_id: 0
        for machine_id in machines["machine_id"]
    }

    for _, order in orders.iterrows():

        order_id = order["production_order_id"]
        routing_id = order["routing_id"]

        order_operations = operations[
            operations["routing_id"] == routing_id
        ].sort_values("operation_sequence")

        previous_end = datetime.combine(
            order["planned_start_date"].date(),
            datetime.min.time()
        )

        predecessor_failed = False

        for _, operation in order_operations.iterrows():

            operation_id = operation["operation_id"]

            operation_name = str(
                operation["operation_name"]
            ).strip()

            sequence = operation["operation_sequence"]

            if predecessor_failed:

                unscheduled_rows.append({
                    "production_order_id": order_id,
                    "operation_id": operation_id,
                    "operation_name": operation_name,
                    "operation_sequence": sequence,
                    "reason": "Previous operation was not scheduled"
                })

                continue

            allowed_types = MACHINE_MAPPING.get(
                operation_name, []
            )

            eligible = machines[
                machines["machine_type"].isin(allowed_types)
            ]

            if eligible.empty:

                unscheduled_rows.append({
                    "production_order_id": order_id,
                    "operation_id": operation_id,
                    "operation_name": operation_name,
                    "operation_sequence": sequence,
                    "reason": "No compatible active machine found"
                })

                predecessor_failed = True
                continue

            setup_minutes = float(operation["setup_time"])
            processing_minutes = float(operation["processing_time"])

            total_duration = (
                setup_minutes + processing_minutes
            )

            best_machine = None
            best_start = None
            best_end = None
            best_score = None

            # Compare all eligible machines.
            for _, machine in eligible.iterrows():

                machine_id = machine["machine_id"]

                start, end = find_slot(
                    machine_id,
                    previous_end,
                    total_duration,
                    calendars,
                    machine_bookings
                )

                if start is None:
                    continue

                # Prefer earliest completion.
                # If completion is equal, prefer the
                # machine with lower existing workload.
                score = (
                    end,
                    machine_workload.get(machine_id, 0),
                    machine_id
                )

                if best_score is None or score < best_score:

                    best_score = score
                    best_machine = machine_id
                    best_start = start
                    best_end = end

            if best_machine is None:

                unscheduled_rows.append({
                    "production_order_id": order_id,
                    "operation_id": operation_id,
                    "operation_name": operation_name,
                    "operation_sequence": sequence,
                    "reason": "No available calendar slot"
                })

                predecessor_failed = True
                continue

            machine_capacity = float(
                eligible.loc[
                    eligible["machine_id"] == best_machine,
                    "capacity"
                ].iloc[0]
            )

            machine_bookings.setdefault(
                best_machine, []
            ).append({
                "start": best_start,
                "end": best_end,
                "production_order_id": order_id
            })

            machine_workload[best_machine] += total_duration

            scheduled_rows.append({

                "production_order_id": order_id,
                "product_id": order["product_id"],
                "routing_id": routing_id,
                "order_quantity": order["order_quantity"],

                "operation_id": operation_id,
                "operation_name": operation_name,
                "operation_sequence": sequence,

                "machine_id": best_machine,
                "machine_capacity": machine_capacity,

                "scheduled_start": best_start,
                "scheduled_end": best_end,

                "setup_duration": setup_minutes,
                "processing_duration": processing_minutes,
                "total_duration": total_duration,

                "schedule_status": "SCHEDULED"
            })

            previous_end = best_end

        order_completion[order_id] = previous_end

    return scheduled_rows, unscheduled_rows, order_completion


def save_results(scheduled, unscheduled, completion):

    scheduled_df = pd.DataFrame(scheduled)
    unscheduled_df = pd.DataFrame(unscheduled)

    scheduled_df.to_csv(
        OUTPUT_DIR / "operation_schedule.csv",
        index=False
    )

    unscheduled_df.to_csv(
        OUTPUT_DIR / "unscheduled_operations.csv",
        index=False
    )

    summary = {
        "total_scheduled_operations": len(scheduled_df),
        "total_unscheduled_operations": len(unscheduled_df),
        "orders_processed": len(completion)
    }

    pd.DataFrame([summary]).to_csv(
        OUTPUT_DIR / "schedule_summary.csv",
        index=False
    )

    print("\n========== SCHEDULING RESULT ==========")

    print(
        "Scheduled operations:",
        summary["total_scheduled_operations"]
    )

    print(
        "Unscheduled operations:",
        summary["total_unscheduled_operations"]
    )

    print(
        "Orders processed:",
        summary["orders_processed"]
    )

    if not scheduled_df.empty:

        print("\nMachine utilization workload:")

        print(
            scheduled_df.groupby("machine_id")[
                "total_duration"
            ].sum().sort_values(ascending=False).to_string()
        )

    print("\nOutput folder:", OUTPUT_DIR)


def main():

    print("Loading production scheduling data...")

    data = load_data()

    print("Running improved scheduling engine...")

    scheduled, unscheduled, completion = schedule_operations(data)

    save_results(
        scheduled,
        unscheduled,
        completion
    )


if __name__ == "__main__":
    main()
