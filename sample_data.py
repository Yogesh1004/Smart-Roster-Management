"""
sample_data.py - Sample Dataset Generator for Smart Roster Management System
Generates 32 employees, 4 pods, 10 brands (8 single-resource, 2 multi-resource),
4 business processes, operating rules, realistic leaves, and gazetted holidays.
"""

from datetime import date
from database import (
    get_connection, init_db, DB_PATH,
    add_pod, update_pod, add_employee, add_brand,
    set_brand_process_rule, add_assignment, add_leave, add_holiday
)


def seed_database(db_path: str = DB_PATH, force: bool = False) -> None:
    """Seeds the database with realistic sample data if empty or forced."""
    init_db(db_path)

    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM employees")
        count = cursor.fetchone()[0]
        if count > 0 and not force:
            print("Database already contains data. Pass force=True to reset.")
            return

    # Clear all data if forced
    if force:
        with get_connection(db_path) as conn:
            conn.executescript("""
                DELETE FROM conflicts;
                DELETE FROM roster_entries;
                DELETE FROM rosters;
                DELETE FROM leaves;
                DELETE FROM public_holidays;
                DELETE FROM assignments;
                DELETE FROM brand_process_rules;
                DELETE FROM processes;
                DELETE FROM brands;
                DELETE FROM employees;
                DELETE FROM pods;
                DELETE FROM sqlite_sequence;
            """)
            conn.commit()

    # 1. Seed Processes
    processes_data = [
        ("Customer Support", "CS", "Inbound chats, ticketing, queries, issue resolution"),
        ("Abandoned Cart Conversion", "ACC", "Outbound cart recovery, WhatsApp follow-ups, payment assistance"),
        ("Customer Retention", "RET", "Subscription renewals, loyalty offers, customer win-backs"),
        ("Non-Delivery Report Management", "NDR", "Courier RTO reduction, buyer address verification, delivery escalations"),
    ]
    with get_connection(db_path) as conn:
        for name, code, desc in processes_data:
            conn.execute(
                "INSERT OR IGNORE INTO processes (name, code, description) VALUES (?, ?, ?)",
                (name, code, desc)
            )
        conn.commit()

    # Fetch process IDs
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT code, id FROM processes")
        p_map = {row["code"]: row["id"] for row in cursor.fetchall()}

    # 2. Seed 4 Operational Pods
    pod_a_id = add_pod("Pod Alpha (North)", None, "Handles North region luxury & beauty D2C accounts", db_path)
    pod_b_id = add_pod("Pod Beta (South)", None, "Handles South electronics and fitness technology accounts", db_path)
    pod_c_id = add_pod("Pod Gamma (East)", None, "Handles East apparel, organic nutrition and home aesthetics", db_path)
    pod_d_id = add_pod("Pod Delta (West)", None, "Handles West lifestyle, quick-commerce and pet care", db_path)

    # 3. Seed 32 Employees (8 per pod) with staggered weekly off combinations
    # Day pairs: ('Sunday', 'Monday'), ('Tuesday', 'Wednesday'), ('Thursday', 'Friday'), ('Saturday', 'Sunday'), ('Friday', 'Saturday')
    employees_seed = [
        # Pod Alpha (North) - 8 employees
        ("Aarav Sharma", "aarav.sharma@datastraw.io", pod_a_id, "Pod Lead", "Sunday", "Monday"),
        ("Rahul Mehta", "rahul.mehta@datastraw.io", pod_a_id, "Senior Agent", "Saturday", "Sunday"),
        ("Neha Gupta", "neha.gupta@datastraw.io", pod_a_id, "Agent", "Sunday", "Monday"),
        ("Vikas Singh", "vikas.singh@datastraw.io", pod_a_id, "Agent", "Tuesday", "Wednesday"),
        ("Pooja Verma", "pooja.verma@datastraw.io", pod_a_id, "Agent", "Thursday", "Friday"),
        ("Amit Roy", "amit.roy@datastraw.io", pod_a_id, "Agent", "Friday", "Saturday"),
        ("Sneha Kapoor", "sneha.kapoor@datastraw.io", pod_a_id, "Agent", "Sunday", "Monday"),
        ("Karan Malhotra", "karan.malhotra@datastraw.io", pod_a_id, "Agent", "Wednesday", "Thursday"),

        # Pod Beta (South) - 8 employees
        ("Priya Nair", "priya.nair@datastraw.io", pod_b_id, "Pod Lead", "Sunday", "Monday"),
        ("Kavita Iyer", "kavita.iyer@datastraw.io", pod_b_id, "Senior Agent", "Saturday", "Sunday"),
        ("Siddharth Menon", "siddharth.menon@datastraw.io", pod_b_id, "Agent", "Friday", "Saturday"),
        ("Deepa Pillai", "deepa.pillai@datastraw.io", pod_b_id, "Agent", "Tuesday", "Wednesday"),
        ("Ashwin Rao", "ashwin.rao@datastraw.io", pod_b_id, "Agent", "Thursday", "Friday"),
        ("Meera Krishnan", "meera.krishnan@datastraw.io", pod_b_id, "Agent", "Sunday", "Monday"),
        ("Arjun Reddy", "arjun.reddy@datastraw.io", pod_b_id, "Agent", "Saturday", "Sunday"),
        ("Swati Joshi", "swati.joshi@datastraw.io", pod_b_id, "Agent", "Wednesday", "Thursday"),

        # Pod Gamma (East) - 8 employees
        ("Rohan Sen", "rohan.sen@datastraw.io", pod_c_id, "Pod Lead", "Sunday", "Monday"),
        ("Ananya Bose", "ananya.bose@datastraw.io", pod_c_id, "Senior Agent", "Saturday", "Sunday"),
        ("Debashish Das", "debashish.das@datastraw.io", pod_c_id, "Agent", "Sunday", "Monday"),
        ("Mitali Mukherjee", "mitali.mukherjee@datastraw.io", pod_c_id, "Agent", "Tuesday", "Wednesday"),
        ("Sourav Chatterjee", "sourav.chatterjee@datastraw.io", pod_c_id, "Agent", "Thursday", "Friday"),
        ("Rupa Ghosh", "rupa.ghosh@datastraw.io", pod_c_id, "Agent", "Friday", "Saturday"),
        ("Tanmoy Dutta", "tanmoy.dutta@datastraw.io", pod_c_id, "Agent", "Sunday", "Monday"),
        ("Payel Paul", "payel.paul@datastraw.io", pod_c_id, "Agent", "Wednesday", "Thursday"),

        # Pod Delta (West) - 8 employees
        ("Ananya Patel", "ananya.patel@datastraw.io", pod_d_id, "Pod Lead", "Sunday", "Monday"),
        ("Bhavin Shah", "bhavin.shah@datastraw.io", pod_d_id, "Senior Agent", "Saturday", "Sunday"),
        ("Tanvi Deshmukh", "tanvi.deshmukh@datastraw.io", pod_d_id, "Agent", "Friday", "Saturday"),
        ("Chirag Kulkarni", "chirag.kulkarni@datastraw.io", pod_d_id, "Agent", "Tuesday", "Wednesday"),
        ("Gauri Shinde", "gauri.shinde@datastraw.io", pod_d_id, "Agent", "Thursday", "Friday"),
        ("Manish Solanki", "manish.solanki@datastraw.io", pod_d_id, "Agent", "Sunday", "Monday"),
        ("Riddhi Merchant", "riddhi.merchant@datastraw.io", pod_d_id, "Agent", "Saturday", "Sunday"),
        ("Hardik Parmar", "hardik.parmar@datastraw.io", pod_d_id, "Agent", "Wednesday", "Thursday"),
    ]

    emp_ids = []
    for name, email, pod_id, role, off1, off2 in employees_seed:
        eid = add_employee(name, email, pod_id, role, off1, off2, 48, db_path)
        emp_ids.append(eid)

    # Assign Pod Leads
    update_pod(pod_a_id, "Pod Alpha (North)", emp_ids[0], "North region luxury & beauty D2C accounts", db_path)
    update_pod(pod_b_id, "Pod Beta (South)", emp_ids[8], "South electronics and fitness technology accounts", db_path)
    update_pod(pod_c_id, "Pod Gamma (East)", emp_ids[16], "East apparel, organic nutrition and home aesthetics", db_path)
    update_pod(pod_d_id, "Pod Delta (West)", emp_ids[24], "West lifestyle, quick-commerce and pet care", db_path)

    # 4. Seed 10 Fictional Brands
    # 8 Single-Resource (~80%) and 2 Multi-Resource (~20%)
    brands_seed = [
        # 8 Single-Resource Brands (is_single_resource = 1)
        ("GlowSkin Luxury", pod_a_id, "365_days", "High-end D2C skincare. 365-day coverage required.", 1),
        ("UrbanThread Apparel", pod_a_id, "daily_ex_holidays", "Modern sustainable apparel. Closed only on national holidays.", 1),
        ("PeakAudio Gear", pod_b_id, "365_days", "Wireless audiophile gear. 24/7/365 operational.", 1),
        ("FitPulse Equipment", pod_b_id, "daily_ex_holidays", "Gym equipment and supplements.", 1),
        ("BloomDecor Living", pod_c_id, "sundays_holidays_off", "Bespoke home decor and artisanal pottery.", 1),
        ("NutriVibe Superfoods", pod_c_id, "daily_ex_holidays", "Cold-pressed juices & vegan superfoods.", 1),
        ("CozyHaven Sleep", pod_d_id, "sundays_holidays_off", "Mattresses, memory pillows, and linen sets.", 1),
        ("PureBite Pet Nutrition", pod_d_id, "sundays_holidays_off", "Fresh organic meals for pets.", 1),

        # 2 Multi-Resource Brands (is_single_resource = 0)
        ("TechNova Smart Gadgets", pod_a_id, "365_days", "Flagship IoT & smart home devices. High-volume 365 days.", 0),
        ("SwiftCart Fast Express", pod_c_id, "daily_ex_holidays", "15-minute quick commerce delivery operations.", 0)
    ]

    brand_ids = []
    for name, pod_id, op_pattern, desc, is_single in brands_seed:
        bid = add_brand(name, pod_id, op_pattern, desc, is_single, db_path)
        brand_ids.append(bid)

    # 5. Seed Brand-Process Rules & Quotas
    # For single-resource brands: requires 1 person across active processes
    # Operating patterns: 365_days, daily_ex_holidays, sundays_holidays_off
    # GlowSkin (365 days, CS & ACC)
    set_brand_process_rule(brand_ids[0], p_map["CS"], "365_days", min_staff=1, db_path=db_path)
    set_brand_process_rule(brand_ids[0], p_map["ACC"], "365_days", min_staff=1, db_path=db_path)

    # UrbanThread (daily_ex_holidays, CS & NDR)
    set_brand_process_rule(brand_ids[1], p_map["CS"], "daily_ex_holidays", min_staff=1, db_path=db_path)
    set_brand_process_rule(brand_ids[1], p_map["NDR"], "daily_ex_holidays", min_staff=1, db_path=db_path)

    # PeakAudio (365_days, CS & RET)
    set_brand_process_rule(brand_ids[2], p_map["CS"], "365_days", min_staff=1, db_path=db_path)
    set_brand_process_rule(brand_ids[2], p_map["RET"], "365_days", min_staff=1, db_path=db_path)

    # FitPulse (daily_ex_holidays, CS & ACC)
    set_brand_process_rule(brand_ids[3], p_map["CS"], "daily_ex_holidays", min_staff=1, db_path=db_path)
    set_brand_process_rule(brand_ids[3], p_map["ACC"], "daily_ex_holidays", min_staff=1, db_path=db_path)

    # BloomDecor (sundays_holidays_off, CS & NDR)
    set_brand_process_rule(brand_ids[4], p_map["CS"], "sundays_holidays_off", min_staff=1, db_path=db_path)
    set_brand_process_rule(brand_ids[4], p_map["NDR"], "sundays_holidays_off", min_staff=1, db_path=db_path)

    # NutriVibe (daily_ex_holidays, CS & RET)
    set_brand_process_rule(brand_ids[5], p_map["CS"], "daily_ex_holidays", min_staff=1, db_path=db_path)
    set_brand_process_rule(brand_ids[5], p_map["RET"], "daily_ex_holidays", min_staff=1, db_path=db_path)

    # CozyHaven (sundays_holidays_off, CS & ACC)
    set_brand_process_rule(brand_ids[6], p_map["CS"], "sundays_holidays_off", min_staff=1, db_path=db_path)
    set_brand_process_rule(brand_ids[6], p_map["ACC"], "sundays_holidays_off", min_staff=1, db_path=db_path)

    # PureBite (sundays_holidays_off, CS & NDR)
    set_brand_process_rule(brand_ids[7], p_map["CS"], "sundays_holidays_off", min_staff=1, db_path=db_path)
    set_brand_process_rule(brand_ids[7], p_map["NDR"], "sundays_holidays_off", min_staff=1, db_path=db_path)

    # Multi-Resource: TechNova Smart Gadgets (365 days, 4 distinct processes, min_staff per process)
    set_brand_process_rule(brand_ids[8], p_map["CS"], "365_days", min_staff=1, db_path=db_path)
    set_brand_process_rule(brand_ids[8], p_map["ACC"], "daily_ex_holidays", min_staff=1, db_path=db_path)
    set_brand_process_rule(brand_ids[8], p_map["RET"], "daily_ex_holidays", min_staff=1, db_path=db_path)
    set_brand_process_rule(brand_ids[8], p_map["NDR"], "sundays_holidays_off", min_staff=1, db_path=db_path)

    # Multi-Resource: SwiftCart Fast Express (daily_ex_holidays, CS min_staff=2, ACC min_staff=1, NDR min_staff=1)
    set_brand_process_rule(brand_ids[9], p_map["CS"], "daily_ex_holidays", min_staff=2, db_path=db_path)
    set_brand_process_rule(brand_ids[9], p_map["ACC"], "daily_ex_holidays", min_staff=1, db_path=db_path)
    set_brand_process_rule(brand_ids[9], p_map["NDR"], "daily_ex_holidays", min_staff=1, db_path=db_path)

    # 6. Seed Employee Assignments
    # --- Single-Resource Brands (1 dedicated employee per brand managing ALL processes) ---
    # GlowSkin Luxury: Rahul Mehta (Emp 1) handles CS & ACC
    add_assignment(emp_ids[1], brand_ids[0], p_map["CS"], is_primary=1, db_path=db_path)
    add_assignment(emp_ids[1], brand_ids[0], p_map["ACC"], is_primary=1, db_path=db_path)

    # UrbanThread Apparel: Sneha Kapoor (Emp 6) handles CS & NDR
    add_assignment(emp_ids[6], brand_ids[1], p_map["CS"], is_primary=1, db_path=db_path)
    add_assignment(emp_ids[6], brand_ids[1], p_map["NDR"], is_primary=1, db_path=db_path)

    # PeakAudio Gear: Kavita Iyer (Emp 9) handles CS & RET
    add_assignment(emp_ids[9], brand_ids[2], p_map["CS"], is_primary=1, db_path=db_path)
    add_assignment(emp_ids[9], brand_ids[2], p_map["RET"], is_primary=1, db_path=db_path)

    # FitPulse Equipment: Siddharth Menon (Emp 10) handles CS & ACC
    add_assignment(emp_ids[10], brand_ids[3], p_map["CS"], is_primary=1, db_path=db_path)
    add_assignment(emp_ids[10], brand_ids[3], p_map["ACC"], is_primary=1, db_path=db_path)

    # BloomDecor Living: Ananya Bose (Emp 17) handles CS & NDR
    add_assignment(emp_ids[17], brand_ids[4], p_map["CS"], is_primary=1, db_path=db_path)
    add_assignment(emp_ids[17], brand_ids[4], p_map["NDR"], is_primary=1, db_path=db_path)

    # NutriVibe Superfoods: Debashish Das (Emp 18) handles CS & RET
    add_assignment(emp_ids[18], brand_ids[5], p_map["CS"], is_primary=1, db_path=db_path)
    add_assignment(emp_ids[18], brand_ids[5], p_map["RET"], is_primary=1, db_path=db_path)

    # CozyHaven Sleep: Bhavin Shah (Emp 25) handles CS & ACC
    add_assignment(emp_ids[25], brand_ids[6], p_map["CS"], is_primary=1, db_path=db_path)
    add_assignment(emp_ids[25], brand_ids[6], p_map["ACC"], is_primary=1, db_path=db_path)

    # PureBite Pet Nutrition: Tanvi Deshmukh (Emp 26) handles CS & NDR
    add_assignment(emp_ids[26], brand_ids[7], p_map["CS"], is_primary=1, db_path=db_path)
    add_assignment(emp_ids[26], brand_ids[7], p_map["NDR"], is_primary=1, db_path=db_path)

    # --- Multi-Resource Brand 1: TechNova Smart Gadgets (3 employees) ---
    # Emp 2 (Neha Gupta) -> CS
    add_assignment(emp_ids[2], brand_ids[8], p_map["CS"], is_primary=1, db_path=db_path)
    # Emp 3 (Vikas Singh) -> ACC & backup CS
    add_assignment(emp_ids[3], brand_ids[8], p_map["ACC"], is_primary=1, db_path=db_path)
    add_assignment(emp_ids[3], brand_ids[8], p_map["CS"], is_primary=0, db_path=db_path)
    # Emp 4 (Pooja Verma) -> RET & NDR
    add_assignment(emp_ids[4], brand_ids[8], p_map["RET"], is_primary=1, db_path=db_path)
    add_assignment(emp_ids[4], brand_ids[8], p_map["NDR"], is_primary=1, db_path=db_path)

    # --- Multi-Resource Brand 2: SwiftCart Fast Express (3 employees with overlap) ---
    # Emp 19 (Mitali Mukherjee) -> CS
    add_assignment(emp_ids[19], brand_ids[9], p_map["CS"], is_primary=1, db_path=db_path)
    # Emp 20 (Sourav Chatterjee) -> CS (2nd required CS) & ACC
    add_assignment(emp_ids[20], brand_ids[9], p_map["CS"], is_primary=1, db_path=db_path)
    add_assignment(emp_ids[20], brand_ids[9], p_map["ACC"], is_primary=1, db_path=db_path)
    # Emp 21 (Rupa Ghosh) -> NDR & backup ACC
    add_assignment(emp_ids[21], brand_ids[9], p_map["NDR"], is_primary=1, db_path=db_path)
    add_assignment(emp_ids[21], brand_ids[9], p_map["ACC"], is_primary=0, db_path=db_path)

    # Assign remaining pod members to multi-brand cross-coverage / floating reserves:
    # Emp 5 (Amit Roy) -> floating reserve on TechNova & GlowSkin backup
    add_assignment(emp_ids[5], brand_ids[0], p_map["CS"], is_primary=0, db_path=db_path)
    add_assignment(emp_ids[5], brand_ids[8], p_map["CS"], is_primary=0, db_path=db_path)

    # Emp 7 (Karan Malhotra) -> UrbanThread backup & CS reserve
    add_assignment(emp_ids[7], brand_ids[1], p_map["CS"], is_primary=0, db_path=db_path)

    # Pod Beta floating reserves:
    # Emp 11 (Deepa Pillai) -> FitPulse backup
    add_assignment(emp_ids[11], brand_ids[3], p_map["CS"], is_primary=0, db_path=db_path)
    # Emp 12 (Ashwin Rao) -> PeakAudio backup
    add_assignment(emp_ids[12], brand_ids[2], p_map["CS"], is_primary=0, db_path=db_path)
    # Emp 13 (Meera Krishnan) -> PeakAudio ACC
    add_assignment(emp_ids[13], brand_ids[2], p_map["RET"], is_primary=0, db_path=db_path)

    # Pod Gamma floating reserves:
    # Emp 22 (Tanmoy Dutta) -> BloomDecor backup
    add_assignment(emp_ids[22], brand_ids[4], p_map["CS"], is_primary=0, db_path=db_path)
    # Emp 23 (Payel Paul) -> NutriVibe backup
    add_assignment(emp_ids[23], brand_ids[5], p_map["CS"], is_primary=0, db_path=db_path)

    # Pod Delta floating reserves:
    # Emp 27 (Chirag Kulkarni) -> CozyHaven backup
    add_assignment(emp_ids[27], brand_ids[6], p_map["CS"], is_primary=0, db_path=db_path)
    # Emp 28 (Gauri Shinde) -> PureBite backup
    add_assignment(emp_ids[28], brand_ids[7], p_map["CS"], is_primary=0, db_path=db_path)
    # Emp 29 (Manish Solanki) -> SwiftCart floating reserve
    add_assignment(emp_ids[29], brand_ids[9], p_map["CS"], is_primary=0, db_path=db_path)

    # 7. Seed Public Holidays (Year 2026 Focus: November & Standard Calendar)
    holidays_seed = [
        ("2026-01-26", "Republic Day", 1),
        ("2026-03-25", "Holi", 1),
        ("2026-08-15", "Independence Day", 1),
        ("2026-10-02", "Gandhi Jayanti", 1),
        ("2026-11-08", "Diwali (Deepavali)", 1),
        ("2026-11-10", "Govardhan Puja", 1),
        ("2026-11-24", "Guru Nanak Jayanti", 1),
        ("2026-12-25", "Christmas", 1),
    ]
    for h_date, h_name, is_mand in holidays_seed:
        add_holiday(h_date, h_name, is_mand, db_path)

    # 8. Seed Pre-planned Leaves for November 2026 Demo Month
    # Notice: Rahul Mehta (Emp 1, sole operator for GlowSkin) has planned leave on Nov 12, 2026!
    # This precisely models the change management scenario where single-resource brand has an unavailabilty gap.
    leaves_seed = [
        (emp_ids[1], "2026-11-12", "Privilege Leave", "APPROVED", "Family function (Critical Change Scenario Demo)"),
        (emp_ids[6], "2026-11-16", "Casual Leave", "APPROVED", "Personal errand"),
        (emp_ids[10], "2026-11-20", "Sick Leave", "APPROVED", "Medical checkup"),
        (emp_ids[19], "2026-11-05", "Casual Leave", "APPROVED", "Personal leave"),
        (emp_ids[20], "2026-11-05", "Comp-Off", "APPROVED", "Comp-off for festival duty"),
    ]
    for eid, l_date, l_type, l_status, l_reason in leaves_seed:
        add_leave(eid, l_date, l_type, l_status, l_reason, db_path)

    print(f"Sample data successfully seeded in {db_path}!")
    print(f"- 4 Pods, 32 Employees, 10 Brands (8 single-resource, 2 multi-resource)")
    print(f"- 4 Processes, Operating rules, Pre-seeded leaves & Public Holidays")


def reset_and_seed_database(db_path: str = DB_PATH) -> None:
    """Forces reset and re-seed of the database."""
    seed_database(db_path, force=True)


if __name__ == "__main__":
    reset_and_seed_database()
