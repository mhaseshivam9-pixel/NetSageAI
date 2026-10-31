import streamlit as st
import csv
import os
from datetime import datetime

from checker import check_rules
from ai_engine import diagnose


# ============================================================
# PAGE CONFIGURATION & INITIALIZATION
# ============================================================

st.set_page_config(
    page_title="NetSage Network Diagnostics",
    page_icon="🖥️",
    layout="wide"
)

# Custom CSS for professional, clean Cisco NOC / Enterprise theme
st.markdown(
    """
    <style>
    /* Main body background & fonts */
    .main {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    
    /* Clean headers */
    h1, h2, h3, h4 {
        color: #1E293B;
        font-weight: 600;
        letter-spacing: -0.02em;
    }
    
    /* Top banner */
    .top-header {
        background-color: #0F172A;
        color: #F8FAFC;
        padding: 20px 24px;
        border-radius: 8px;
        margin-bottom: 20px;
        border-left: 5px solid #0284C7;
    }
    .top-header h2 {
        color: #FFFFFF;
        margin: 0;
        font-size: 1.5rem;
    }
    .top-header p {
        color: #94A3B8;
        margin: 4px 0 0 0;
        font-size: 0.95rem;
    }

    /* Terminal output block */
    pre, code {
        font-family: 'Consolas', 'Menlo', 'Monaco', 'Courier New', monospace !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# REVIEW LOGGING FUNCTION
# ============================================================

def save_review(case_id, decision, correction, notes):

    diagnosis = st.session_state.get("diagnosis", {})
    symptom = st.session_state.get("symptom", "")
    topology = st.session_state.get("topology_context", "")

    file_exists = os.path.exists("review_log.csv")

    with open("review_log.csv", "a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        if not file_exists or os.path.getsize("review_log.csv") == 0:
            writer.writerow([
                "case_id",
                "date_time",
                "symptom",
                "topology_context",
                "ai_root_cause",
                "ai_confidence",
                "ai_osi_layer",
                "ai_evidence",
                "ai_next_command",
                "human_decision",
                "human_correction",
                "reviewer_notes"
            ])

        writer.writerow([
            case_id,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            symptom,
            topology,
            diagnosis.get("root_cause", ""),
            diagnosis.get("confidence", ""),
            diagnosis.get("osi_layer", ""),
            diagnosis.get("evidence", ""),
            diagnosis.get("next_command", ""),
            decision,
            correction,
            notes
        ])


# ============================================================
# TOP BANNER
# ============================================================

st.markdown(
    """
    <div class="top-header">
        <h2>NetSage Network Diagnostics Console</h2>
        <p>Cisco Packet Tracer Troubleshooting, Automated Rule Validation, and Human Authorization</p>
    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# CASE SELECTION (OUTSIDE / MAIN PAGE)
# ============================================================

cases = []
if os.path.exists("cases.csv"):
    with open("cases.csv", "r", encoding="utf-8") as f:
        cases = list(csv.DictReader(f))

case_options = ["Custom Incident (Manual)"] + [row["case_id"] for row in cases]

col_case_sel, col_case_info = st.columns([1, 2])

with col_case_sel:
    selected_case = st.selectbox(
        "Select Incident Case File",
        case_options,
        index=0
    )

if selected_case != "Custom Incident (Manual)":
    selected_row = next((r for r in cases if r.get("case_id") == selected_case), {})
    case_id = selected_row.get("case_id", "")
    symptom_default = selected_row.get("symptom", "")
    topology_default = str(selected_row.get("topology_context", ""))
    show_output_default = selected_row.get("show_output", "")
    
    with col_case_info:
        st.info(f"**Loaded Incident Case:** `{case_id}`")
else:
    case_id = "Manual-Entry"
    symptom_default = ""
    topology_default = ""
    show_output_default = ""
    with col_case_info:
        st.caption("Manual Mode: Enter custom symptoms, device topology context, and Cisco CLI capture below.")


# ============================================================
# INPUT SECTION (TWO COLUMNS)
# ============================================================

st.divider()
col_input1, col_input2 = st.columns(2)

with col_input1:
    st.subheader("1. Incident Summary & Symptom")
    symptom = st.text_input(
        "Reported Problem / Observed Symptom",
        value=symptom_default,
        placeholder="e.g., PC cannot reach Gateway / Ping failed"
    )

    st.subheader("2. Network Topology & Device Context")
    topology_context = st.text_area(
        "Device names, interface designations, and IP subnets",
        value=topology_default,
        height=130,
        placeholder="e.g., Router: R1 (Cisco 4321), Interface: GigabitEthernet0/0/0, Subnet: 192.168.1.0/24"
    )

with col_input2:
    st.subheader("3. Cisco Show Command Evidence")
    show_output = st.text_area(
        "Captured Cisco CLI output",
        value=show_output_default,
        height=240,
        placeholder="Paste output from: show ip interface brief / show ip route / show run / ipconfig"
    )

# Diagnose Action Button
analyze_button = st.button("Run Diagnostic Analysis", type="primary", use_container_width=True)

if analyze_button:
    if not symptom.strip():
        st.error("Please enter an incident symptom.")
        st.stop()

    if not show_output.strip():
        st.error("Please paste Cisco show command evidence.")
        st.stop()

    st.session_state["symptom"] = symptom
    st.session_state["topology_context"] = topology_context
    st.session_state["show_output"] = show_output
    st.session_state["case_id"] = case_id
    st.session_state["editing"] = False
    st.session_state["rejecting"] = False

    # Execute Python Rule Checker
    st.session_state["rule_results"] = check_rules(show_output)

    # Execute AI Diagnosis
    with st.spinner("Analyzing network evidence against topology context..."):
        try:
            st.session_state["diagnosis"] = diagnose(symptom, show_output, topology_context)
        except Exception as err:
            st.error("Error generating diagnostic report.")
            st.exception(err)
            st.stop()


# ============================================================
# RESULTS SECTION
# ============================================================

if "diagnosis" in st.session_state and "rule_results" in st.session_state:
    st.divider()
    st.subheader("Diagnostic Results & Analysis")

    col_res1, col_res2 = st.columns(2)

    with col_res1:
        st.markdown("**Deterministic Rule Validation (Static Checks)**")
        for finding in st.session_state["rule_results"]:
            clean_finding = finding.replace("❌ ", "").replace("⚠️ ", "").replace("✅ ", "")
            if "❌" in finding:
                st.error(clean_finding)
            elif "⚠️" in finding:
                st.warning(clean_finding)
            else:
                st.success(clean_finding)

    with col_res2:
        st.markdown("**Semantic Reasoning Engine**")
        diag = st.session_state["diagnosis"]
        
        st.markdown(f"**Root Cause:** {diag.get('root_cause', 'N/A')}")
        st.markdown(f"**OSI Layer:** `{diag.get('osi_layer', 'N/A')}` &nbsp;|&nbsp; **Confidence:** `{diag.get('confidence', 'N/A')}`")
        st.markdown(f"**Evidence Evaluated:** {diag.get('evidence', 'N/A')}")

    # Recommended CLI Verification & Fix
    st.markdown("**Recommended Verification Command**")
    st.code(st.session_state["diagnosis"].get("next_command", "show ip interface brief"), language="cisco")

    st.markdown("**Remediation Steps (Configured for Topology)**")
    fix_steps = st.session_state["diagnosis"].get("fix_steps", [])
    if fix_steps:
        for idx, step in enumerate(fix_steps, 1):
            st.markdown(f"**{idx}.** `{step}`" if any(k in step for k in ["interface", "ip", "no", "switchport", "vlan", "router", "shutdown", "clock"]) else f"**{idx}.** {step}")
    else:
        st.info("No specific remediation steps required.")

    # ========================================================
    # HUMAN REVIEW & AUTHORIZATION
    # ========================================================
    st.divider()
    st.subheader("Engineer Review & Authorization")
    st.caption("Review the recommended changes before applying configuration to network hardware.")

    col_btn1, col_btn2, col_btn3 = st.columns(3)

    with col_btn1:
        if st.button("Approve Resolution", use_container_width=True):
            save_review(
                st.session_state["case_id"],
                "Accepted",
                "",
                "Remediation verified against topology and accepted."
            )
            st.session_state["editing"] = False
            st.session_state["rejecting"] = False
            st.success("Decision logged: ACCEPTED")

    with col_btn2:
        if st.button("Modify Remediation", use_container_width=True):
            st.session_state["editing"] = True
            st.session_state["rejecting"] = False

    with col_btn3:
        if st.button("Reject & Escalate", use_container_width=True):
            st.session_state["rejecting"] = True
            st.session_state["editing"] = False

    # Edit Flow
    if st.session_state.get("editing", False):
        st.markdown("##### Modify Remediation Commands")
        correction = st.text_area(
            "Adjusted Commands",
            value="\n".join(fix_steps) if isinstance(fix_steps, list) else "",
            height=100
        )
        notes = st.text_input(
            "Engineer Notes",
            value="Adjusted interface/subnet configuration for Packet Tracer topology."
        )
        if st.button("Save Adjusted Decision"):
            if correction.strip():
                save_review(
                    st.session_state["case_id"],
                    "Edited",
                    correction,
                    notes
                )
                st.session_state["editing"] = False
                st.success("Decision logged: EDITED")
            else:
                st.warning("Please provide the modified configuration.")

    # Reject Flow
    if st.session_state.get("rejecting", False):
        st.markdown("##### Log Rejection Justification")
        rejection_notes = st.text_area(
            "Reason for Rejection",
            placeholder="e.g., Physical link issue or diagnostic inaccuracy."
        )
        if st.button("Confirm Rejection"):
            save_review(
                st.session_state["case_id"],
                "Rejected",
                "",
                rejection_notes
            )
            st.session_state["rejecting"] = False
            st.error("Decision logged: REJECTED")


# ============================================================
# AUDIT LOG DOWNLOAD
# ============================================================
st.divider()

if os.path.exists("review_log.csv") and os.path.getsize("review_log.csv") > 0:
    with open("review_log.csv", "r", encoding="utf-8") as f:
        csv_data = f.read()

    col_dl1, col_dl2 = st.columns([1, 3])
    with col_dl1:
        st.download_button(
            label="📥 Download Review Audit Log (CSV)",
            data=csv_data,
            file_name="review_log.csv",
            mime="text/csv",
            use_container_width=True
        )
    with col_dl2:
        st.caption("Export the complete history of authorized network decisions for your project submission.")
else:
    st.caption("No review records logged yet. Run a diagnostic and save a decision above to generate the log.")