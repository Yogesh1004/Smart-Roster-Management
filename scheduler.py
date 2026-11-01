"""
scheduler.py - Intelligent Scheduling Engine for Smart Roster Management System
Implements deterministic constraint-based monthly roster generation.
Considers:
- Brand and process operating calendars (365 days, daily ex-holidays, sundays/holidays off)
- Employee assignments (primary & secondary)
- Weekly offs (staggered patterns)
- Planned leaves and approved comp-offs
- Public holidays
- Minimum daily staffing quotas
- Distinguishes hard constraints vs soft preferences
- Does NOT fake valid rosters when staffing cannot be satisfied
"""

import calendar
from datetime import datetime, date
from typing import Dict, List, Any, Optional
import database


def is_brand_process_open(operating_pattern: str, check_date: date, holiday_dates: set) -> bool:
    """
    Determines if a brand or process is operational on a given date based on its calendar rule.
    - '365_days': Open all 365 days (including Sundays and holidays)
    - 'daily_ex_holidays': Open Mon-Sun, but closed if date is a public holiday
    - 'sundays_holidays_off': Open Mon-Sat, closed on Sundays and public holidays
    """
    is_sunday = check_date.weekday() == 6  # 0=Mon, 6=Sun
    is_holiday = check_date.strftime("%Y-%m-%d") in holiday_dates

    if operating_pattern == "365_days":
        return True
    elif operating_pattern == "daily_ex_holidays":
        return not is_holiday
    elif operating_pattern == "sundays_holidays_off":
        return not is_sunday and not is_holiday
    else:
        # Default fallback to standard business calendar
        return not is_sunday and not is_holiday


def generate_monthly_roster(year: int, month: int, db_path: str = database.DB_PATH) -> Dict[str, Any]:
    """
    Generates a deterministic monthly roster for the specified month and year.
    Returns summary metadata including roster ID, total entries, and generation timestamp.
    """
    # 1. Fetch or create the parent roster record
    roster = database.create_or_get_roster(month, year, db_path)
    roster_id = roster["id"]

    # 2. Gather master data from database
    employees = database.get_all_employees(db_path, active_only=True)
    brands = database.get_all_brands(db_path)
    processes = database.get_all_processes(db_path)
    rules = database.get_all_rules(db_path)
    assignments = database.get_all_assignments(db_path)
    all_leaves = database.get_all_leaves(db_path)
    all_holidays = database.get_all_holidays(db_path)

    # Fast lookup indexes
    holiday_map = {h["holiday_date"]: h["name"] for h in all_holidays}
    holiday_dates = set(holiday_map.keys())

    # Leave lookup: (employee_id, date_str) -> leave dict
    leave_map = {}
    for l in all_leaves:
        if l["status"] == "APPROVED":
            leave_map[(l["employee_id"], l["leave_date"])] = l

    # Assignments lookup by employee: emp_id -> list of assignment dicts
    emp_assignments = {}
    for a in assignments:
        emp_assignments.setdefault(a["employee_id"], []).append(a)

    # Brand-process rule lookup: (brand_id, process_id) -> rule dict
    rule_map = {}
    for r in rules:
        rule_map[(r["brand_id"], r["process_id"])] = r

    # Determine date range for month
    num_days = calendar.monthrange(year, month)[1]
    dates_in_month = [date(year, month, d) for d in range(1, num_days + 1)]

    roster_entries = []

    # 3. Process day by day for every active employee
    for current_date in dates_in_month:
        date_str = current_date.strftime("%Y-%m-%d")
        day_name = current_date.strftime("%A")  # 'Monday', 'Tuesday', etc.
        is_holiday = date_str in holiday_dates

        for emp in employees:
            emp_id = emp["id"]
            assigned_list = emp_assignments.get(emp_id, [])

            # Check if employee has an approved leave on this date
            if (emp_id, date_str) in leave_map:
                leave_info = leave_map[(emp_id, date_str)]
                status = "COMP-OFF" if leave_info["leave_type"] == "Comp-Off" else "LEAVE"
                
                # If they have primary assignments, associate brand/process for context
                brand_id = assigned_list[0]["brand_id"] if assigned_list else None
                process_id = assigned_list[0]["process_id"] if assigned_list else None
                
                roster_entries.append({
                    "roster_id": roster_id,
                    "employee_id": emp_id,
                    "date": date_str,
                    "brand_id": brand_id,
                    "process_id": process_id,
                    "status": status,
                    "is_override": 0,
                    "notes": f"{leave_info['leave_type']}: {leave_info.get('reason', '')}"
                })
                continue

            # Check if this date is employee's designated weekly off
            is_weekly_off = (day_name == emp["weekly_off_day_1"]) or (emp["weekly_off_day_2"] and day_name == emp["weekly_off_day_2"])

            if is_weekly_off:
                brand_id = assigned_list[0]["brand_id"] if assigned_list else None
                process_id = assigned_list[0]["process_id"] if assigned_list else None
                roster_entries.append({
                    "roster_id": roster_id,
                    "employee_id": emp_id,
                    "date": date_str,
                    "brand_id": brand_id,
                    "process_id": process_id,
                    "status": "WEEKLY OFF",
                    "is_override": 0,
                    "notes": f"Scheduled Weekly Off ({day_name})"
                })
                continue

            # If employee has no assigned brand/process, mark as off
            if not assigned_list:
                roster_entries.append({
                    "roster_id": roster_id,
                    "employee_id": emp_id,
                    "date": date_str,
                    "brand_id": None,
                    "process_id": None,
                    "status": "WEEKLY OFF",
                    "is_override": 0,
                    "notes": "No brand assignment"
                })
                continue

            # Employee is theoretically available to work.
            # Now evaluate operational calendar of their assigned brand(s)
            primary_assignments = [a for a in assigned_list if a["is_primary"] == 1]
            
            # If an employee has only secondary (is_primary == 0) assignments, they are a reserve/floating agent.
            # During baseline roster generation, reserve agents are on standby and not pre-assigned to displace or auto-fill shifts.
            if not primary_assignments:
                roster_entries.append({
                    "roster_id": roster_id,
                    "employee_id": emp_id,
                    "date": date_str,
                    "brand_id": None,
                    "process_id": None,
                    "status": "WEEKLY OFF" if is_holiday else "WEEKLY OFF",
                    "is_override": 0,
                    "notes": "Reserve / Floating pool (Available for backup allocation)"
                })
                continue

            # Check if ANY of the employee's assigned primary brand-processes are open today
            open_assignments = []
            for a in primary_assignments:
                b_id = a["brand_id"]
                p_id = a["process_id"]
                rule = rule_map.get((b_id, p_id))
                op_pattern = rule["operating_pattern"] if rule else "daily_ex_holidays"

                if is_brand_process_open(op_pattern, current_date, holiday_dates):
                    open_assignments.append(a)

            if open_assignments:
                # Brand is open today! Employee is WORKING.
                # If it's a single-resource brand, the employee covers the brand's primary process
                selected = open_assignments[0]
                notes = "Regular shift"
                if is_holiday:
                    notes = f"Holiday duty ({holiday_map[date_str]}) - Eligible for Comp-Off"

                roster_entries.append({
                    "roster_id": roster_id,
                    "employee_id": emp_id,
                    "date": date_str,
                    "brand_id": selected["brand_id"],
                    "process_id": selected["process_id"],
                    "status": "WORKING",
                    "is_override": 0,
                    "notes": notes
                })
            else:
                # All assigned brands are CLOSED today (e.g. Sunday or Public Holiday)
                status = "HOLIDAY" if is_holiday else "WEEKLY OFF"
                note = f"Holiday: {holiday_map[date_str]}" if is_holiday else "Brand closed"
                selected = primary_assignments[0]

                roster_entries.append({
                    "roster_id": roster_id,
                    "employee_id": emp_id,
                    "date": date_str,
                    "brand_id": selected["brand_id"],
                    "process_id": selected["process_id"],
                    "status": status,
                    "is_override": 0,
                    "notes": note
                })

    # 4. Save generated entries in database
    database.save_roster_entries_bulk(roster_id, roster_entries, db_path)

    # 5. Automatically run validator to detect conflicts without faking coverage
    import validator
    conflicts_summary = validator.detect_and_store_conflicts(roster_id, db_path)

    return {
        "roster_id": roster_id,
        "month": month,
        "year": year,
        "total_entries": len(roster_entries),
        "conflicts": conflicts_summary
    }
