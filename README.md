# Smart Roster Management System
### DataStraw Tech Internship Assessment

A production-grade, constraint-aware monthly roster scheduling and compliance management platform built for modern D2C customer operations companies. Designed with Python, SQLite, Streamlit, Pandas, and Openpyxl.

---

## 📑 Table of Contents
1. [Executive Summary & Problem Statement](#executive-summary--problem-statement)
2. [Key Capabilities & Innovations](#key-capabilities--innovations)
3. [System Architecture & Data Model](#system-architecture--data-model)
4. [Technology Stack](#technology-stack)
5. [Installation & Quick Start](#installation--quick-start)
6. [Automated Test Suite](#automated-test-suite)
7. [Tell Us How You Think: Assessment Answers](#tell-us-how-you-think-assessment-answers)
   - [Question 1: Modeling Relationships](#1-how-did-you-model-employees-brands-processes-pods-and-their-relationships)
   - [Question 2: Constraint Engine & Validation](#2-how-does-your-system-generate-a-roster-and-determine-whether-it-satisfies-the-required-constraints)
   - [Question 3: Single-Resource vs Multi-Resource Brands](#3-how-did-you-handle-the-difference-between-single-resource-brands-and-brands-with-multiple-employees)
   - [Question 4: Unavailability of Sole Operators](#4-what-happens-when-an-employee-manages-all-processes-for-a-brand-but-is-unavailable-on-a-required-working-day)
   - [Question 5: Conflicting Requirements & Understaffing](#5-how-does-your-system-handle-conflicting-requirements-or-insufficient-staffing)
   - [Question 6: Automated vs Human-Controlled Decisions](#6-which-parts-of-the-process-did-you-automate-and-which-did-you-leave-under-human-control-why)
   - [Question 7: Scaling Strategy (2x Team & Brands)](#7-if-the-company-doubled-its-team-and-brand-count-what-would-you-change-about-your-solution)
   - [Question 8: Roadmap & 1-Week Improvements](#8-if-you-had-one-additional-week-to-work-on-this-what-would-you-improve-first)
8. [Public Deployment Guide](#public-deployment-guide)

---

## Executive Summary & Problem Statement
Customer experience (CX) and operations companies serving Direct-to-Consumer (D2C) brands face non-uniform scheduling complexities:
- **80% Single-Resource Brands**: A single dedicated agent handles all processes for that client brand.
- **20% Multi-Resource Brands**: 2–3 agents work collaboratively, with split or overlapping process specializations.
- **Divergent Operating Calendars**: Some brands operate **365 days a year** (including holidays and Sundays), others operate **daily except public holidays**, and some take **Sundays and holidays off**.
- **Employee Nuances**: Staggered weekly offs (e.g. Fri/Sat, Sun/Mon), planned leaves, public holidays, and approved comp-offs.

A weekly off assigned to a sole operator risks total client outage. This platform moves beyond static calendars by deploying a **deterministic constraint solver** with **honest gap detection**, **instant backup recommendations**, and **single-click change management**.

---

## Key Capabilities & Innovations
1. **Honest Constraint Solving**: Unlike naive tools that mark employees "Working" to mask deficits, our engine respects hard constraints (approved leaves, closed operating days) and surfaces unfillable gaps as explicit compliance conflicts.
2. **5-Way Multi-Dimensional Roster Views**:
   - **Company-Wide Matrix**: Heatmap of all 32+ employees across 30 days with status pills (`WORKING`, `WEEKLY OFF`, `LEAVE`, `HOLIDAY`, `COMP-OFF`).
   - **Pod-Wise View**: Filtered team schedules grouped under each Pod Lead.
   - **Brand-Wise View**: Daily operational coverage indicator (✅ Met / ❌ Zero Coverage) per brand.
   - **Process-Wise View**: Cross-brand staffing distribution for Customer Support (CS), Abandoned Cart Conversion (ACC), Retention (RET), and Non-Delivery Reports (NDR).
   - **Employee-Wise View**: Personalized monthly attendance card with working day totals and leave summaries.
3. **Change Management Demonstration**: Built-in interactive simulator demonstrating emergency leave of a sole operator, automated backup scoring, and 1-click conflict resolution.
4. **Multi-Format Export**: Styled, multi-tab Excel workbooks (`.xlsx`) via Openpyxl and raw CSV outputs.

---

## System Architecture & Data Model

```mermaid
flowchart TD
    subgraph Data Tier [SQLite Database - roster.db]
        PODS[pods]
        EMP[employees]
        BRANDS[brands]
        PROC[processes]
        RULES[brand_process_rules]
        ASSIGN[assignments]
        LEAVES[leaves]
        HOLIDAYS[public_holidays]
        ROSTERS[rosters]
        ENTRIES[roster_entries]
        CONFS[conflicts]
    end

    subgraph Logic Tier [Python Scheduling & Compliance Core]
        SCHED[scheduler.py\nDeterministic Constraint Solver]
        VAL[validator.py\nConflict Detection & Backup Engine]
        EXP[exporter.py\nOpenpyxl Multi-Sheet Exporter]
        SEED[sample_data.py\nRealistic 32-Emp Benchmark Dataset]
    end

    subgraph UI Tier [Streamlit Admin SaaS]
        APP[app.py\nModern SaaS Interface]
    end

    Data Tier <--> SCHED
    Data Tier <--> VAL
    Data Tier <--> EXP
    SCHED --> APP
    VAL --> APP
    EXP --> APP
```

---

## Technology Stack
- **Language**: Python 3.12+
- **Database**: SQLite 3 (Normalized relational schema with foreign key enforcement and indices)
- **Web Framework**: Streamlit (Modern custom CSS, responsive cards, interactive state management)
- **Data Manipulation**: Pandas
- **Spreadsheet Generation**: Openpyxl (Multi-sheet workbooks with custom typography and color fills)
- **Automated Testing**: Pytest

---

## Installation & Quick Start

### 1. Clone & Enter Directory
```bash
git clone https://github.com/<your-username>/Smart-Roster-Management.git
cd Smart-Roster-Management
```

### 2. Set Up Virtual Environment (Recommended)
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Initialize Database & Seed Benchmark Data
```bash
python sample_data.py
```

### 5. Launch Application
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## Automated Test Suite
Run the comprehensive Pytest suite covering single-resource brands, multi-resource brands, weekly offs, leaves, holiday rules, and backup reassignments:

```bash
pytest tests/ -v
```

Expected output:
```text
tests/test_roster.py::test_database_initialization PASSED
tests/test_roster.py::test_monthly_roster_generation PASSED
tests/test_roster.py::test_operating_patterns PASSED
tests/test_roster.py::test_single_resource_brand_leave_conflict PASSED
tests/test_roster.py::test_backup_recommendations_and_reassignment PASSED
tests/test_roster.py::test_weekly_off_honoring PASSED
tests/test_roster.py::test_public_holiday_handling PASSED
============================== 7 passed in 0.80s ==============================
```

---

## Tell Us How You Think: Assessment Answers

### 1. How did you model employees, brands, processes, pods, and their relationships?
We designed a normalized relational schema in SQLite enforcing strict foreign keys and cascading rules:
- **`pods`**: Represents operational clusters (Alpha, Beta, Gamma, Delta), with a `lead_id` referencing the designated Pod Lead.
- **`employees`**: Stores employee profiles, pod association, designation, and primary weekly-off patterns (`weekly_off_day_1`, `weekly_off_day_2`).
- **`brands`**: Holds client entities, their supervising pod, operating pattern (`365_days`, `daily_ex_holidays`, `sundays_holidays_off`), and an architectural flag `is_single_resource` (1 for ~80% single-operator brands, 0 for multi-operator brands).
- **`processes`**: Standardized catalog of operational capabilities (*CS*, *ACC*, *RET*, *NDR*).
- **`brand_process_rules`**: Many-to-many relationship linking a brand and process with operating pattern, minimum daily staffing quotas (`min_staff_req`), and daily hours.
- **`assignments`**: Junction table mapping `(employee_id, brand_id, process_id)` with an `is_primary` flag (1 for dedicated assignment, 0 for secondary/backup cross-coverage).
- **`roster_entries`** & **`conflicts`**: Granular day-level shift records and detected SLA violations tied to a monthly `rosters` parent record.

### 2. How does your system generate a roster and determine whether it satisfies the required constraints?
The generation logic executes a deterministic forward-pass algorithm:
1. **Calendar Ingestion**: Identifies total days in the month and gazetted public holidays.
2. **Employee Availability Resolution**: For each employee on date $D$:
   - If an approved leave exists $\implies$ status is strictly `LEAVE` (or `COMP-OFF`).
   - If date $D$ matches their weekly off pattern $\implies$ status is `WEEKLY OFF`.
   - If available, evaluate assigned brands' operating rules. If the brand operates on date $D$ (even on Sundays/holidays for 365-day brands), status is marked `WORKING` (with a comp-off credit note on holidays). If the brand is closed, status is `HOLIDAY` or `WEEKLY OFF`.
3. **Automated Audit**: The validator scans all generated entries against required rules:
   - Evaluates whether $\text{Working Staff} \ge \text{Min Required Staff}$.
   - Checks that no agent is assigned `WORKING` while on approved leave.
   - Verifies that no agent has overlapping conflicting shifts across different brands.
   - Flags discrepancies as `CRITICAL`, `WARNING`, or `INFO`.

### 3. How did you handle the difference between single-resource brands and brands with multiple employees?
- **Single-Resource Brands (~80%)**: Assigned exactly one primary dedicated employee who handles all active processes for that brand. During schedule evaluation, if that sole operator is on duty, all brand processes inherit coverage. However, if that operator is on leave or weekly off, the brand drops to zero coverage, immediately triggering a **`CRITICAL: MISSING_COVERAGE`** exception.
- **Multi-Resource Brands (~20%)**: Have 2–3 employees with either specialized processes (e.g., TechNova: Emp A on CS, Emp B on ACC, Emp C on RET/NDR) or pooled overlapping capacity (e.g., SwiftCart with 2 required CS agents). The engine aggregates staff by specific process ID. If one agent is absent, the system checks whether remaining agents maintain the minimum threshold before flagging a warning.

### 4. What happens when an employee manages all processes for a brand but is unavailable on a required working day?
When a sole operator (e.g. Rahul Mehta on GlowSkin Luxury) takes leave or has a weekly off on a required operating day:
1. The scheduling engine does **not** invent fake coverage. It marks the employee as `LEAVE`.
2. The validator identifies zero coverage and registers a **`CRITICAL`** conflict.
3. The **Backup Recommendation Engine** (`validator.get_backup_recommendations`) dynamically evaluates all other agents in the company, ranking them based on:
   - **Pod Affiliation**: Agents in the same pod receive priority (+25 score).
   - **Pre-assigned Secondary Backup**: Agents cross-trained on this brand receive priority (+20 score).
   - **Process Competency**: Direct skill match (+15 score).
   - **Availability**: Agents on weekly off can be called for comp-off (+10 score); agents already managing another single-resource brand are penalized (-40 score); agents on leave are disqualified.
4. The operations manager can review the ranked candidates and apply a 1-click reassignment, which updates the shift and revalidates the roster to confirm resolution.

### 5. How does your system handle conflicting requirements or insufficient staffing?
The system prioritizes **truthful operational visibility** over false compliance:
- **Hierarchical Conflict Categorization**:
  - `CRITICAL`: Zero coverage on an open client brand; employee scheduled while on approved leave.
  - `WARNING`: Insufficient staffing below SLA; working on weekly off without comp-off tag; overlapping multi-brand duties.
  - `INFO`: Holiday duty with comp-off accrual.
- Gaps are displayed prominently in the Executive Dashboard, the Live Conflict Center, and the exported Excel audit sheet.
- Managers are equipped with actionable suggested resolutions (e.g., "Assign backup from Pod Alpha").

### 6. Which parts of the process did you automate, and which did you leave under human control? Why?
- **Automated**:
  - Deterministic generation of baseline monthly rosters from rules.
  - Identification of holiday duty and weekly off alignment.
  - Real-time detection and severity classification of conflicts.
  - Multi-factor scoring and ranking of backup resources.
  - Instant revalidation upon manual adjustments.
- **Human-Controlled**:
  - Final decision on which backup resource to reassign.
  - Approval or rejection of employee leave and comp-off requests.
  - Overriding shifts and custom note annotations.
- **Rationale**: While algorithmic suggestions optimize for speed, operational human managers possess qualitative context (e.g., agent burnout, nuanced client expectations, interpersonal pod dynamics) that automated solvers cannot capture.

### 7. If the company doubled its team and brand count, what would you change about your solution?
If scaling from 32 to 64+ employees and 10 to 20+ brands:
1. **Database Migration**: Migrate SQLite to PostgreSQL with connection pooling to handle concurrent multi-manager editing.
2. **Asynchronous Solver**: Move the generation algorithm to background worker tasks (e.g. Celery / Redis queue) to avoid blocking web workers.
3. **Constraint Optimization Engine**: Integrate an integer linear programming solver (such as Google OR-Tools or PuLP) to automatically solve multi-resource shift scheduling with optimal fairness and cost minimization.
4. **Role-Based Access Control (RBAC)**: Partition views so Pod Leads manage only their pod members and brands, while Operations Directors access company-wide metrics.

### 8. If you had one additional week to work on this, what would you improve first?
1. **Interactive Drag-and-Drop Gantt Calendar**: Replace tabular shift views with a full drag-and-drop interactive Gantt timeline (using FullCalendar or Streamlit AgGrid).
2. **Automated Fair-Share Optimization**: Incorporate fairness heuristics to equalize weekend shifts and holiday duties across pod agents across quarters.
3. **Real-time Slack / WhatsApp Bot Integration**: Send shift notifications, swap requests, and emergency backup callouts directly to agent messaging channels.
4. **Shift Swapping Portal**: Allow agents to initiate peer-to-peer shift swap requests subject to pod lead approval.

---

## Public Deployment Guide

### Deploying to Streamlit Community Cloud (Free & Instant)
1. Push this repository to GitHub:
   ```bash
   git init
   git add .
   git commit -m "feat: initial commit of Smart Roster Management System"
   git remote add origin https://github.com/<your-username>/Smart-Roster-Management.git
   git push -u origin main
   ```
2. Navigate to [share.streamlit.io](https://share.streamlit.io/).
3. Connect your GitHub account and select repository `Smart-Roster-Management`.
4. Set Main file path: `app.py`.
5. Click **Deploy**. The app will be publicly accessible worldwide in under 2 minutes!

---

## Author & Submission Details
- **Assignment**: Smart Roster Management System — Tech Internship Assessment
- **Submitted To**: `ozair.shaikh@datastraw.in`, `aryan.jaiswal@datastraw.in`, `talent@datastraw`
