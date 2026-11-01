"""
validator.py - Conflict Detection & Constraint Validation Engine
Identifies:
- Missing brand coverage on operational days (CRITICAL)
- Missing process coverage (CRITICAL / WARNING)
- Insufficient employees against min_staff_req (WARNING)
- Employee marked working while on approved leave (CRITICAL)
- Working on designated weekly off without comp-off (WARNING)
- Overlapping assignments / multi-brand conflicts (WARNING)
- Recommends intelligent backup candidates for quick resolution
"""

import calendar
from datetime import datetime, date
from typing import List, Dict, Any, Optional
import database
from scheduler import is_brand_process_open


def detect_and_store_conflicts(roster_id: int, db_path: str = database.DB_PATH) -> Dict[str, Any]:
    """
    Validates all roster entries for a given roster against operating rules and availability constraints.
    Persists conflicts to SQLite and returns summary counts and conflict objects.
    """
    entries = database.get_roster_entries(roster_id, db_path)
    if not entries:
        database.save_conflicts(roster_id, [], db_path)
        return {"total": 0, "critical": 0, "warning": 0, "info": 0, "list": []}

    brands = {b["id"]: b for b in database.get_all_brands(db_path)}
    processes = {p["id"]: p for p in database.get_all_processes(db_path)}
    rules = database.get_all_rules(db_path)
    holidays = {h["holiday_date"]: h["name"] for h in database.get_all_holidays(db_path)}
    leaves = database.get_all_leaves(db_path)
    employees = {e["id"]: e for e in database.get_all_employees(db_path, active_only=False)}

    leave_map = {(l["employee_id"], l["leave_date"]): l for l in leaves if l["status"] == "APPROVED"}
    holiday_dates = set(holidays.keys())

    # Group entries by date and by (date, brand_id, process_id)
    entries_by_date = {}
    for entry in entries:
        entries_by_date.setdefault(entry["date"], []).append(entry)

    conflicts = []

    # Map rules by brand and process
    rule_map = {(r["brand_id"], r["process_id"]): r for r in rules}

    # Evaluate day by day
    for date_str, day_entries in sorted(entries_by_date.items()):
        current_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        day_name = current_date.strftime("%A")

        # -------------------------------------------------------------
        # 1. Coverage Validation for every configured Brand & Process Rule
        # -------------------------------------------------------------
        for (b_id, p_id), rule in rule_map.items():
            brand = brands.get(b_id)
            proc = processes.get(p_id)
            if not brand or not proc:
                continue

            op_pattern = rule["operating_pattern"]
            is_open = is_brand_process_open(op_pattern, current_date, holiday_dates)
            if not is_open:
                # Brand/Process is legitimately closed today; no coverage required
                continue

            min_req = rule.get("min_staff_req", 1)

            # Count employees WORKING on this brand and process on this date
            # Also account for single-resource brands: if the dedicated agent is working on that brand,
            # they handle all processes of that brand
            is_single = brand.get("is_single_resource", 0) == 1

            working_agents = []
            for e in day_entries:
                if e["status"] == "WORKING":
                    if is_single and e["brand_id"] == b_id:
                        working_agents.append(e)
                    elif e["brand_id"] == b_id and e["process_id"] == p_id:
                        working_agents.append(e)

            working_count = len(working_agents)

            if working_count == 0:
                conflicts.append({
                    "roster_id": roster_id,
                    "date": date_str,
                    "brand_id": b_id,
                    "process_id": p_id,
                    "employee_id": None,
                    "severity": "CRITICAL",
                    "conflict_type": "MISSING_COVERAGE",
                    "message": f"Zero coverage for '{brand['name']}' ({proc['code']}) on operational {day_name}.",
                    "suggested_fix": f"Reassign an available backup agent from {brand.get('pod_name', 'Pod')}."
                })
            elif working_count < min_req:
                conflicts.append({
                    "roster_id": roster_id,
                    "date": date_str,
                    "brand_id": b_id,
                    "process_id": p_id,
                    "employee_id": None,
                    "severity": "WARNING",
                    "conflict_type": "INSUFFICIENT_STAFFING",
                    "message": f"'{brand['name']}' ({proc['code']}) has {working_count}/{min_req} required staff on {day_name}.",
                    "suggested_fix": f"Assign {min_req - working_count} additional agent(s) to meet client SLA."
                })

        # -------------------------------------------------------------
        # 2. Individual Employee Availability & Constraint Validation
        # -------------------------------------------------------------
        # Track employee working count on this date to detect overlaps
        emp_working_shifts = {}

        for e in day_entries:
            emp_id = e["employee_id"]
            emp_info = employees.get(emp_id, {})
            status = e["status"]

            # A. Check for Working while on Approved Leave (CRITICAL)
            if status == "WORKING" and (emp_id, date_str) in leave_map:
                l_info = leave_map[(emp_id, date_str)]
                conflicts.append({
                    "roster_id": roster_id,
                    "date": date_str,
                    "brand_id": e["brand_id"],
                    "process_id": e["process_id"],
                    "employee_id": emp_id,
                    "severity": "CRITICAL",
                    "conflict_type": "UNAVAILABLE_WORKING",
                    "message": f"{emp_info.get('name', 'Employee')} is scheduled WORKING but has approved {l_info['leave_type']}.",
                    "suggested_fix": f"Relieve {emp_info.get('name')} for approved leave and allocate backup resource."
                })

            # B. Check for Working on Designated Weekly Off (WARNING)
            if status == "WORKING":
                is_off_day = (day_name == emp_info.get("weekly_off_day_1")) or (emp_info.get("weekly_off_day_2") and day_name == emp_info.get("weekly_off_day_2"))
                if is_off_day and not e.get("is_override"):
                    conflicts.append({
                        "roster_id": roster_id,
                        "date": date_str,
                        "brand_id": e["brand_id"],
                        "process_id": e["process_id"],
                        "employee_id": emp_id,
                        "severity": "WARNING",
                        "conflict_type": "OFF_DAY_WORKING",
                        "message": f"{emp_info.get('name')} is working on regular weekly off ({day_name}).",
                        "suggested_fix": "Compensate with an alternative weekly off day or approve comp-off credit."
                    })

                emp_working_shifts.setdefault(emp_id, []).append(e)

        # C. Check for Overlapping Shifts (WARNING)
        for emp_id, shifts in emp_working_shifts.items():
            if len(shifts) > 1:
                emp_name = employees.get(emp_id, {}).get("name", "Employee")
                brand_names = [brands.get(s["brand_id"], {}).get("name", "Unknown") for s in shifts]
                conflicts.append({
                    "roster_id": roster_id,
                    "date": date_str,
                    "brand_id": shifts[0]["brand_id"],
                    "process_id": shifts[0]["process_id"],
                    "employee_id": emp_id,
                    "severity": "WARNING",
                    "conflict_type": "OVERLAPPING_SHIFT",
                    "message": f"{emp_name} has multiple simultaneous working shifts across: {', '.join(brand_names)}.",
                    "suggested_fix": "De-conflict schedule or divide working hours explicitly."
                })

    # Save to database
    database.save_conflicts(roster_id, conflicts, db_path)

    critical_count = sum(1 for c in conflicts if c["severity"] == "CRITICAL")
    warning_count = sum(1 for c in conflicts if c["severity"] == "WARNING")
    info_count = sum(1 for c in conflicts if c["severity"] == "INFO")

    return {
        "total": len(conflicts),
        "critical": critical_count,
        "warning": warning_count,
        "info": info_count,
        "list": conflicts
    }


def get_backup_recommendations(brand_id: int, process_id: Optional[int], date_str: str,
                               roster_id: int, db_path: str = database.DB_PATH) -> List[Dict[str, Any]]:
    """
    Ranks and returns potential backup candidates for a given brand and date.
    Prioritizes:
    1. Assigned secondary / backup agents for this brand & process
    2. Agents within the same Pod who are free or have matching process skill
    3. Floating agents not tied to single-resource brands
    """
    brand = database.get_brand_by_id(brand_id, db_path)
    if not brand:
        return []

    pod_id = brand["pod_id"]
    all_employees = database.get_all_employees(db_path, active_only=True)
    all_assignments = database.get_all_assignments(db_path)
    leaves = database.get_all_leaves(db_path)
    roster_entries = database.get_roster_entries(roster_id, db_path)

    # Fast lookup for leave on this date
    leave_emp_ids = {l["employee_id"] for l in leaves if l["leave_date"] == date_str and l["status"] == "APPROVED"}

    # Employee status on this date in roster
    emp_day_status = {}
    for entry in roster_entries:
        if entry["date"] == date_str:
            emp_day_status[entry["employee_id"]] = entry

    # Assignment sets
    # Direct brand assignments:
    direct_brand_emps = {a["employee_id"]: a for a in all_assignments if a["brand_id"] == brand_id}
    # Process assignments:
    proc_emps = {a["employee_id"] for a in all_assignments if process_id and a["process_id"] == process_id}

    recommendations = []

    for emp in all_employees:
        emp_id = emp["id"]

        # Disqualify if employee is on approved leave
        if emp_id in leave_emp_ids:
            continue

        score = 50  # Base eligibility score
        reasons = []

        # Current status on this date
        entry = emp_day_status.get(emp_id)
        current_status = entry["status"] if entry else "UNKNOWN"
        current_brand_id = entry["brand_id"] if entry else None

        # Same pod bonus
        if emp["pod_id"] == pod_id:
            score += 25
            reasons.append(f"Same Pod ({emp['pod_name']})")
        else:
            reasons.append(f"Cross-Pod ({emp['pod_name']})")

        # Explicit backup or secondary assignment
        if emp_id in direct_brand_emps:
            score += 20
            reasons.append("Pre-assigned secondary backup for brand")

        # Process skill match
        if emp_id in proc_emps:
            score += 15
            reasons.append("Direct process skill match")

        # Status impact
        if current_status == "WEEKLY OFF":
            # Can be called for comp-off
            score += 10
            reasons.append("Currently on Weekly Off (Eligible for Comp-Off)")
        elif current_status == "WORKING":
            # Check if they are currently tied to a single-resource brand
            if current_brand_id:
                curr_brand = database.get_brand_by_id(current_brand_id, db_path)
                if curr_brand and curr_brand.get("is_single_resource"):
                    score -= 40
                    reasons.append(f"Already managing single-resource brand '{curr_brand['name']}'")
                else:
                    score -= 10
                    reasons.append(f"Working on multi-resource brand '{curr_brand['name'] if curr_brand else 'Other'}'")
        elif current_status == "HOLIDAY":
            score += 5
            reasons.append("Holiday off duty")

        recommendations.append({
            "employee_id": emp_id,
            "name": emp["name"],
            "role": emp["role"],
            "pod_name": emp["pod_name"],
            "current_status": current_status,
            "score": max(0, min(100, score)),
            "reason": " • ".join(reasons)
        })

    # Sort descending by score
    recommendations.sort(key=lambda x: x["score"], reverse=True)
    return recommendations


def resolve_conflict_reassign(roster_id: int, date_str: str, brand_id: int,
                              process_id: Optional[int], backup_employee_id: int,
                              notes: str = "Reassigned via Change Management",
                              db_path: str = database.DB_PATH) -> Dict[str, Any]:
    """
    Applies backup reassignment in the roster entries and re-evaluates conflicts.
    """
    entries = database.get_roster_entries(roster_id, db_path)

    # Check if backup employee already has an entry on this date
    existing_entry = None
    for e in entries:
        if e["date"] == date_str and e["employee_id"] == backup_employee_id:
            existing_entry = e
            break

    if existing_entry:
        database.update_roster_entry(
            entry_id=existing_entry["id"],
            status="WORKING",
            brand_id=brand_id,
            process_id=process_id,
            is_override=1,
            notes=notes,
            db_path=db_path
        )
    else:
        # Insert a new entry
        with database.get_connection(db_path) as conn:
            conn.execute("""
                INSERT INTO roster_entries (roster_id, employee_id, date, brand_id, process_id, status, is_override, notes)
                VALUES (?, ?, ?, ?, ?, 'WORKING', 1, ?)
            """, (roster_id, backup_employee_id, date_str, brand_id, process_id, notes))
            conn.commit()

    # Re-run conflict detection
    updated_conflicts = detect_and_store_conflicts(roster_id, db_path)
    return updated_conflicts
