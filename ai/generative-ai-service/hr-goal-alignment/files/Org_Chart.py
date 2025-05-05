import streamlit as st
from urllib.parse import quote, unquote

from org_chart_backend import check_goal_alignment, fetch_goals_from_emp, mapping_all_employees

try:
    import graphviz
except ImportError:
    st.error("Please install graphviz package: pip install graphviz")
    st.stop()

st.title("Organization Chart")
st.markdown("Use the sidebar to adjust settings and select employees for details.")

# Get org chart data
mapping, employees_df = mapping_all_employees()
if not mapping:
    st.warning("No data available to display.")
    st.stop()

# Get all employee names
all_employees = sorted(set(mapping.keys()) | {emp for values in mapping.values() for emp in values})

# Sidebar controls
with st.sidebar:
    st.header("Chart Settings")
    orientation = st.selectbox("Layout", ["Top-Down", "Left-Right"], index=0)
    zoom_level = st.slider("Zoom Level (%)", 50, 200, 50, step=10)
    
    # Direct employee selection
    st.markdown("---")
    st.header("Select Employee")
    
    # Preloaded selectbox with all employees
    selected_employee = st.selectbox(
        "Choose an employee:", 
        [""] + all_employees,  # Add empty option at the top
        index=0
    )
    
    if selected_employee:
        if st.button("View Details"):
            st.session_state.selected_employee = selected_employee
            # Update URL parameter
            st.query_params["emp"] = quote(selected_employee)
            st.rerun()

# Store selected employee in session state
if "selected_employee" not in st.session_state:
    # Try to get from URL params first
    params = st.query_params
    emp_param = params.get("emp")
    if emp_param:
        if isinstance(emp_param, list):
            emp_param = emp_param[0]
        st.session_state.selected_employee = unquote(emp_param)
    else:
        st.session_state.selected_employee = None

# Create the graphviz chart
def create_org_chart():
    dot = graphviz.Digraph(format="svg")
    
    # Set orientation
    if orientation == "Left-Right":
        dot.attr(rankdir="LR")
    
    # Set global attributes
    dot.attr("graph")
    dot.attr("node", shape="box", style="rounded")
    
    # Add all nodes
    for node in all_employees:
        if node == st.session_state.selected_employee:
            dot.node(node, style="filled,rounded", fillcolor="#ffd966")
        else:
            dot.node(node)
    
    # Add all edges
    for manager, subordinates in mapping.items():
        for subordinate in subordinates:
            dot.edge(manager, subordinate)
    
    return dot

# Create chart
chart = create_org_chart()

# Generate SVG for zoomable display
svg_code = chart.pipe(format='svg').decode('utf-8')

# Create HTML with zoom and pan capabilities
html_chart = f"""
<div style="border:1px solid #ddd; width:100%; height:500px; overflow:auto;">
    <div style="transform:scale({zoom_level/100}); transform-origin:top left;">
        {svg_code}
    </div>
</div>
"""

# Display the chart with HTML component
st.components.v1.html(html_chart, height=520, scrolling=True)

# Show details section for selected employee
# ------------------------------------------------------------
# 📋 Employee profile & goal alignment
# ------------------------------------------------------------
if st.session_state.selected_employee:
    emp = st.session_state.selected_employee
    with st.spinner("Loading employee details...", show_time=True):
        # ── Fetch data ────────────────────────────────────────────
        manager  = next((m for m, emps in mapping.items() if emp in emps), None)
        reports  = mapping.get(emp, [])
        v_align, h_align = check_goal_alignment(employees_df, emp, manager)
        goals_df = fetch_goals_from_emp(employees_df, emp)

        # ── PROFILE HEADER ───────────────────────────────────────
        with st.container(border=True):
            head, metrics = st.columns([3, 2])

            with head:
                st.header(f"👤 {emp.splitlines()[0]}")
                title = emp.splitlines()[1][1:-1] if len(emp.splitlines()) > 1 else ""
                st.caption(title)

                rel_emp = ""
                if manager:
                    m_name = manager.split('(')[0]
                    rel_emp = rel_emp + f"**Manager:**  {m_name} "
                if len(reports) > 0:
                    rel_emp = rel_emp + f"&emsp;|&emsp; **Direct reports:**  {len(reports)}"

                st.write(rel_emp, unsafe_allow_html=True)

            with metrics:
                # side-by-side animated metrics
                if v_align:
                    st.metric("Vertical alignment",   f"{v_align}% ", f"{100-v_align}%")
                if h_align:
                    st.metric("Horizontal alignment", f"{h_align}% ", f"{100-h_align}%")

            # animated progress bars look slick and let the user
            if v_align:
                st.progress(v_align / 100.0, text="Vertical goal alignment")
            if h_align:
                st.progress(h_align / 100.0, text="Horizontal goal alignment")

        # ------------------------------------------------------------
        # 🎯  Goal quality & list  (robust, no KeyErrors)
        # ------------------------------------------------------------
        SMART_COL   = "smart"    # original column
        LABEL_COL   = "Quality"  # new column for the emoji chip

        # --- 1. create a Boolean mask -------------------------------
        mask = goals_df[SMART_COL].astype(str).str.lower().isin({"yes", "true", "smart"})
        goals_pretty = goals_df.copy()
        goals_pretty[LABEL_COL] = mask.map({True: "✅ SMART", False: "⚪️ Not SMART"})
        goals_pretty.drop(columns=[SMART_COL], inplace=True)

        # move the chip to the front
        first = goals_pretty.pop(LABEL_COL)
        goals_pretty.insert(0, LABEL_COL, first)

        # --- 2. quick KPI -------------------------------------------
        total, good = len(goals_pretty), mask.sum()
        pct_good    = int(good / total * 100) if total else 0

        c_num, c_bar = st.columns([1, 4])
        with c_num:
            st.metric("SMART goals", f"{good}/{total}", f"{pct_good}%")
        with c_bar:
            st.progress(pct_good / 100, text=f"{pct_good}% SMART")

        st.divider()

        # --- 3. style just the chip column --------------------------
        def chip_style(val):
            return (
                "background-color:#d4edda;font-weight:bold"
                if "✅" in val
                else "background-color:#f8d7da;font-weight:bold"
            )

        styled = goals_pretty.style.applymap(chip_style, subset=[LABEL_COL])
        st.dataframe(styled, use_container_width=True, hide_index=True)
