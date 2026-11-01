"""
database.py - Database Layer for Smart Roster Management System
Provides SQLite schema definitions, connection management, and CRUD helpers.
"""

import sqlite3
import os
from typing import List, Dict, Any, Optional
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "roster.db")


def get_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    """Returns an SQLite connection configured with foreign keys and dict-like rows."""
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str = DB_PATH) -> None:
    """Initializes the database schema if tables do not exist."""
    schema_sql = """
    CREATE TABLE IF NOT EXISTS pods (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        lead_id INTEGER,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS employees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        pod_id INTEGER NOT NULL REFERENCES pods(id) ON DELETE RESTRICT,
        role TEXT DEFAULT 'Agent',
        weekly_off_day_1 TEXT NOT NULL,
        weekly_off_day_2 TEXT,
        max_hours_week INTEGER DEFAULT 48,
        is_active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS brands (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        pod_id INTEGER NOT NULL REFERENCES pods(id) ON DELETE RESTRICT,
        operating_pattern TEXT NOT NULL,
        description TEXT,
        is_single_resource INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS processes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        code TEXT NOT NULL UNIQUE,
        description TEXT
    );

    CREATE TABLE IF NOT EXISTS brand_process_rules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        brand_id INTEGER NOT NULL REFERENCES brands(id) ON DELETE CASCADE,
        process_id INTEGER NOT NULL REFERENCES processes(id) ON DELETE CASCADE,
        operating_pattern TEXT NOT NULL,
        min_staff_req INTEGER DEFAULT 1,
        hours_per_day INTEGER DEFAULT 8,
        UNIQUE(brand_id, process_id)
    );

    CREATE TABLE IF NOT EXISTS assignments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
        brand_id INTEGER NOT NULL REFERENCES brands(id) ON DELETE CASCADE,
        process_id INTEGER NOT NULL REFERENCES processes(id) ON DELETE CASCADE,
        is_primary INTEGER DEFAULT 1,
        UNIQUE(employee_id, brand_id, process_id)
    );

    CREATE TABLE IF NOT EXISTS leaves (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
        leave_date TEXT NOT NULL,
        leave_type TEXT NOT NULL,
        status TEXT DEFAULT 'APPROVED',
        reason TEXT,
        UNIQUE(employee_id, leave_date)
    );

    CREATE TABLE IF NOT EXISTS public_holidays (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        holiday_date TEXT NOT NULL UNIQUE,
        name TEXT NOT NULL,
        is_mandatory_off INTEGER DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS rosters (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        month INTEGER NOT NULL,
        year INTEGER NOT NULL,
        status TEXT DEFAULT 'DRAFT',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(month, year)
    );

    CREATE TABLE IF NOT EXISTS roster_entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        roster_id INTEGER NOT NULL REFERENCES rosters(id) ON DELETE CASCADE,
        employee_id INTEGER NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
        date TEXT NOT NULL,
        brand_id INTEGER REFERENCES brands(id) ON DELETE SET NULL,
        process_id INTEGER REFERENCES processes(id) ON DELETE SET NULL,
        status TEXT NOT NULL,
        is_override INTEGER DEFAULT 0,
        notes TEXT,
        UNIQUE(roster_id, employee_id, date, brand_id, process_id)
    );

    CREATE TABLE IF NOT EXISTS conflicts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        roster_id INTEGER NOT NULL REFERENCES rosters(id) ON DELETE CASCADE,
        date TEXT NOT NULL,
        brand_id INTEGER REFERENCES brands(id) ON DELETE CASCADE,
        process_id INTEGER REFERENCES processes(id) ON DELETE CASCADE,
        employee_id INTEGER REFERENCES employees(id) ON DELETE CASCADE,
        severity TEXT NOT NULL,
        conflict_type TEXT NOT NULL,
        message TEXT NOT NULL,
        suggested_fix TEXT
    );

    CREATE INDEX IF NOT EXISTS idx_roster_entries_lookup 
    ON roster_entries(roster_id, date, employee_id);

    CREATE INDEX IF NOT EXISTS idx_conflicts_lookup 
    ON conflicts(roster_id, date);
    """
    with get_connection(db_path) as conn:
        conn.executescript(schema_sql)
        conn.commit()


# ============================================================================
# CRUD: PODS
# ============================================================================

def get_all_pods(db_path: str = DB_PATH) -> List[Dict[str, Any]]:
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.*, e.name as lead_name,
                   (SELECT COUNT(*) FROM employees WHERE pod_id = p.id) as employee_count,
                   (SELECT COUNT(*) FROM brands WHERE pod_id = p.id) as brand_count
            FROM pods p
            LEFT JOIN employees e ON p.lead_id = e.id
            ORDER BY p.name
        """)
        return [dict(row) for row in cursor.fetchall()]


def add_pod(name: str, lead_id: Optional[int] = None, description: str = "", db_path: str = DB_PATH) -> int:
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO pods (name, lead_id, description) VALUES (?, ?, ?)",
            (name, lead_id, description)
        )
        conn.commit()
        return cursor.lastrowid


def update_pod(pod_id: int, name: str, lead_id: Optional[int], description: str, db_path: str = DB_PATH) -> None:
    with get_connection(db_path) as conn:
        conn.execute(
            "UPDATE pods SET name = ?, lead_id = ?, description = ? WHERE id = ?",
            (name, lead_id, description, pod_id)
        )
        conn.commit()


# ============================================================================
# CRUD: EMPLOYEES
# ============================================================================

def get_all_employees(db_path: str = DB_PATH, active_only: bool = True) -> List[Dict[str, Any]]:
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        query = """
            SELECT e.*, p.name as pod_name
            FROM employees e
            JOIN pods p ON e.pod_id = p.id
        """
        if active_only:
            query += " WHERE e.is_active = 1"
        query += " ORDER BY p.name, e.name"
        cursor.execute(query)
        return [dict(row) for row in cursor.fetchall()]


def get_employee_by_id(employee_id: int, db_path: str = DB_PATH) -> Optional[Dict[str, Any]]:
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT e.*, p.name as pod_name
            FROM employees e
            JOIN pods p ON e.pod_id = p.id
            WHERE e.id = ?
        """, (employee_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def add_employee(name: str, email: str, pod_id: int, role: str,
                 off_day_1: str, off_day_2: Optional[str] = None,
                 max_hours: int = 48, db_path: str = DB_PATH) -> int:
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO employees (name, email, pod_id, role, weekly_off_day_1, weekly_off_day_2, max_hours_week)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (name, email, pod_id, role, off_day_1, off_day_2, max_hours))
        conn.commit()
        return cursor.lastrowid


def update_employee(employee_id: int, name: str, email: str, pod_id: int, role: str,
                    off_day_1: str, off_day_2: Optional[str], is_active: int = 1,
                    db_path: str = DB_PATH) -> None:
    with get_connection(db_path) as conn:
        conn.execute("""
            UPDATE employees 
            SET name = ?, email = ?, pod_id = ?, role = ?, 
                weekly_off_day_1 = ?, weekly_off_day_2 = ?, is_active = ?
            WHERE id = ?
        """, (name, email, pod_id, role, off_day_1, off_day_2, is_active, employee_id))
        conn.commit()


def delete_employee(employee_id: int, db_path: str = DB_PATH) -> None:
    with get_connection(db_path) as conn:
        conn.execute("DELETE FROM employees WHERE id = ?", (employee_id,))
        conn.commit()


# ============================================================================
# CRUD: BRANDS
# ============================================================================

def get_all_brands(db_path: str = DB_PATH) -> List[Dict[str, Any]]:
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT b.*, p.name as pod_name,
                   (SELECT COUNT(DISTINCT employee_id) FROM assignments WHERE brand_id = b.id) as assigned_emp_count
            FROM brands b
            JOIN pods p ON b.pod_id = p.id
            ORDER BY b.name
        """)
        return [dict(row) for row in cursor.fetchall()]


def get_brand_by_id(brand_id: int, db_path: str = DB_PATH) -> Optional[Dict[str, Any]]:
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT b.*, p.name as pod_name
            FROM brands b
            JOIN pods p ON b.pod_id = p.id
            WHERE b.id = ?
        """, (brand_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def add_brand(name: str, pod_id: int, operating_pattern: str,
              description: str = "", is_single_resource: int = 1, db_path: str = DB_PATH) -> int:
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO brands (name, pod_id, operating_pattern, description, is_single_resource)
            VALUES (?, ?, ?, ?, ?)
        """, (name, pod_id, operating_pattern, description, is_single_resource))
        conn.commit()
        return cursor.lastrowid


def update_brand(brand_id: int, name: str, pod_id: int, operating_pattern: str,
                 description: str, is_single_resource: int, db_path: str = DB_PATH) -> None:
    with get_connection(db_path) as conn:
        conn.execute("""
            UPDATE brands 
            SET name = ?, pod_id = ?, operating_pattern = ?, description = ?, is_single_resource = ?
            WHERE id = ?
        """, (name, pod_id, operating_pattern, description, is_single_resource, brand_id))
        conn.commit()


def delete_brand(brand_id: int, db_path: str = DB_PATH) -> None:
    with get_connection(db_path) as conn:
        conn.execute("DELETE FROM brands WHERE id = ?", (brand_id,))
        conn.commit()


# ============================================================================
# CRUD: PROCESSES & RULES
# ============================================================================

def get_all_processes(db_path: str = DB_PATH) -> List[Dict[str, Any]]:
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM processes ORDER BY name")
        return [dict(row) for row in cursor.fetchall()]


def get_all_rules(db_path: str = DB_PATH) -> List[Dict[str, Any]]:
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT r.*, b.name as brand_name, p.name as process_name, p.code as process_code
            FROM brand_process_rules r
            JOIN brands b ON r.brand_id = b.id
            JOIN processes p ON r.process_id = p.id
            ORDER BY b.name, p.name
        """)
        return [dict(row) for row in cursor.fetchall()]


def set_brand_process_rule(brand_id: int, process_id: int, operating_pattern: str,
                           min_staff: int = 1, hours: int = 8, db_path: str = DB_PATH) -> None:
    with get_connection(db_path) as conn:
        conn.execute("""
            INSERT INTO brand_process_rules (brand_id, process_id, operating_pattern, min_staff_req, hours_per_day)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(brand_id, process_id) DO UPDATE SET
                operating_pattern = excluded.operating_pattern,
                min_staff_req = excluded.min_staff_req,
                hours_per_day = excluded.hours_per_day
        """, (brand_id, process_id, operating_pattern, min_staff, hours))
        conn.commit()


def delete_brand_process_rule(rule_id: int, db_path: str = DB_PATH) -> None:
    with get_connection(db_path) as conn:
        conn.execute("DELETE FROM brand_process_rules WHERE id = ?", (rule_id,))
        conn.commit()


# ============================================================================
# CRUD: ASSIGNMENTS
# ============================================================================

def get_all_assignments(db_path: str = DB_PATH) -> List[Dict[str, Any]]:
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT a.*, e.name as employee_name, e.role as employee_role,
                   b.name as brand_name, p.name as process_name, p.code as process_code,
                   pod.name as pod_name
            FROM assignments a
            JOIN employees e ON a.employee_id = e.id
            JOIN brands b ON a.brand_id = b.id
            JOIN processes p ON a.process_id = p.id
            JOIN pods pod ON b.pod_id = pod.id
            ORDER BY b.name, p.name, e.name
        """)
        return [dict(row) for row in cursor.fetchall()]


def add_assignment(employee_id: int, brand_id: int, process_id: int,
                   is_primary: int = 1, db_path: str = DB_PATH) -> int:
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO assignments (employee_id, brand_id, process_id, is_primary)
            VALUES (?, ?, ?, ?)
        """, (employee_id, brand_id, process_id, is_primary))
        conn.commit()
        return cursor.lastrowid


def delete_assignment(assignment_id: int, db_path: str = DB_PATH) -> None:
    with get_connection(db_path) as conn:
        conn.execute("DELETE FROM assignments WHERE id = ?", (assignment_id,))
        conn.commit()


# ============================================================================
# CRUD: LEAVES & HOLIDAYS
# ============================================================================

def get_all_leaves(db_path: str = DB_PATH) -> List[Dict[str, Any]]:
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT l.*, e.name as employee_name, pod.name as pod_name
            FROM leaves l
            JOIN employees e ON l.employee_id = e.id
            JOIN pods pod ON e.pod_id = pod.id
            ORDER BY l.leave_date DESC, e.name
        """)
        return [dict(row) for row in cursor.fetchall()]


def add_leave(employee_id: int, leave_date: str, leave_type: str,
              status: str = "APPROVED", reason: str = "", db_path: str = DB_PATH) -> int:
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO leaves (employee_id, leave_date, leave_type, status, reason)
            VALUES (?, ?, ?, ?, ?)
        """, (employee_id, leave_date, leave_type, status, reason))
        conn.commit()
        return cursor.lastrowid


def delete_leave(leave_id: int, db_path: str = DB_PATH) -> None:
    with get_connection(db_path) as conn:
        conn.execute("DELETE FROM leaves WHERE id = ?", (leave_id,))
        conn.commit()


def get_all_holidays(db_path: str = DB_PATH) -> List[Dict[str, Any]]:
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM public_holidays ORDER BY holiday_date ASC")
        return [dict(row) for row in cursor.fetchall()]


def add_holiday(holiday_date: str, name: str, is_mandatory_off: int = 1, db_path: str = DB_PATH) -> int:
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO public_holidays (holiday_date, name, is_mandatory_off)
            VALUES (?, ?, ?)
        """, (holiday_date, name, is_mandatory_off))
        conn.commit()
        return cursor.lastrowid


def delete_holiday(holiday_id: int, db_path: str = DB_PATH) -> None:
    with get_connection(db_path) as conn:
        conn.execute("DELETE FROM public_holidays WHERE id = ?", (holiday_id,))
        conn.commit()


# ============================================================================
# CRUD: ROSTERS & ENTRIES
# ============================================================================

def create_or_get_roster(month: int, year: int, db_path: str = DB_PATH) -> Dict[str, Any]:
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM rosters WHERE month = ? AND year = ?", (month, year))
        row = cursor.fetchone()
        if row:
            return dict(row)
        cursor.execute("INSERT INTO rosters (month, year, status) VALUES (?, ?, 'DRAFT')", (month, year))
        conn.commit()
        cursor.execute("SELECT * FROM rosters WHERE id = ?", (cursor.lastrowid,))
        return dict(cursor.fetchone())


def get_roster_entries(roster_id: int, db_path: str = DB_PATH) -> List[Dict[str, Any]]:
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT re.*, 
                   e.name as employee_name, e.role as employee_role, e.weekly_off_day_1, e.weekly_off_day_2,
                   p_emp.name as employee_pod_name,
                   b.name as brand_name,
                   p.name as process_name, p.code as process_code
            FROM roster_entries re
            JOIN employees e ON re.employee_id = e.id
            JOIN pods p_emp ON e.pod_id = p_emp.id
            LEFT JOIN brands b ON re.brand_id = b.id
            LEFT JOIN processes p ON re.process_id = p.id
            WHERE re.roster_id = ?
            ORDER BY re.date, e.name
        """, (roster_id,))
        return [dict(row) for row in cursor.fetchall()]


def update_roster_entry(entry_id: int, status: str, brand_id: Optional[int],
                        process_id: Optional[int], is_override: int = 1,
                        notes: Optional[str] = None, db_path: str = DB_PATH) -> None:
    with get_connection(db_path) as conn:
        conn.execute("""
            UPDATE roster_entries 
            SET status = ?, brand_id = ?, process_id = ?, is_override = ?, notes = ?
            WHERE id = ?
        """, (status, brand_id, process_id, is_override, notes, entry_id))
        conn.commit()


def save_roster_entries_bulk(roster_id: int, entries: List[Dict[str, Any]], db_path: str = DB_PATH) -> None:
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        # Clear existing entries for this roster
        cursor.execute("DELETE FROM roster_entries WHERE roster_id = ?", (roster_id,))
        cursor.executemany("""
            INSERT INTO roster_entries (roster_id, employee_id, date, brand_id, process_id, status, is_override, notes)
            VALUES (:roster_id, :employee_id, :date, :brand_id, :process_id, :status, :is_override, :notes)
        """, entries)
        conn.commit()


# ============================================================================
# CRUD: CONFLICTS
# ============================================================================

def save_conflicts(roster_id: int, conflicts: List[Dict[str, Any]], db_path: str = DB_PATH) -> None:
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM conflicts WHERE roster_id = ?", (roster_id,))
        if conflicts:
            cursor.executemany("""
                INSERT INTO conflicts 
                (roster_id, date, brand_id, process_id, employee_id, severity, conflict_type, message, suggested_fix)
                VALUES (:roster_id, :date, :brand_id, :process_id, :employee_id, :severity, :conflict_type, :message, :suggested_fix)
            """, conflicts)
        conn.commit()


def get_conflicts_for_roster(roster_id: int, db_path: str = DB_PATH) -> List[Dict[str, Any]]:
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.*, 
                   b.name as brand_name, 
                   p.name as process_name, 
                   e.name as employee_name
            FROM conflicts c
            LEFT JOIN brands b ON c.brand_id = b.id
            LEFT JOIN processes p ON c.process_id = p.id
            LEFT JOIN employees e ON c.employee_id = e.id
            WHERE c.roster_id = ?
            ORDER BY c.date, c.severity DESC
        """, (roster_id,))
        return [dict(row) for row in cursor.fetchall()]


# ============================================================================
# DASHBOARD METRICS QUERY
# ============================================================================

def get_system_summary(db_path: str = DB_PATH) -> Dict[str, Any]:
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM employees WHERE is_active = 1")
        total_employees = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM pods")
        total_pods = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM brands")
        total_brands = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM brands WHERE is_single_resource = 1")
        single_resource_brands = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM processes")
        total_processes = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM assignments")
        total_assignments = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM public_holidays")
        total_holidays = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM leaves WHERE status = 'APPROVED'")
        total_leaves = cursor.fetchone()[0]

        return {
            "total_employees": total_employees,
            "total_pods": total_pods,
            "total_brands": total_brands,
            "single_resource_brands": single_resource_brands,
            "multi_resource_brands": total_brands - single_resource_brands,
            "total_processes": total_processes,
            "total_assignments": total_assignments,
            "total_holidays": total_holidays,
            "total_leaves": total_leaves
        }
