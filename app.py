import streamlit as st

from ui import payroll_ui
from ui import gl_ui

# ---------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------

st.set_page_config(
    page_title="Payroll Reconciliation",
    layout="wide"
)

st.title("Payroll Reconciliation Tool")

# ---------------------------------------------------
# TAB NAVIGATION
# ---------------------------------------------------

tab_payroll, tab_gl = st.tabs([
    "Payroll Reconciliation",
    "GL Reconciliation"
])

with tab_payroll:
    payroll_ui.render()

with tab_gl:
    gl_ui.render()
