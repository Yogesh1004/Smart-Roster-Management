"""
app.py - Main Streamlit Application for Smart Roster Management System
DataStraw Tech Internship Assessment
Modern SaaS Admin Dashboard with deterministic scheduling, 5-way roster views,
live conflict validation, change management simulation, and multi-format reports.
"""

import streamlit as st
import pandas as pd
import calendar
from datetime import datetime, date
import database
import sample_data
import scheduler
import validator
import exporter

# ============================================================================
# PAGE CONFIGURATION & CUSTOM STYLING
# ============================================================================
st.set_page_config(
    page_title="DataStraw | Smart Roster Management",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database and seed if empty
database.init_db()
summary = database.get_system_summary()
if summary["total_employees"] == 0:
    sample_data.seed_database()
    summary = database.get_system_summary()

# ============================================================================
# PREMIUM UI THEME — SMART ROSTER MANAGEMENT
# ============================================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=Manrope:wght@500;600;700;800&display=swap');

    :root {
        --bg: #07111f;
        --surface: rgba(15, 29, 49, .88);
        --surface-2: rgba(20, 39, 63, .92);
        --line: rgba(148, 163, 184, .17);
        --text: #e8f0fb;
        --muted: #9aacc2;
        --accent: #60a5fa;
        --accent-2: #22d3ee;
    }

    html, body, [class*="css"], [data-testid="stAppViewContainer"] {
        font-family: 'DM Sans', sans-serif;
    }

    /* Project-relevant office / workforce wallpaper with a dark readability layer */
    [data-testid="stAppViewContainer"] {
        background:
            linear-gradient(115deg, rgba(4, 12, 25, .96) 0%, rgba(5, 18, 35, .91) 52%, rgba(7, 24, 43, .88) 100%),
            url("https://images.unsplash.com/photo-1497366754035-f200968a6e72?auto=format&fit=crop&w=2400&q=85")
            center / cover fixed;
        color: var(--text);
    }
    [data-testid="stAppViewContainer"]::before {
        content: "";
        position: fixed;
        inset: 0;
        pointer-events: none;
        z-index: 0;
        background:
            radial-gradient(circle at 82% 12%, rgba(34, 211, 238, .12), transparent 28%),
            radial-gradient(circle at 12% 82%, rgba(59, 130, 246, .13), transparent 32%);
    }
    [data-testid="stHeader"] { background: rgba(5, 15, 28, .55); }
    [data-testid="stMain"] { background: transparent; }
    .block-container {
        position: relative;
        z-index: 1;
        padding-top: 2rem;
        padding-bottom: 3.5rem;
        max-width: 1600px;
        animation: pageEnter .55s cubic-bezier(.2,.75,.25,1) both;
    }

    /* Longer, layered transitions for every section change */
    @keyframes pageEnter {
        0%   { opacity: 0; transform: translate3d(0, 28px, 0) scale(.985); filter: blur(7px); }
        55%  { opacity: .8; filter: blur(2px); }
        100% { opacity: 1; transform: translate3d(0, 0, 0) scale(1); filter: blur(0); }
    }
    @keyframes sectionReveal {
        0%   { opacity: 0; transform: translate3d(0, 34px, 0) scale(.975); filter: blur(5px); }
        65%  { opacity: .85; }
        100% { opacity: 1; transform: translate3d(0, 0, 0) scale(1); filter: blur(0); }
    }
    @keyframes softRise {
        from { opacity: 0; transform: translateY(18px); }
        to   { opacity: 1; transform: translateY(0); }
    }
    @keyframes navSelect {
        0%   { transform: translateX(-7px) scale(.97); box-shadow: 0 0 0 rgba(34,211,238,0); }
        55%  { transform: translateX(5px) scale(1.035); box-shadow: 0 0 28px rgba(34,211,238,.22); }
        100% { transform: translateX(0) scale(1); box-shadow: 0 8px 24px rgba(0,0,0,.18); }
    }
    @keyframes navGlow {
        0%, 100% { opacity: .55; }
        50% { opacity: 1; }
    }
    @keyframes glowPulse {
        0%, 100% { box-shadow: 0 0 0 rgba(34, 211, 238, 0); }
        50% { box-shadow: 0 0 22px rgba(34, 211, 238, .13); }
    }
    @keyframes sectionFlash {
        0%   { opacity: 0; transform: translate3d(0, 42px, 0) scale(.965); filter: blur(9px) saturate(.7); }
        45%  { opacity: 1; filter: blur(1px) saturate(1.35); }
        72%  { transform: translate3d(0, -4px, 0) scale(1.006); }
        100% { opacity: 1; transform: translate3d(0, 0, 0) scale(1); filter: blur(0) saturate(1); }
    }
    @keyframes accentSweep {
        0%   { transform: translateX(-115%) skewX(-18deg); opacity: 0; }
        18%  { opacity: .8; }
        100% { transform: translateX(220%) skewX(-18deg); opacity: 0; }
    }
    @keyframes activeSectionGlow {
        0%   { box-shadow: 0 0 0 rgba(34,211,238,0); }
        45%  { box-shadow: 0 0 42px rgba(34,211,238,.17), 0 0 85px rgba(37,99,235,.10); }
        100% { box-shadow: 0 0 0 rgba(34,211,238,0); }
    }

    /* Sidebar navigation: larger hit areas, hover expansion and selected animation */
    /* Wider sidebar; on hover it expands over the page like a premium app drawer. */
    section[data-testid="stSidebar"] {
        width: 310px !important;
        min-width: 310px !important;
        background:
            radial-gradient(ellipse at 15% 8%, rgba(34,211,238,.14), transparent 38%),
            linear-gradient(180deg, rgba(7, 18, 33, .99), rgba(10, 27, 48, .99));
        border-right: 1px solid rgba(96,165,250,.28);
        box-shadow: 12px 0 38px rgba(0,0,0,.20);
        transition: width .38s cubic-bezier(.2,.8,.2,1),
                    min-width .38s cubic-bezier(.2,.8,.2,1),
                    box-shadow .38s ease;
        z-index: 100;
    }
    section[data-testid="stSidebar"]:hover {
        width: 370px !important;
        min-width: 370px !important;
        box-shadow: 18px 0 55px rgba(0,0,0,.38), 0 0 30px rgba(34,211,238,.10);
    }
    [data-testid="stSidebar"] > div:first-child { background: transparent; }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 { color: #f1f7ff; font-family: 'Manrope', sans-serif; }
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] label { color: #a9bbd1; }
    [data-testid="stSidebar"] [data-testid="stRadio"] > label {
        color: #dce9f8; font-weight: 800; letter-spacing: .09em;
        text-transform: uppercase; font-size: .78rem; margin-bottom: 12px;
    }
    [data-testid="stSidebar"] [role="radiogroup"] { gap: 9px; }
    [data-testid="stSidebar"] [role="radiogroup"] label {
        position: relative;
        display: flex;
        align-items: center;
        min-height: 62px;
        box-sizing: border-box;
        border: 1px solid rgba(148,163,184,.10);
        border-radius: 15px;
        padding: 16px 16px;
        margin: 6px 3px;
        background: linear-gradient(110deg, rgba(18,38,62,.62), rgba(12,27,46,.48));
        box-shadow: 0 5px 14px rgba(0,0,0,.10);
        transform-origin: left center;
        transition: transform .32s cubic-bezier(.2,.8,.2,1),
                    background .32s ease, border-color .32s ease,
                    box-shadow .32s ease, padding .32s ease;
        cursor: pointer;
    }
    [data-testid="stSidebar"] [role="radiogroup"] label p {
        color: #dce9f8;
        font-size: .91rem;
        line-height: 1.35;
        font-weight: 700;
        transition: color .25s ease;
    }
    [data-testid="stSidebar"] [role="radiogroup"] label:hover {
        z-index: 2;
        transform: translateX(9px) scale(1.065);
        padding-left: 21px;
        background: linear-gradient(105deg, rgba(37,99,235,.30), rgba(8,145,178,.20));
        border-color: rgba(103,232,249,.55);
        box-shadow: 0 15px 34px rgba(0,0,0,.34), 0 0 28px rgba(34,211,238,.20);
    }
    [data-testid="stSidebar"] [role="radiogroup"] label:hover p { color: #ffffff; }
    [data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {
        background: linear-gradient(105deg, rgba(37,99,235,.42), rgba(8,145,178,.28));
        border: 1px solid rgba(103,232,249,.72);
        box-shadow: inset 3px 0 0 #67e8f9, 0 9px 25px rgba(0,0,0,.24);
        animation: navSelect .72s cubic-bezier(.2,.8,.2,1) both;
    }
    [data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) p {
        color: #ffffff; font-weight: 800;
    }
    [data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked)::after {
        content: "";
        position: absolute;
        right: 13px;
        width: 7px; height: 7px;
        border-radius: 50%;
        background: #67e8f9;
        box-shadow: 0 0 12px #22d3ee;
        animation: navGlow 1.8s ease-in-out infinite;
    }

    /* Animate the actual page body and its first-level content on navigation reruns */
    [data-testid="stMainBlockContainer"] > div {
        position: relative;
        animation: sectionFlash 1.05s cubic-bezier(.16,1,.3,1) both,
                   activeSectionGlow 1.25s ease-out both;
        border-radius: 18px;
    }
    /* Brief light sweep gives the right content panel a clear section-change cue. */
    [data-testid="stMainBlockContainer"] > div::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        width: 24%;
        height: 3px;
        border-radius: 99px;
        pointer-events: none;
        background: linear-gradient(90deg, transparent, #67e8f9, #60a5fa, transparent);
        filter: drop-shadow(0 0 9px rgba(34,211,238,.8));
        animation: accentSweep 1.15s ease-out both;
        z-index: 5;
    }
    [data-testid="stMainBlockContainer"] [data-testid="stVerticalBlock"] > div {
        animation: softRise .72s cubic-bezier(.2,.75,.25,1) both;
    }
    [data-testid="stMainBlockContainer"] [data-testid="stVerticalBlock"] > div:nth-child(2) { animation-delay: .07s; }
    [data-testid="stMainBlockContainer"] [data-testid="stVerticalBlock"] > div:nth-child(3) { animation-delay: .13s; }
    [data-testid="stMainBlockContainer"] [data-testid="stVerticalBlock"] > div:nth-child(4) { animation-delay: .19s; }

    /* Headings and copy */
    h1, h2, h3, h4 {
        color: #f3f8ff !important;
        font-family: 'Manrope', sans-serif !important;
        letter-spacing: -.025em;
    }
    h1 { font-weight: 800 !important; }
    h2, h3 { font-weight: 700 !important; }
    p, li, .stMarkdown { color: #d3deec; }
    [data-testid="stCaptionContainer"] { color: var(--muted); }

    /* Metric / content cards */
    .metric-card {
        position: relative;
        overflow: hidden;
        background: linear-gradient(145deg, rgba(21, 42, 68, .94), rgba(11, 25, 44, .94));
        border: 1px solid rgba(148, 163, 184, .19);
        border-radius: 17px;
        padding: 1.25rem 1.3rem;
        box-shadow: 0 12px 32px rgba(0, 0, 0, .20);
        margin-bottom: 1rem;
        border-left: 4px solid #60a5fa;
        backdrop-filter: blur(14px);
        transition: transform .25s ease, border-color .25s ease, box-shadow .25s ease;
        animation: softRise .55s ease both;
    }
    .metric-card::after {
        content: "";
        position: absolute;
        width: 130px; height: 130px;
        right: -55px; top: -65px;
        border-radius: 50%;
        background: rgba(96, 165, 250, .10);
        filter: blur(2px);
    }
    .metric-card:hover {
        transform: translateY(-5px);
        border-color: rgba(96, 165, 250, .55);
        box-shadow: 0 18px 38px rgba(0, 0, 0, .32);
    }
    .metric-title {
        font-size: .76rem; font-weight: 700; color: #9eb2ca;
        text-transform: uppercase; letter-spacing: .09em;
    }
    .metric-value {
        font-size: 2.15rem; line-height: 1.25; font-weight: 800;
        color: #f4f8ff; margin-top: .35rem; font-family: 'Manrope', sans-serif;
    }
    .metric-sub { font-size: .78rem; color: #91a6c0; margin-top: .35rem; }

    /* Streamlit widgets */
    .stButton > button, .stDownloadButton > button, button[kind="primary"] {
        border: 1px solid rgba(96, 165, 250, .42);
        border-radius: 11px;
        color: #f8fbff;
        background: linear-gradient(110deg, #2563eb, #0891b2);
        font-weight: 700;
        transition: transform .2s ease, box-shadow .2s ease, filter .2s ease;
        box-shadow: 0 7px 18px rgba(37, 99, 235, .20);
    }
    .stButton > button:hover, .stDownloadButton > button:hover {
        transform: translateY(-2px);
        filter: brightness(1.12);
        box-shadow: 0 11px 24px rgba(34, 211, 238, .19);
        border-color: rgba(103, 232, 249, .7);
    }
    [data-baseweb="select"] > div, [data-baseweb="input"] > div,
    [data-baseweb="textarea"] > div {
        background: rgba(12, 27, 46, .92);
        border-color: rgba(148, 163, 184, .25);
        border-radius: 10px;
        color: #edf5ff;
    }
    input, textarea { color: #edf5ff !important; }
    [data-testid="stDataFrame"], [data-testid="stTable"] {
        border: 1px solid rgba(148, 163, 184, .18);
        border-radius: 13px;
        overflow: hidden;
        background: rgba(12, 27, 46, .76);
    }
    [data-testid="stExpander"] {
        background: rgba(14, 30, 50, .72);
        border: 1px solid rgba(148, 163, 184, .18);
        border-radius: 13px;
    }
    [data-testid="stTabs"] [role="tab"] {
        color: #aebfd3;
        font-weight: 700;
        transition: color .2s ease, background .2s ease;
    }
    [data-testid="stTabs"] [role="tab"][aria-selected="true"] {
        color: #67e8f9;
        border-bottom-color: #22d3ee;
    }
    [data-testid="stAlert"] {
        border-radius: 12px;
        border: 1px solid rgba(148, 163, 184, .18);
        background: rgba(15, 34, 56, .88);
    }
    [data-testid="stMetric"] {
        background: rgba(18, 37, 60, .78);
        border: 1px solid rgba(148, 163, 184, .16);
        padding: 13px 15px;
        border-radius: 13px;
    }
    hr { border-color: rgba(148, 163, 184, .18); }

    /* Severity badges */
    .badge-critical { background:#541d2a; color:#fecaca; padding:4px 9px; border-radius:7px; font-weight:700; font-size:.78rem; border:1px solid #9f354b; }
    .badge-warning { background:#503817; color:#fde68a; padding:4px 9px; border-radius:7px; font-weight:700; font-size:.78rem; border:1px solid #9a6b27; }
    .badge-info { background:#153b60; color:#bfdbfe; padding:4px 9px; border-radius:7px; font-weight:700; font-size:.78rem; border:1px solid #326a9e; }

    /* Roster status pills */
    .pill-working { background:#124b3b; color:#bbf7d0; font-weight:700; padding:3px 7px; border-radius:5px; font-size:.75rem; }
    .pill-off { background:#263548; color:#cbd5e1; padding:3px 7px; border-radius:5px; font-size:.75rem; }
    .pill-leave { background:#542333; color:#fecdd3; font-weight:700; padding:3px 7px; border-radius:5px; font-size:.75rem; }
    .pill-holiday { background:#513b19; color:#fde68a; font-weight:700; padding:3px 7px; border-radius:5px; font-size:.75rem; }
    .pill-compoff { background:#12494b; color:#a5f3fc; font-weight:700; padding:3px 7px; border-radius:5px; font-size:.75rem; }

    /* Respect accessibility settings */
    @media (prefers-reduced-motion: reduce) {
        *, *::before, *::after {
            animation-duration: .01ms !important;
            animation-iteration-count: 1 !important;
            transition-duration: .01ms !important;
            scroll-behavior: auto !important;
            transform: none !important;
        }
    }
</style>
""", unsafe_allow_html=True)

# Compact branded header for a consistent product identity
st.markdown("""
<div style="
    display:flex; align-items:center; justify-content:space-between; gap:16px;
    padding:13px 18px; margin:0 0 22px 0; border-radius:15px;
    background:linear-gradient(100deg, rgba(17,42,69,.92), rgba(12,29,49,.78));
    border:1px solid rgba(125,170,220,.22); box-shadow:0 10px 28px rgba(0,0,0,.16);">
  <div>
    <div style="font-size:11px;letter-spacing:2px;color:#67e8f9;font-weight:800;">DATASTRAW • OPERATIONS SUITE</div>
    <div style="font-size:22px;color:#f4f8ff;font-weight:800;font-family:Manrope,sans-serif;">SMART ROSTER <span style="color:#67e8f9;">MANAGEMENT</span></div>
    <div style="font-size:12px;color:#9eb2ca;">Workforce intelligence · Scheduling · Compliance</div>
    <div style="font-size:11px;color:#67e8f9;margin-top:7px;font-weight:700;letter-spacing:.35px;">
        Prepared by Yogesh Shilawat · Computer Engineering
    </div>
  </div>
  <div style="font-size:30px; padding:10px 14px; border-radius:13px; background:rgba(34,211,238,.10);">✦</div>
</div>
""", unsafe_allow_html=True)


# ============================================================================
# SIDEBAR NAVIGATION
# ============================================================================
with st.sidebar:
    st.image("https://img.icons8.com/color/96/calendar--v1.png", width=54)
    st.title("Smart Roster")
    st.caption("DataStraw Tech Assessment System")
    st.markdown("""
    <div style="
        margin:14px 0 18px 0;padding:14px;border-radius:15px;
        background:linear-gradient(125deg,rgba(37,99,235,.22),rgba(8,145,178,.14));
        border:1px solid rgba(103,232,249,.28);
        box-shadow:0 8px 24px rgba(0,0,0,.18);">
        <div style="display:flex;align-items:center;gap:11px;">
            <div style="
                width:42px;height:42px;display:flex;align-items:center;justify-content:center;
                border-radius:13px;background:linear-gradient(135deg,#2563eb,#0891b2);
                color:white;font-size:15px;font-weight:900;box-shadow:0 5px 16px rgba(8,145,178,.3);">
                YS
            </div>
            <div>
                <div style="font-size:14px;font-weight:800;color:#f4f8ff;">Yogesh Shilawat</div>
                <div style="font-size:11px;color:#9eb2ca;">Developer · Project Showcase</div>
            </div>
        </div>
        <div style="margin-top:11px;font-size:11px;line-height:1.5;color:#c7d8eb;">
            Smart workforce operations, roster planning and compliance insights.
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")

    selected_menu = st.radio(
        "Navigation",
        [
            "📊 Executive Dashboard",
            "👥 Employee Directory",
            "🏢 Pods & Brands",
            "⚙️ Processes & Operating Rules",
            "🔗 Assignments Matrix",
            "🏖️ Leaves & Holidays",
            "📅 Monthly Roster (5-Way Views)",
            "⚠️ Live Conflict Center & Editor",
            "🔄 Change Management Simulator",
            "📥 Reports & Multi-Export",
        ],
        index=0
    )

    st.markdown("---")
    st.markdown("### 🛠️ Quick System Actions")
    col_sb1, col_sb2 = st.columns(2)
    with col_sb1:
        if st.button("🔄 Reset Data", use_container_width=True, help="Resets DB with full 32-employee benchmark dataset"):
            sample_data.reset_and_seed_database()
            st.success("Database Reset!")
            st.rerun()
    with col_sb2:
        if st.button("⚡ Audit Conflicts", use_container_width=True, help="Re-runs constraint validator on current roster"):
            # Check if roster exists
            roster = database.create_or_get_roster(11, 2026)
            validator.detect_and_store_conflicts(roster["id"])
            st.success("Audit complete!")
            st.rerun()

    st.markdown("---")
    st.caption("v1.1.0 • SQLite + Streamlit SaaS Engine")
    st.caption("Crafted for the DataStraw Tech assessment")


# Ensure default roster for November 2026 is seeded and validated
current_roster = database.create_or_get_roster(11, 2026)
entries_check = database.get_roster_entries(current_roster["id"])
if len(entries_check) == 0:
    scheduler.generate_monthly_roster(2026, 11)


# ============================================================================
# MODULE 1: EXECUTIVE DASHBOARD
# ============================================================================
if selected_menu == "📊 Executive Dashboard":
    st.title("Operations Command Center")
    st.markdown("Live operational metrics, staffing availability, and compliance health across pods.")

    sys_summary = database.get_system_summary()
    confs = database.get_conflicts_for_roster(current_roster["id"])
    crit_confs = sum(1 for c in confs if c["severity"] == "CRITICAL")
    warn_confs = sum(1 for c in confs if c["severity"] == "WARNING")

    # Top KPI Metrics Cards
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: #2563EB;">
            <div class="metric-title">Active Employees</div>
            <div class="metric-value">{sys_summary['total_employees']}</div>
            <div class="metric-sub">Distributed across {sys_summary['total_pods']} Pods</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: #059669;">
            <div class="metric-title">D2C Client Brands</div>
            <div class="metric-value">{sys_summary['total_brands']}</div>
            <div class="metric-sub">{sys_summary['single_resource_brands']} Single-Resource (~80%) • {sys_summary['multi_resource_brands']} Multi</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: #DC2626;">
            <div class="metric-title">Critical Conflicts</div>
            <div class="metric-value" style="color: #DC2626;">{crit_confs}</div>
            <div class="metric-sub">Zero coverage or leave clashes</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: #D97706;">
            <div class="metric-title">Warning Alerts</div>
            <div class="metric-value" style="color: #D97706;">{warn_confs}</div>
            <div class="metric-sub">Understaffing / Off-day shifts</div>
        </div>
        """, unsafe_allow_html=True)

    # Operational Visualizations
    st.markdown("### 📈 Pod Workload & Distribution")
    col_chart1, col_chart2 = st.columns([2, 1])

    with col_chart1:
        pods = database.get_all_pods()
        pod_df = pd.DataFrame(pods)
        if not pod_df.empty:
            st.bar_chart(
                pod_df.set_index("name")[["employee_count", "brand_count"]],
                use_container_width=True
            )
            st.caption("Employee & Brand Distribution per Pod")

    with col_chart2:
        brands = database.get_all_brands()
        b_df = pd.DataFrame(brands)
        if not b_df.empty:
            pattern_counts = b_df["operating_pattern"].value_counts()
            st.write("##### Operating Calendars")
            for pat, count in pattern_counts.items():
                st.markdown(f"- **{pat.replace('_', ' ').title()}**: `{count} brands`")
            st.info("💡 **80% of brands** rely on a single dedicated resource. When that operator is off, pod reserves must provide coverage.")

    # High-Priority Conflicts Preview
    st.markdown("### 🚨 Urgent Attention Required")
    if crit_confs > 0:
        critical_items = [c for c in confs if c["severity"] == "CRITICAL"][:5]
        for c in critical_items:
            st.error(f"**{c['date']}** | **{c.get('brand_name', 'Brand')}** ({c.get('process_name', 'CS')}): {c['message']} → *Fix: {c.get('suggested_fix', '')}*")
    else:
        st.success("🎉 No critical coverage gaps detected! All client operating hours are fully staffed.")


# ============================================================================
# MODULE 2: EMPLOYEE DIRECTORY
# ============================================================================
elif selected_menu == "👥 Employee Directory":
    st.title("Employee Management Directory")
    st.markdown("Maintain staff rosters, pod affiliations, weekly-off configurations, and operational roles.")

    employees = database.get_all_employees()
    pods = database.get_all_pods()
    pod_names = ["All Pods"] + [p["name"] for p in pods]

    col_flt1, col_flt2, col_flt3 = st.columns([2, 2, 2])
    with col_flt1:
        pod_filter = st.selectbox("Filter by Pod", pod_names)
    with col_flt2:
        role_filter = st.selectbox("Filter by Role", ["All Roles", "Pod Lead", "Senior Agent", "Agent"])
    with col_flt3:
        search_query = st.text_input("Search Name / Email", "")

    filtered = employees
    if pod_filter != "All Pods":
        filtered = [e for e in filtered if e["pod_name"] == pod_filter]
    if role_filter != "All Roles":
        filtered = [e for e in filtered if e["role"] == role_filter]
    if search_query:
        q = search_query.lower()
        filtered = [e for e in filtered if q in e["name"].lower() or q in e["email"].lower()]

    st.write(f"Showing **{len(filtered)}** of **{len(employees)}** employees")
    
    df_emps = pd.DataFrame(filtered)
    if not df_emps.empty:
        display_cols = ["id", "name", "email", "pod_name", "role", "weekly_off_day_1", "weekly_off_day_2", "max_hours_week"]
        st.dataframe(
            df_emps[display_cols].rename(columns={
                "id": "ID", "name": "Name", "email": "Email", "pod_name": "Pod",
                "role": "Role", "weekly_off_day_1": "Off Day 1", "weekly_off_day_2": "Off Day 2",
                "max_hours_week": "Max Hrs/Wk"
            }),
            use_container_width=True,
            hide_index=True
        )

    # Add / Edit Employee Expander
    with st.expander("➕ Add New Employee"):
        with st.form("add_employee_form"):
            col_e1, col_e2 = st.columns(2)
            with col_e1:
                new_name = st.text_input("Full Name", "Ankit Sharma")
                new_email = st.text_input("Corporate Email", "ankit.sharma@datastraw.io")
                pod_map = {p["name"]: p["id"] for p in pods}
                new_pod = st.selectbox("Pod Assignment", list(pod_map.keys()))
            with col_e2:
                new_role = st.selectbox("Designation / Role", ["Agent", "Senior Agent", "Pod Lead"])
                days_list = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
                new_off1 = st.selectbox("Weekly Off 1", days_list, index=0)
                new_off2 = st.selectbox("Weekly Off 2 (Optional)", ["None"] + days_list, index=1)
            
            submit_emp = st.form_submit_button("Register Employee")
            if submit_emp:
                off2_val = None if new_off2 == "None" else new_off2
                database.add_employee(new_name, new_email, pod_map[new_pod], new_role, new_off1, off2_val)
                st.success(f"Employee {new_name} added successfully!")
                st.rerun()


# ============================================================================
# MODULE 3: PODS & BRANDS
# ============================================================================
elif selected_menu == "🏢 Pods & Brands":
    st.title("Pods & D2C Client Brand Management")
    st.markdown("Configure operational pods, lead oversight, brand SLAs, and operating patterns.")

    tab_pods, tab_brands = st.tabs(["Operational Pods", "D2C Client Brands"])

    with tab_pods:
        pods = database.get_all_pods()
        cols = st.columns(len(pods))
        for i, p in enumerate(pods):
            with cols[i]:
                st.markdown(f"""
                <div class="metric-card" style="border-left-color: #3B82F6;">
                    <div class="metric-title">{p['name']}</div>
                    <div class="metric-value" style="font-size: 1.4rem;">Lead: {p.get('lead_name', 'Unassigned')}</div>
                    <div class="metric-sub">👥 {p['employee_count']} Employees • 🏷️ {p['brand_count']} Brands</div>
                    <div style="font-size: 0.75rem; color: #64748B; margin-top: 0.5rem;">{p.get('description', '')}</div>
                </div>
                """, unsafe_allow_html=True)

    with tab_brands:
        brands = database.get_all_brands()
        df_b = pd.DataFrame(brands)
        if not df_b.empty:
            df_b["Type"] = df_b["is_single_resource"].apply(lambda x: "Single-Resource (~80%)" if x == 1 else "Multi-Resource (~20%)")
            st.dataframe(
                df_b[["id", "name", "pod_name", "Type", "operating_pattern", "assigned_emp_count", "description"]].rename(columns={
                    "id": "ID", "name": "Brand Name", "pod_name": "Pod", "operating_pattern": "Operating Pattern",
                    "assigned_emp_count": "Assigned Staff", "description": "Scope / Description"
                }),
                use_container_width=True,
                hide_index=True
            )

        with st.expander("➕ Onboard New Brand"):
            with st.form("add_brand_form"):
                col_b1, col_b2 = st.columns(2)
                with col_b1:
                    b_name = st.text_input("Brand Name", "AeroDrop Logistics")
                    pod_opts = {p["name"]: p["id"] for p in pods}
                    b_pod = st.selectbox("Assign to Pod", list(pod_opts.keys()))
                with col_b2:
                    b_pattern = st.selectbox("Operating Pattern", ["365_days", "daily_ex_holidays", "sundays_holidays_off"])
                    b_type = st.radio("Staffing Architecture", ["Single-Resource (Dedicated Solo)", "Multi-Resource (Shared Team)"])
                    b_desc = st.text_input("Description", "D2C express consumer brand")

                if st.form_submit_button("Create Brand"):
                    is_single = 1 if "Single" in b_type else 0
                    database.add_brand(b_name, pod_opts[b_pod], b_pattern, b_desc, is_single)
                    st.success(f"Brand '{b_name}' successfully configured!")
                    st.rerun()


# ============================================================================
# MODULE 4: PROCESSES & OPERATING RULES
# ============================================================================
elif selected_menu == "⚙️ Processes & Operating Rules":
    st.title("Business Processes & Operating Rules")
    st.markdown("Define process categories and brand-specific operational calendars and minimum daily staffing requirements.")

    processes = database.get_all_processes()
    rules = database.get_all_rules()

    col_p1, col_p2 = st.columns([1, 2])
    with col_p1:
        st.write("##### Core Supported Processes")
        for p in processes:
            st.markdown(f"**{p['code']} — {p['name']}**")
            st.caption(p["description"])

    with col_p2:
        st.write("##### Brand-Process Rules & Staffing Quotas")
        if rules:
            df_rules = pd.DataFrame(rules)
            st.dataframe(
                df_rules[["id", "brand_name", "process_name", "operating_pattern", "min_staff_req", "hours_per_day"]].rename(columns={
                    "id": "Rule ID", "brand_name": "Brand", "process_name": "Process",
                    "operating_pattern": "Operating Pattern", "min_staff_req": "Min Staff", "hours_per_day": "Hours/Day"
                }),
                use_container_width=True,
                hide_index=True
            )

    with st.expander("⚙️ Configure Brand Process Rule"):
        with st.form("set_rule_form"):
            brands = database.get_all_brands()
            b_map = {b["name"]: b["id"] for b in brands}
            p_map = {p["name"]: p["id"] for p in processes}
            
            c_r1, c_r2 = st.columns(2)
            with c_r1:
                sel_b = st.selectbox("Select Brand", list(b_map.keys()))
                sel_p = st.selectbox("Select Process", list(p_map.keys()))
            with c_r2:
                sel_op = st.selectbox("Process Operating Pattern", ["365_days", "daily_ex_holidays", "sundays_holidays_off"])
                sel_min = st.number_input("Minimum Required Staff (Daily Quota)", min_value=1, max_value=10, value=1)
            
            if st.form_submit_button("Save Rule"):
                database.set_brand_process_rule(b_map[sel_b], p_map[sel_p], sel_op, sel_min)
                st.success("Rule updated successfully!")
                st.rerun()


# ============================================================================
# MODULE 5: ASSIGNMENTS MATRIX
# ============================================================================
elif selected_menu == "🔗 Assignments Matrix":
    st.title("Employee-to-Brand & Process Assignments")
    st.markdown("Multi-brand and process skill allocation matrix. Distinguishes primary operators from backup/cross-coverage.")

    assignments = database.get_all_assignments()
    df_a = pd.DataFrame(assignments)
    
    col_af1, col_af2 = st.columns(2)
    with col_af1:
        brand_list = ["All Brands"] + sorted(list({a["brand_name"] for a in assignments}))
        sel_brand_filter = st.selectbox("Filter Brand", brand_list)
    with col_af2:
        proc_list = ["All Processes"] + sorted(list({a["process_name"] for a in assignments}))
        sel_proc_filter = st.selectbox("Filter Process", proc_list)

    filtered_a = assignments
    if sel_brand_filter != "All Brands":
        filtered_a = [a for a in filtered_a if a["brand_name"] == sel_brand_filter]
    if sel_proc_filter != "All Processes":
        filtered_a = [a for a in filtered_a if a["process_name"] == sel_proc_filter]

    df_filtered_a = pd.DataFrame(filtered_a)
    if not df_filtered_a.empty:
        df_filtered_a["Role Type"] = df_filtered_a["is_primary"].apply(lambda x: "Primary Assigned" if x == 1 else "Secondary / Backup")
        st.dataframe(
            df_filtered_a[["id", "employee_name", "pod_name", "brand_name", "process_code", "Role Type"]].rename(columns={
                "id": "Assignment ID", "employee_name": "Employee", "pod_name": "Pod",
                "brand_name": "Brand", "process_code": "Process", "Role Type": "Assignment Type"
            }),
            use_container_width=True,
            hide_index=True
        )

    with st.expander("➕ Add Assignment Mapping"):
        with st.form("add_assignment_form"):
            emps = database.get_all_employees()
            brands = database.get_all_brands()
            procs = database.get_all_processes()
            e_map = {f"{e['name']} ({e['pod_name']})": e["id"] for e in emps}
            b_map = {b["name"]: b["id"] for b in brands}
            pr_map = {f"{p['name']} ({p['code']})": p["id"] for p in procs}

            c_as1, c_as2 = st.columns(2)
            with c_as1:
                as_emp = st.selectbox("Employee", list(e_map.keys()))
                as_brand = st.selectbox("Brand", list(b_map.keys()))
            with c_as2:
                as_proc = st.selectbox("Process", list(pr_map.keys()))
                as_primary = st.radio("Primary Responsibility?", ["Primary Dedicated (1)", "Secondary Backup / Reserve (0)"])

            if st.form_submit_button("Assign Employee"):
                is_p = 1 if "Primary" in as_primary else 0
                database.add_assignment(e_map[as_emp], b_map[as_brand], pr_map[as_proc], is_p)
                st.success("Assignment linked!")
                st.rerun()


# ============================================================================
# MODULE 6: LEAVES & PUBLIC HOLIDAYS
# ============================================================================
elif selected_menu == "🏖️ Leaves & Holidays":
    st.title("Planned Leaves & Public Holidays Calendar")
    st.markdown("Track approved leaves, compensatory off credits, and recognized gazetted public holidays.")

    tab_leaves, tab_holidays = st.tabs(["Employee Leaves & Comp-Offs", "Public Holidays"])

    with tab_leaves:
        leaves = database.get_all_leaves()
        df_l = pd.DataFrame(leaves)
        if not df_l.empty:
            st.dataframe(
                df_l[["id", "employee_name", "pod_name", "leave_date", "leave_type", "status", "reason"]].rename(columns={
                    "id": "ID", "employee_name": "Employee", "pod_name": "Pod",
                    "leave_date": "Date", "leave_type": "Leave Type", "status": "Approval Status", "reason": "Reason / Note"
                }),
                use_container_width=True,
                hide_index=True
            )

        with st.expander("➕ Submit / Approve Planned Leave"):
            with st.form("add_leave_form"):
                emps = database.get_all_employees()
                e_map = {f"{e['name']} ({e['pod_name']})": e["id"] for e in emps}
                c_lv1, c_lv2 = st.columns(2)
                with c_lv1:
                    l_emp = st.selectbox("Employee", list(e_map.keys()))
                    l_date = st.date_input("Leave Date", value=date(2026, 11, 12))
                with c_lv2:
                    l_type = st.selectbox("Type", ["Privilege Leave", "Casual Leave", "Sick Leave", "Comp-Off"])
                    l_reason = st.text_input("Reason", "Personal planned leave")

                if st.form_submit_button("Approve Leave"):
                    database.add_leave(e_map[l_emp], l_date.strftime("%Y-%m-%d"), l_type, "APPROVED", l_reason)
                    st.success("Leave approved and recorded!")
                    st.rerun()

    with tab_holidays:
        holidays = database.get_all_holidays()
        df_h = pd.DataFrame(holidays)
        if not df_h.empty:
            st.dataframe(
                df_h[["id", "holiday_date", "name", "is_mandatory_off"]].rename(columns={
                    "id": "ID", "holiday_date": "Date", "name": "Holiday Name", "is_mandatory_off": "Mandatory Off"
                }),
                use_container_width=True,
                hide_index=True
            )


# ============================================================================
# MODULE 7: MONTHLY ROSTER (5-WAY VIEWS)
# ============================================================================
elif selected_menu == "📅 Monthly Roster (5-Way Views)":
    st.title("Monthly Operational Roster")
    st.markdown("Generate, inspect, and analyze the full multi-dimensional monthly schedule across 5 distinct lenses.")

    col_ctrl1, col_ctrl2, col_ctrl3 = st.columns([2, 2, 2])
    with col_ctrl1:
        sel_month = st.selectbox("Target Month", list(range(1, 13)), index=10, format_func=lambda m: f"{calendar.month_name[m]} ({m})")
    with col_ctrl2:
        sel_year = st.selectbox("Target Year", [2026, 2027], index=0)
    with col_ctrl3:
        st.write("")
        st.write("")
        if st.button("⚡ Regenerate Roster", use_container_width=True):
            with st.spinner("Executing deterministic constraint solver..."):
                res = scheduler.generate_monthly_roster(sel_year, sel_month)
                st.success(f"Generated {res['total_entries']} entries with {res['conflicts']['total']} flagged conflicts.")
                st.rerun()

    roster = database.create_or_get_roster(sel_month, sel_year)
    entries = database.get_roster_entries(roster["id"])

    num_days = calendar.monthrange(sel_year, sel_month)[1]
    days_cols = [f"{sel_year}-{sel_month:02d}-{d:02d}" for d in range(1, num_days + 1)]

    # 5 Tabbed Stakeholder Views
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "1. 🏢 Company-Wide View",
        "2. 👥 Pod-Wise View",
        "3. 🏷️ Brand-Wise View",
        "4. ⚙️ Process-Wise View",
        "5. 👤 Individual Employee View"
    ])

    # -------------------------------------------------------------
    # VIEW 1: Company-Wide View
    # -------------------------------------------------------------
    with tab1:
        st.write("##### Full Monthly Team Roster Matrix")
        st.markdown("""
        **Legend**: 
        <span class="pill-working">WORKING</span> Regular Shift &nbsp;|&nbsp; 
        <span class="pill-off">WEEKLY OFF</span> Off Day &nbsp;|&nbsp; 
        <span class="pill-leave">LEAVE</span> Approved Leave &nbsp;|&nbsp; 
        <span class="pill-holiday">HOLIDAY</span> Public Holiday &nbsp;|&nbsp; 
        <span class="pill-compoff">COMP-OFF</span> Comp-off Duty
        """, unsafe_allow_html=True)

        # Pivot to Employee x Days
        matrix_data = []
        emp_groups = {}
        for e in entries:
            emp_groups.setdefault(e["employee_name"], {})[e["date"]] = e["status"]

        emps = database.get_all_employees()
        for emp in emps:
            row = {"Employee": emp["name"], "Pod": emp["pod_name"], "Role": emp["role"]}
            e_dates = emp_groups.get(emp["name"], {})
            for d in range(1, num_days + 1):
                d_str = f"{sel_year}-{sel_month:02d}-{d:02d}"
                row[f"{d:02d}"] = e_dates.get(d_str, "OFF")
            matrix_data.append(row)

        df_company = pd.DataFrame(matrix_data)
        st.dataframe(df_company, use_container_width=True, hide_index=True)

    # -------------------------------------------------------------
    # VIEW 2: Pod-Wise View
    # -------------------------------------------------------------
    with tab2:
        pods = database.get_all_pods()
        sel_pod = st.selectbox("Select Pod to Inspect", [p["name"] for p in pods])
        pod_emps = [emp for emp in emps if emp["pod_name"] == sel_pod]
        pod_names_set = {emp["name"] for emp in pod_emps}

        st.info(f"Oversight Lead: **{next((p.get('lead_name', 'Unassigned') for p in pods if p['name'] == sel_pod), 'None')}**")
        df_pod = df_company[df_company["Employee"].isin(pod_names_set)]
        st.dataframe(df_pod, use_container_width=True, hide_index=True)

    # -------------------------------------------------------------
    # VIEW 3: Brand-Wise View
    # -------------------------------------------------------------
    with tab3:
        brands = database.get_all_brands()
        sel_brand_name = st.selectbox("Select D2C Brand", [b["name"] for b in brands])
        sel_brand = next(b for b in brands if b["name"] == sel_brand_name)
        
        st.markdown(f"**Operating Pattern**: `{sel_brand['operating_pattern']}` | **Pod**: `{sel_brand['pod_name']}` | **Architecture**: `{'Single-Resource (~80%)' if sel_brand['is_single_resource'] else 'Multi-Resource'}`")

        # Daily coverage calculation
        b_entries = [e for e in entries if e["brand_id"] == sel_brand["id"]]
        coverage_rows = []
        for d in range(1, num_days + 1):
            d_str = f"{sel_year}-{sel_month:02d}-{d:02d}"
            dt = date(sel_year, sel_month, d)
            working_on_day = [e["employee_name"] for e in b_entries if e["date"] == d_str and e["status"] == "WORKING"]
            count = len(working_on_day)
            status_tag = "✅ Met" if count > 0 else "❌ Zero Coverage"
            coverage_rows.append({
                "Date": d_str,
                "Day": dt.strftime("%A"),
                "Staff On Duty": count,
                "Status": status_tag,
                "Assigned Agents": ", ".join(working_on_day) if working_on_day else "None"
            })
        
        df_cov = pd.DataFrame(coverage_rows)
        st.dataframe(df_cov, use_container_width=True, hide_index=True)

    # -------------------------------------------------------------
    # VIEW 4: Process-Wise View
    # -------------------------------------------------------------
    with tab4:
        processes = database.get_all_processes()
        sel_proc = st.selectbox("Select Business Process", [p["name"] for p in processes])
        sel_proc_obj = next(p for p in processes if p["name"] == sel_proc)

        p_entries = [e for e in entries if e["process_id"] == sel_proc_obj["id"] and e["status"] == "WORKING"]
        st.write(f"Showing daily active staff deployed on **{sel_proc}** ({sel_proc_obj['code']})")

        proc_daily = []
        for d in range(1, num_days + 1):
            d_str = f"{sel_year}-{sel_month:02d}-{d:02d}"
            agents = [e["employee_name"] for e in p_entries if e["date"] == d_str]
            proc_daily.append({"Date": d_str, "Working Staff Count": len(agents), "Agents": ", ".join(agents)})

        st.dataframe(pd.DataFrame(proc_daily), use_container_width=True, hide_index=True)

    # -------------------------------------------------------------
    # VIEW 5: Individual Employee View
    # -------------------------------------------------------------
    with tab5:
        emp_names = [emp["name"] for emp in emps]
        sel_emp_name = st.selectbox("Select Employee", emp_names)
        sel_emp = next(e for e in emps if e["name"] == sel_emp_name)
        
        e_entries = [e for e in entries if e["employee_name"] == sel_emp_name]
        st.markdown(f"**Pod**: `{sel_emp['pod_name']}` | **Role**: `{sel_emp['role']}` | **Weekly Offs**: `{sel_emp['weekly_off_day_1']}` & `{sel_emp['weekly_off_day_2'] or 'None'}`")

        c_stat1, c_stat2, c_stat3, c_stat4 = st.columns(4)
        c_stat1.metric("Working Days", sum(1 for e in e_entries if e["status"] == "WORKING"))
        c_stat2.metric("Weekly Offs", sum(1 for e in e_entries if e["status"] == "WEEKLY OFF"))
        c_stat3.metric("Approved Leaves", sum(1 for e in e_entries if e["status"] == "LEAVE"))
        c_stat4.metric("Holidays / Comp-Offs", sum(1 for e in e_entries if e["status"] in ["HOLIDAY", "COMP-OFF"]))

        st.dataframe(
            pd.DataFrame(e_entries)[["date", "brand_name", "process_name", "status", "notes"]].rename(columns={
                "date": "Date", "brand_name": "Brand", "process_name": "Process", "status": "Shift Status", "notes": "Schedule Notes"
            }),
            use_container_width=True,
            hide_index=True
        )


# ============================================================================
# MODULE 8: CONFLICT CENTER & ROSTER EDITOR
# ============================================================================
elif selected_menu == "⚠️ Live Conflict Center & Editor":
    st.title("Compliance & Conflict Resolution Center")
    st.markdown("Automated constraint audit engine flagging SLA violations, understaffing, and employee clashes.")

    confs = database.get_conflicts_for_roster(current_roster["id"])
    crit_cnt = sum(1 for c in confs if c["severity"] == "CRITICAL")
    warn_cnt = sum(1 for c in confs if c["severity"] == "WARNING")

    col_cf1, col_cf2, col_cf3 = st.columns(3)
    col_cf1.metric("Total Flagged Exceptions", len(confs))
    col_cf2.metric("Critical Gaps (Must Resolve)", crit_cnt, delta=f"-{crit_cnt}" if crit_cnt > 0 else "0", delta_color="inverse")
    col_cf3.metric("Warnings (Review Required)", warn_cnt)

    col_flt_c1, col_flt_c2 = st.columns(2)
    with col_flt_c1:
        sev_filter = st.selectbox("Filter by Severity", ["All Severities", "CRITICAL", "WARNING", "INFO"])
    with col_flt_c2:
        brands = database.get_all_brands()
        b_names = ["All Brands"] + [b["name"] for b in brands]
        brand_c_filter = st.selectbox("Filter by Brand Impact", b_names)

    filtered_confs = confs
    if sev_filter != "All Severities":
        filtered_confs = [c for c in filtered_confs if c["severity"] == sev_filter]
    if brand_c_filter != "All Brands":
        filtered_confs = [c for c in filtered_confs if c.get("brand_name") == brand_c_filter]

    st.write(f"Showing **{len(filtered_confs)}** exceptions:")

    df_c = pd.DataFrame(filtered_confs)
    if not df_c.empty:
        st.dataframe(
            df_c[["id", "date", "severity", "conflict_type", "brand_name", "process_name", "message", "suggested_fix"]].rename(columns={
                "id": "ID", "date": "Date", "severity": "Severity", "conflict_type": "Violation Type",
                "brand_name": "Brand", "process_name": "Process", "message": "Constraint Violation", "suggested_fix": "Recommended Resolution"
            }),
            use_container_width=True,
            hide_index=True
        )

    st.markdown("---")
    st.markdown("### ✏️ Interactive Shift Override & Cell Editor")
    with st.expander("🛠️ Manual Schedule Adjustment"):
        st.caption("Directly modify any employee's schedule on a specific date. The system will revalidate the entire roster immediately.")
        with st.form("manual_override_form"):
            col_m1, col_m2 = st.columns(2)
            emps = database.get_all_employees()
            emp_dict = {f"{e['name']} ({e['pod_name']})": e["id"] for e in emps}
            brand_dict = {b["name"]: b["id"] for b in brands}
            procs = database.get_all_processes()
            proc_dict = {p["name"]: p["id"] for p in procs}

            with col_m1:
                edit_emp = st.selectbox("Select Employee", list(emp_dict.keys()))
                edit_date = st.date_input("Target Date", value=date(2026, 11, 12))
                new_status = st.selectbox("Set Shift Status", ["WORKING", "WEEKLY OFF", "LEAVE", "HOLIDAY", "COMP-OFF"])
            with col_m2:
                new_b = st.selectbox("Assign Brand", ["None"] + list(brand_dict.keys()))
                new_p = st.selectbox("Assign Process", ["None"] + list(proc_dict.keys()))
                edit_note = st.text_input("Override Reason", "Manual manager override")

            if st.form_submit_button("Apply Override & Revalidate"):
                b_val = None if new_b == "None" else brand_dict[new_b]
                p_val = None if new_p == "None" else proc_dict[new_p]
                
                # Check existing entry
                entries = database.get_roster_entries(current_roster["id"])
                d_str = edit_date.strftime("%Y-%m-%d")
                eid = emp_dict[edit_emp]
                match = next((e for e in entries if e["date"] == d_str and e["employee_id"] == eid), None)
                
                if match:
                    database.update_roster_entry(match["id"], new_status, b_val, p_val, is_override=1, notes=edit_note)
                else:
                    with database.get_connection() as conn:
                        conn.execute("""
                            INSERT INTO roster_entries (roster_id, employee_id, date, brand_id, process_id, status, is_override, notes)
                            VALUES (?, ?, ?, ?, ?, ?, 1, ?)
                        """, (current_roster["id"], eid, d_str, b_val, p_val, new_status, edit_note))
                        conn.commit()

                # Revalidate
                validator.detect_and_store_conflicts(current_roster["id"])
                st.success("Override applied and roster audited!")
                st.rerun()


# ============================================================================
# MODULE 9: CHANGE MANAGEMENT SIMULATOR (ASSESSMENT SCENARIO)
# ============================================================================
elif selected_menu == "🔄 Change Management Simulator":
    st.title("Dynamic Change Management Simulator")
    st.markdown("""
    **Assessment Core Workflow Demonstration (Section 3.F & 7)**:
    Simulates the critical real-world scenario where the sole operator of a **single-resource brand**
    becomes unavailable on a required working day, leaving client SLAs at risk.
    """)

    st.info("💡 **Demonstration Scenario**: Rahul Mehta is the sole dedicated operator managing all processes for **GlowSkin Luxury** (Pod Alpha). GlowSkin operates 365 days a year.")

    col_sim1, col_sim2 = st.columns([1, 1])

    with col_sim1:
        st.write("#### Step 1: Simulated Unavailability")
        st.write("Rahul Mehta has taken approved leave on **2026-11-12** (Thursday).")
        
        # Check current status of GlowSkin on 2026-11-12
        confs = database.get_conflicts_for_roster(current_roster["id"])
        glowskin_confs = [c for c in confs if c["date"] == "2026-11-12" and c.get("brand_name") == "GlowSkin Luxury"]

        if glowskin_confs:
            st.error(f"🚨 **CRITICAL COVERAGE GAP DETECTED!**")
            for c in glowskin_confs:
                st.markdown(f"- **{c['conflict_type']}**: {c['message']}")
            st.caption("Single-resource brand is currently unstaffed. Client SLA breach imminent.")
        else:
            st.success("✅ GlowSkin Luxury has active coverage on 2026-11-12.")

    with col_sim2:
        st.write("#### Step 2: Automated Backup Recommendations")
        # GlowSkin brand ID = 1, CS process ID = 1
        recs = validator.get_backup_recommendations(brand_id=1, process_id=1, date_str="2026-11-12", roster_id=current_roster["id"])
        
        st.write(f"Identified **{len(recs)}** eligible staff members:")
        for r in recs[:3]:
            st.markdown(f"""
            <div style="background: #F8FAFC; border: 1px solid #E2E8F0; padding: 10px; border-radius: 8px; margin-bottom: 8px;">
                <strong>{r['name']}</strong> ({r['role']}) — <span style="color: #2563EB; font-weight: 700;">Score: {r['score']}/100</span><br>
                <small style="color: #64748B;">{r['pod_name']} • Current Status: <strong>{r['current_status']}</strong></small><br>
                <small style="color: #059669;">{r['reason']}</small>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")
    st.write("#### Step 3: Execute Backup Reassignment")
    col_act1, col_act2 = st.columns(2)
    with col_act1:
        cand_dict = {f"{r['name']} (Score: {r['score']})": r["employee_id"] for r in recs}
        sel_cand = st.selectbox("Select Recommended Backup Resource", list(cand_dict.keys()), index=0)
    with col_act2:
        st.write("")
        st.write("")
        if st.button("🚀 Reassign & Revalidate Roster", use_container_width=True, type="primary"):
            chosen_id = cand_dict[sel_cand]
            validator.resolve_conflict_reassign(
                roster_id=current_roster["id"],
                date_str="2026-11-12",
                brand_id=1,
                process_id=1,
                backup_employee_id=chosen_id,
                notes=f"Reassigned as backup for GlowSkin via Change Management"
            )
            st.success(f"🎉 Coverage restored! Roster revalidated automatically.")
            st.balloons()
            st.rerun()


# ============================================================================
# MODULE 10: REPORTS & MULTI-FORMAT EXPORT
# ============================================================================
elif selected_menu == "📥 Reports & Multi-Export":
    st.title("Operational Reports & Data Export")
    st.markdown("Generate formatted Excel workbooks (.xlsx) with styled color highlights and CSV exports.")

    roster = current_roster
    excel_bytes = exporter.export_roster_to_excel(roster["id"], roster["month"], roster["year"])
    csv_roster = exporter.export_roster_to_csv(roster["id"])
    csv_confs = exporter.export_conflicts_to_csv(roster["id"])

    col_exp1, col_exp2, col_exp3 = st.columns(3)
    with col_exp1:
        st.download_button(
            label="📊 Download Excel Workbook (.xlsx)",
            data=excel_bytes,
            file_name=f"Smart_Roster_November_{roster['year']}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
        st.caption("Multi-sheet: Monthly Roster, Brand Coverage, Conflicts Audit & Employee KPIs.")

    with col_exp2:
        st.download_button(
            label="📄 Download Roster Entries (CSV)",
            data=csv_roster,
            file_name=f"Roster_Entries_{roster['month']}_{roster['year']}.csv",
            mime="text/csv",
            use_container_width=True
        )
        st.caption("Raw tabular shift records for external reporting or BI tools.")

    with col_exp3:
        st.download_button(
            label="⚠️ Download Conflicts Audit (CSV)",
            data=csv_confs,
            file_name=f"Roster_Conflicts_{roster['month']}_{roster['year']}.csv",
            mime="text/csv",
            use_container_width=True
        )
        st.caption("Complete compliance violations log with suggested resolutions.")

    st.markdown("---")
    st.markdown("### 📋 Executive Summary Table")
    entries = database.get_roster_entries(roster["id"])
    df_entries = pd.DataFrame(entries)
    if not df_entries.empty:
        summary_kpi = df_entries.groupby(["employee_name", "employee_pod_name", "status"]).size().unstack(fill_value=0)
        st.dataframe(summary_kpi, use_container_width=True)
