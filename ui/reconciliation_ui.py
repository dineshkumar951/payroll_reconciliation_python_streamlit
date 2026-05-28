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
    # PERIOD DATE COLUMNS (accrued mode)
    # -----------------------------------

    period_begin_column = None
    period_end_column = None

    if accrued_mode:

        period_begin_column = st.selectbox(
            "Select Period Begin Date Column",
            columns,
            key="period_begin_col"
        )

        period_end_column = st.selectbox(
            "Select Period End Date Column",
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

    return (
        pay_date_column,
        period_begin_column,
        period_end_column,
        sum_columns,
        keep_columns
    )
