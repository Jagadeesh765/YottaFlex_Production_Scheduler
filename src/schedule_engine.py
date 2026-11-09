
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from material_checker import check_order_materials

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

    data = {}

    for name in files:
        file_path = DATA_DIR / f"{name}.csv"

        if not file_path.exists():
            raise FileNotFoundError(
                f"Required file not found: {file_path}"
            )

        data[name] = pd.read_csv(file_path)

    return data


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

        shift_end = datetime.combine(
            day,
            datetime.strptime(
                row["shift_end"], "%H:%M"
            ).time()
        )

        available_minutes = max(
            0, int(row["available_minutes"])
        )

        end = start + timedelta(
            minutes=available_minutes
        )

        effective_end = min(end, shift_end)

        if effective_end > start:
            calendars.setdefault(
                machine_id, []
            ).append({
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


def get_changeover_minutes(
    changeovers,
    previous_booking,
    product_id,
    machine_type
):
    if previous_booking is None:
        return 0.0

    required_columns = [
        "from_product_id",
        "to_product_id",
        "from_machine_type",
        "to_machine_type",
        "changeover_minutes"
    ]

    if not all(
        column in changeovers.columns
        for column in required_columns
    ):
        return 0.0

    # The supplied changeover file uses TYPE_A/TYPE_B labels, while the
    # machine master uses physical types such as CNC and Assembly. Therefore
    # match the product transition (the meaningful shared keys) and do not
    # incorrectly compare those two different type vocabularies.
    match = changeovers[
        (changeovers["from_product_id"] ==
         previous_booking["product_id"]) &
        (changeovers["to_product_id"] == product_id)
    ]

    if match.empty:
        return 0.0

    return max(
        0.0,
        float(match.iloc[0]["changeover_minutes"])
    )


def find_machine_slot(
    machine_id,
    earliest_start,
    base_duration,
    product_id,
    machine_type,
    changeovers,
    calendars,
    machine_bookings
):
    changeover_minutes = 0.0
    start = None
    end = None

    # Recalculate when the candidate moves past an existing booking.
    for _ in range(10):

        start, end = find_slot(
            machine_id,
            earliest_start,
            base_duration + changeover_minutes,
            calendars,
            machine_bookings
        )

        if start is None:
            return None, None, 0.0

        earlier_bookings = [
            booking
            for booking in machine_bookings.get(
                machine_id, []
            )
            if booking["end"] <= start
        ]

        previous_booking = None

        if earlier_bookings:
            previous_booking = max(
                earlier_bookings,
                key=lambda x: x["end"]
            )

        new_changeover = get_changeover_minutes(
            changeovers,
            previous_booking,
            product_id,
            machine_type
        )

        if abs(
            new_changeover - changeover_minutes
        ) < 0.001:
            return start, end, changeover_minutes

        changeover_minutes = new_changeover

    return start, end, changeover_minutes


def schedule_operations(data):

    orders = data["production_orders"].copy()
    operations = data["operations"].copy()
    machines = data["machines"].copy()
    changeovers = data["changeover_matrix"].copy()

    calendars = prepare_calendars(
        data["machine_calendar"]
    )

    machines = machines[
        machines["status"].astype(str).str.upper() == "ACTIVE"
    ].copy()

    machine_bookings = {}
    machine_workload = {
        machine_id: 0
        for machine_id in machines["machine_id"]
    }

    scheduled_rows = []
    unscheduled_rows = []
    order_completion = {}

    # Track material quantities committed to earlier orders.
    reserved_inventory = {}

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

    for _, order in orders.iterrows():

        order_id = order["production_order_id"]
        routing_id = order["routing_id"]
        product_id = order["product_id"]

        order_operations = operations[
            operations["routing_id"] == routing_id
        ].sort_values("operation_sequence")

        previous_end = datetime.combine(
            order["planned_start_date"].date(),
            datetime.min.time()
        )

        if order_operations.empty:
            order_completion[order_id] = previous_end
            continue

        # MATERIAL AVAILABILITY CHECK
        material_results = check_order_materials(order_id)

        if isinstance(material_results, dict):
            material_results = [material_results]

        # Check material quantities against previous reservations.
        unavailable_materials = []

        for item in material_results:

            material_id = item.get("material_id")

            required = float(
                item.get("required_quantity", 0)
            )

            available = float(
                item.get("available_quantity", 0)
            )

            already_reserved = reserved_inventory.get(
                material_id, 0
            )

            if available - already_reserved < required:
                unavailable_materials.append(item)

        if unavailable_materials:

            for _, operation in order_operations.iterrows():

                unscheduled_rows.append({
                    "production_order_id": order_id,
                    "operation_id": operation["operation_id"],
                    "operation_name": operation["operation_name"],
                    "operation_sequence": operation["operation_sequence"],
                    "reason": "Insufficient material"
                })

            order_completion[order_id] = previous_end
            continue

        # Keep temporary changes until the complete order succeeds.
        temporary_scheduled = []
        temporary_bookings = []
        temporary_workload = {}

        predecessor_failed = False

        for _, operation in order_operations.iterrows():

            operation_id = operation["operation_id"]

            operation_name = str(
                operation["operation_name"]
            ).strip()

            sequence = operation["operation_sequence"]

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
                break

            setup_minutes = float(operation["setup_time"])
            nominal_processing_minutes = float(
                operation["processing_time"]
            )

            # Capacity is expressed as pieces/hour. Use it to calculate the
            # minimum run time for this order quantity. Keep the supplied
            # processing estimate as a lower bound because its dataset
            # semantics do not specify whether it is per-piece or per-batch.
            base_duration = setup_minutes

            best_machine = None
            best_start = None
            best_end = None
            best_changeover = 0.0
            best_processing_minutes = nominal_processing_minutes
            best_score = None

            for _, machine in eligible.iterrows():

                machine_id = machine["machine_id"]
                machine_type = machine["machine_type"]

                machine_capacity_value = float(machine["capacity"])
                capacity_unit = str(machine.get("capacity_unit", "")).upper()
                if capacity_unit == "PCS_PER_HOUR" and machine_capacity_value > 0:
                    capacity_minutes = (
                        float(order["order_quantity"]) / machine_capacity_value
                    ) * 60.0
                    processing_minutes = max(
                        nominal_processing_minutes, capacity_minutes
                    )
                else:
                    processing_minutes = nominal_processing_minutes

                operation_duration = setup_minutes + processing_minutes

                start, end, changeover_minutes = (
                    find_machine_slot(
                        machine_id,
                        previous_end,
                        operation_duration,
                        product_id,
                        machine_type,
                        changeovers,
                        calendars,
                        machine_bookings
                    )
                )

                if start is None:
                    continue

                score = (
                    end,
                    machine_workload.get(machine_id, 0)
                    + temporary_workload.get(machine_id, 0),
                    machine_id
                )

                if best_score is None or score < best_score:

                    best_score = score
                    best_machine = machine_id
                    best_start = start
                    best_end = end
                    best_changeover = changeover_minutes
                    best_processing_minutes = processing_minutes

            if best_machine is None:

                unscheduled_rows.append({
                    "production_order_id": order_id,
                    "operation_id": operation_id,
                    "operation_name": operation_name,
                    "operation_sequence": sequence,
                    "reason": "No available calendar slot"
                })

                predecessor_failed = True
                break

            machine_capacity = float(
                eligible.loc[
                    eligible["machine_id"] == best_machine,
                    "capacity"
                ].iloc[0]
            )

            booking = {
                "start": best_start,
                "end": best_end,
                "production_order_id": order_id,
                "product_id": product_id
            }

            machine_bookings.setdefault(
                best_machine, []
            ).append(booking)

            temporary_bookings.append(
                (best_machine, booking)
            )

            total_duration = (
                setup_minutes + best_processing_minutes + best_changeover
            )

            temporary_workload[best_machine] = (
                temporary_workload.get(best_machine, 0)
                + total_duration
            )

            temporary_scheduled.append({

                "production_order_id": order_id,
                "product_id": product_id,
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
                "processing_duration": best_processing_minutes,
                "changeover_duration": best_changeover,
                "total_duration": total_duration,

                "schedule_status": "SCHEDULED"
            })

            previous_end = best_end

        if predecessor_failed:

            # Roll back all machine bookings for this incomplete order.
            for machine_id, booking in temporary_bookings:
                machine_bookings[machine_id].remove(
                    booking
                )

            for _, operation in order_operations.iterrows():

                already_recorded = any(
                    row["operation_id"] == operation["operation_id"]
                    and row["production_order_id"] == order_id
                    for row in unscheduled_rows
                )

                already_scheduled = any(
                    row["operation_id"] == operation["operation_id"]
                    and row["production_order_id"] == order_id
                    for row in scheduled_rows
                )

                if not already_recorded and not already_scheduled:

                    unscheduled_rows.append({
                        "production_order_id": order_id,
                        "operation_id": operation["operation_id"],
                        "operation_name": operation["operation_name"],
                        "operation_sequence": operation["operation_sequence"],
                        "reason": "Previous operation was not scheduled"
                    })

            order_completion[order_id] = datetime.combine(
                order["planned_start_date"].date(),
                datetime.min.time()
            )

            continue

        # Commit the complete order's schedule and workload.
        scheduled_rows.extend(temporary_scheduled)

        for machine_id, minutes in temporary_workload.items():
            machine_workload[machine_id] += minutes

        # Commit material reservations only after full order scheduling.
        for item in material_results:

            material_id = item.get("material_id")

            required = float(
                item.get("required_quantity", 0)
            )

            reserved_inventory[material_id] = (
                reserved_inventory.get(material_id, 0)
                + required
            )

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

        print("\nMachine workload in minutes:")

        print(
            scheduled_df.groupby("machine_id")[
                "total_duration"
            ].sum().sort_values(
                ascending=False
            ).to_string()
        )

    if not unscheduled_df.empty:

        print("\nUnscheduled reasons:")

        print(
            unscheduled_df["reason"].value_counts().to_string()
        )

    print("\nOutput folder:", OUTPUT_DIR)


def main():

    print("Loading production scheduling data...")

    data = load_data()

    print("Running production scheduling engine...")

    scheduled, unscheduled, completion = schedule_operations(
        data
    )

    save_results(
        scheduled,
        unscheduled,
        completion
    )


if __name__ == "__main__":
    main()
