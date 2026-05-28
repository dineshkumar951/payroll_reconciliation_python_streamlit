import streamlit as st


def reconciliation_selection_ui(df, accrued_mode=False):

    st.subheader("Reconciliation Configuration")

    columns = df.columns.tolist()

    # -----------------------------------
    # PAY DATE COLUMN
    # -----------------------------------

    pay_date_column = st.selectbox(
        "Select Group By Pay Date Column",
        columns,
        key="group_paydate"
    )

    # -----------------------------------
    # PERIOD DATE COLUMNS (always shown —
    # used as composite group key in both
    # normal and accrued modes)
    # -----------------------------------

    period_begin_column = st.selectbox(
        "Select Period Begin Date Column (Group By)",
        columns,
        key="period_begin_col"
    )

    period_end_column = st.selectbox(
        "Select Period End Date Column (Group By)",
        columns,
        key="period_end_col"
    )

    # -----------------------------------
    # SUM COLUMNS
    # -----------------------------------

    sum_columns = st.multiselect(
        "Select Columns To Aggregate (SUM)",
        columns,
        key="sum_columns"
    )

    # -----------------------------------
    # KEEP COLUMNS
    # -----------------------------------

    keep_columns = st.multiselect(
        "Select Additional Fields To Keep",
        columns,
        key="keep_columns"
    )

    # -----------------------------------
    # TOTAL TAX COLUMN
    # -----------------------------------

    add_total_tax = st.checkbox(
        "Add Total Tax Column",
        value=False,
        key="add_total_tax"
    )

    tax_columns = []
    if add_total_tax:
        tax_columns = st.multiselect(
            "Select Tax Columns To Sum",
            columns,
            key="tax_columns"
        )

    return (
        pay_date_column,
        period_begin_column,
        period_end_column,
        sum_columns,
        keep_columns,
        add_total_tax,
        tax_columns
    )
