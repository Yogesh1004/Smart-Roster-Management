"""
exporter.py - Multi-format Report & Excel/CSV Exporter
Generates styled Excel workbooks (.xlsx) using openpyxl and CSV exports for rosters,
coverage matrices, conflicts, and employee statistics.
"""

import io
import calendar
from datetime import datetime, date
import pandas as pd
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
import database


def export_roster_to_excel(roster_id: int, month: int, year: int, db_path: str = database.DB_PATH) -> bytes:
    """
    Generates a beautifully styled, multi-sheet Excel workbook:
    1. Monthly Roster Matrix (Color-coded cells per status)
    2. Brand Daily Coverage Analysis
    3. Conflict & Compliance Log
    4. Employee Attendance & KPI Summary
    """
    wb = openpyxl.Workbook()
    
    # -------------------------------------------------------------
    # Styling Definitions
    # -------------------------------------------------------------
    font_title = Font(name="Segoe UI", size=14, bold=True, color="1E3A8A")
    font_header = Font(name="Segoe UI", size=10, bold=True, color="FFFFFF")
    font_bold = Font(name="Segoe UI", size=10, bold=True)
    font_regular = Font(name="Segoe UI", size=10)
    
    fill_header = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
    fill_sub_header = PatternFill(start_color="3B82F6", end_color="3B82F6", fill_type="solid")
    
    # Status fills
    status_fills = {
        "WORKING": PatternFill(start_color="DCFCE7", end_color="DCFCE7", fill_type="solid"),     # Soft Green
        "WEEKLY OFF": PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid"),  # Slate Gray
        "LEAVE": PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid"),       # Soft Red
        "HOLIDAY": PatternFill(start_color="FEF3C7", end_color="FEF3C7", fill_type="solid"),     # Soft Amber
        "COMP-OFF": PatternFill(start_color="CCFBF1", end_color="CCFBF1", fill_type="solid"),    # Teal
    }
    
    status_fonts = {
        "WORKING": Font(name="Segoe UI", size=9, color="166534", bold=True),
        "WEEKLY OFF": Font(name="Segoe UI", size=9, color="475569"),
        "LEAVE": Font(name="Segoe UI", size=9, color="991B1B", bold=True),
        "HOLIDAY": Font(name="Segoe UI", size=9, color="92400E", bold=True),
        "COMP-OFF": Font(name="Segoe UI", size=9, color="115E59", bold=True),
    }

    thin_border = Border(
        left=Side(style='thin', color='E2E8F0'),
        right=Side(style='thin', color='E2E8F0'),
        top=Side(style='thin', color='E2E8F0'),
        bottom=Side(style='thin', color='E2E8F0')
    )
    
    align_center = Alignment(horizontal="center", vertical="center")
    align_left = Alignment(horizontal="left", vertical="center")

    num_days = calendar.monthrange(year, month)[1]
    month_name = calendar.month_name[month]

    # =============================================================
    # SHEET 1: Monthly Roster Matrix
    # =============================================================
    ws1 = wb.active
    ws1.title = "Monthly Roster"
    ws1.views.sheetView[0].showGridLines = True

    # Title Banner
    ws1.merge_cells("A1:G1")
    ws1["A1"] = f"Smart Roster Management System — {month_name} {year}"
    ws1["A1"].font = font_title

    # Header Row
    headers = ["Employee Name", "Pod", "Role"] + [f"Day {d}" for d in range(1, num_days + 1)]
    for col_idx, h in enumerate(headers, 1):
        cell = ws1.cell(row=3, column=col_idx, value=h)
        cell.font = font_header
        cell.fill = fill_header
        cell.alignment = align_center if col_idx > 3 else align_left
        cell.border = thin_border

    entries = database.get_roster_entries(roster_id, db_path)
    
    # Pivot entries: {emp_name: {day: status}}
    emp_meta = {}
    matrix = {}
    for e in entries:
        emp_name = e["employee_name"]
        emp_meta[emp_name] = (e["employee_pod_name"], e["employee_role"])
        day = int(e["date"].split("-")[2])
        matrix.setdefault(emp_name, {})[day] = e["status"]

    current_row = 4
    for emp_name in sorted(matrix.keys()):
        pod_name, role = emp_meta[emp_name]
        ws1.cell(row=current_row, column=1, value=emp_name).font = font_bold
        ws1.cell(row=current_row, column=1).border = thin_border
        
        ws1.cell(row=current_row, column=2, value=pod_name).font = font_regular
        ws1.cell(row=current_row, column=2).border = thin_border

        ws1.cell(row=current_row, column=3, value=role).font = font_regular
        ws1.cell(row=current_row, column=3).border = thin_border

        for day in range(1, num_days + 1):
            st = matrix[emp_name].get(day, "OFF")
            c = ws1.cell(row=current_row, column=3 + day, value=st)
            c.border = thin_border
            c.alignment = align_center
            if st in status_fills:
                c.fill = status_fills[st]
                c.font = status_fonts[st]
            else:
                c.font = font_regular

        current_row += 1

    # Auto-adjust column widths
    ws1.column_dimensions["A"].width = 24
    ws1.column_dimensions["B"].width = 20
    ws1.column_dimensions["C"].width = 16
    for d in range(1, num_days + 1):
        col_letter = get_column_letter(3 + d)
        ws1.column_dimensions[col_letter].width = 13

    # =============================================================
    # SHEET 2: Brand Daily Coverage Analysis
    # =============================================================
    ws2 = wb.create_sheet(title="Brand Daily Coverage")
    ws2.views.sheetView[0].showGridLines = True
    
    ws2.merge_cells("A1:E1")
    ws2["A1"] = f"Brand & Process Daily Staffing Coverage — {month_name} {year}"
    ws2["A1"].font = font_title

    headers_b = ["Brand Name", "Process", "Type", "Min Required"] + [f"Day {d}" for d in range(1, num_days + 1)]
    for col_idx, h in enumerate(headers_b, 1):
        cell = ws2.cell(row=3, column=col_idx, value=h)
        cell.font = font_header
        cell.fill = fill_sub_header
        cell.alignment = align_center if col_idx > 3 else align_left
        cell.border = thin_border

    brands = database.get_all_brands(db_path)
    rules = database.get_all_rules(db_path)
    
    # Calculate daily count for each rule
    current_row = 4
    for r in rules:
        b_name = r["brand_name"]
        p_code = r["process_code"]
        op_pat = r["operating_pattern"]
        min_req = r["min_staff_req"]
        
        ws2.cell(row=current_row, column=1, value=b_name).font = font_bold
        ws2.cell(row=current_row, column=1).border = thin_border
        
        ws2.cell(row=current_row, column=2, value=p_code).font = font_regular
        ws2.cell(row=current_row, column=2).border = thin_border

        ws2.cell(row=current_row, column=3, value=op_pat).font = font_regular
        ws2.cell(row=current_row, column=3).border = thin_border

        ws2.cell(row=current_row, column=4, value=min_req).font = font_bold
        ws2.cell(row=current_row, column=4).border = thin_border
        ws2.cell(row=current_row, column=4).alignment = align_center

        for d in range(1, num_days + 1):
            date_str = f"{year}-{month:02d}-{d:02d}"
            # Count working staff
            working_cnt = sum(
                1 for e in entries 
                if e["date"] == date_str and e["status"] == "WORKING" and (
                    e["brand_id"] == r["brand_id"] and e["process_id"] == r["process_id"]
                )
            )
            c = ws2.cell(row=current_row, column=4 + d, value=working_cnt)
            c.border = thin_border
            c.alignment = align_center
            if working_cnt >= min_req:
                c.fill = status_fills["WORKING"]
                c.font = status_fonts["WORKING"]
            elif working_cnt == 0:
                c.fill = status_fills["LEAVE"]
                c.font = status_fonts["LEAVE"]
            else:
                c.fill = status_fills["HOLIDAY"]
                c.font = status_fonts["HOLIDAY"]

        current_row += 1

    ws2.column_dimensions["A"].width = 26
    ws2.column_dimensions["B"].width = 12
    ws2.column_dimensions["C"].width = 22
    ws2.column_dimensions["D"].width = 14
    for d in range(1, num_days + 1):
        ws2.column_dimensions[get_column_letter(4 + d)].width = 8

    # =============================================================
    # SHEET 3: Conflicts & Compliance Log
    # =============================================================
    ws3 = wb.create_sheet(title="Conflicts & SLA Audit")
    ws3.views.sheetView[0].showGridLines = True
    
    ws3.merge_cells("A1:F1")
    ws3["A1"] = f"Identified Conflicts & Operational Exceptions — {month_name} {year}"
    ws3["A1"].font = font_title

    conf_headers = ["Date", "Severity", "Conflict Type", "Brand", "Process", "Employee", "Violation Message", "Suggested Fix"]
    for col_idx, h in enumerate(conf_headers, 1):
        cell = ws3.cell(row=3, column=col_idx, value=h)
        cell.font = font_header
        cell.fill = fill_header
        cell.border = thin_border

    confs = database.get_conflicts_for_roster(roster_id, db_path)
    current_row = 4
    for c in confs:
        ws3.cell(row=current_row, column=1, value=c["date"]).border = thin_border
        
        sev_cell = ws3.cell(row=current_row, column=2, value=c["severity"])
        sev_cell.border = thin_border
        sev_cell.alignment = align_center
        if c["severity"] == "CRITICAL":
            sev_cell.fill = status_fills["LEAVE"]
            sev_cell.font = status_fonts["LEAVE"]
        else:
            sev_cell.fill = status_fills["HOLIDAY"]
            sev_cell.font = status_fonts["HOLIDAY"]

        ws3.cell(row=current_row, column=3, value=c["conflict_type"]).border = thin_border
        ws3.cell(row=current_row, column=4, value=c.get("brand_name", "-") or "-").border = thin_border
        ws3.cell(row=current_row, column=5, value=c.get("process_name", "-") or "-").border = thin_border
        ws3.cell(row=current_row, column=6, value=c.get("employee_name", "-") or "-").border = thin_border
        ws3.cell(row=current_row, column=7, value=c["message"]).border = thin_border
        ws3.cell(row=current_row, column=8, value=c.get("suggested_fix", "-")).border = thin_border
        current_row += 1

    ws3.column_dimensions["A"].width = 14
    ws3.column_dimensions["B"].width = 14
    ws3.column_dimensions["C"].width = 24
    ws3.column_dimensions["D"].width = 22
    ws3.column_dimensions["E"].width = 18
    ws3.column_dimensions["F"].width = 20
    ws3.column_dimensions["G"].width = 45
    ws3.column_dimensions["H"].width = 45

    # =============================================================
    # SHEET 4: Employee Attendance & KPI Summary
    # =============================================================
    ws4 = wb.create_sheet(title="Employee KPI Summary")
    ws4.views.sheetView[0].showGridLines = True
    
    ws4.merge_cells("A1:G1")
    ws4["A1"] = f"Employee Monthly Shift & Attendance Summary — {month_name} {year}"
    ws4["A1"].font = font_title

    kpi_headers = ["Employee Name", "Pod", "Role", "Working Days", "Weekly Offs", "Leaves", "Holidays", "Comp-Offs"]
    for col_idx, h in enumerate(kpi_headers, 1):
        cell = ws4.cell(row=3, column=col_idx, value=h)
        cell.font = font_header
        cell.fill = fill_sub_header
        cell.border = thin_border

    current_row = 4
    for emp_name in sorted(matrix.keys()):
        pod_name, role = emp_meta[emp_name]
        emp_statuses = list(matrix[emp_name].values())
        
        ws4.cell(row=current_row, column=1, value=emp_name).font = font_bold
        ws4.cell(row=current_row, column=1).border = thin_border
        ws4.cell(row=current_row, column=2, value=pod_name).border = thin_border
        ws4.cell(row=current_row, column=3, value=role).border = thin_border

        ws4.cell(row=current_row, column=4, value=emp_statuses.count("WORKING")).border = thin_border
        ws4.cell(row=current_row, column=5, value=emp_statuses.count("WEEKLY OFF")).border = thin_border
        ws4.cell(row=current_row, column=6, value=emp_statuses.count("LEAVE")).border = thin_border
        ws4.cell(row=current_row, column=7, value=emp_statuses.count("HOLIDAY")).border = thin_border
        ws4.cell(row=current_row, column=8, value=emp_statuses.count("COMP-OFF")).border = thin_border
        current_row += 1

    ws4.column_dimensions["A"].width = 24
    ws4.column_dimensions["B"].width = 20
    ws4.column_dimensions["C"].width = 16
    for c in ["D", "E", "F", "G", "H"]:
        ws4.column_dimensions[c].width = 14

    output = io.BytesIO()
    wb.save(output)
    return output.getvalue()


def export_roster_to_csv(roster_id: int, db_path: str = database.DB_PATH) -> str:
    """Exports all roster entries for a roster to CSV format."""
    entries = database.get_roster_entries(roster_id, db_path)
    df = pd.DataFrame(entries)
    return df.to_csv(index=False)


def export_conflicts_to_csv(roster_id: int, db_path: str = database.DB_PATH) -> str:
    """Exports all conflicts for a roster to CSV format."""
    confs = database.get_conflicts_for_roster(roster_id, db_path)
    df = pd.DataFrame(confs)
    return df.to_csv(index=False)
