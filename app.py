import datetime

import streamlit as st
import pandas as pd

from services.excel_service import (
    get_sheet_names,
    preview_sheet,
    load_sheet_data
)

from services.payroll_service import (
    get_available_years,
    filter_by_period,
    filter_for_accrued_period
)

from services.reconciliation_service import (
    generate_grouped_report,
    generate_accrued_report,
    generate_review_checks
)

from services.export_service import (
    generate_excel_file
)

from ui.preview import (
    show_columns,
    show_data_preview
)

from ui.reconciliation_ui import (
    reconciliation_selection_ui
)

# ---------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------

st.set_page_config(
    page_title="Payroll Reconciliation",
    layout="wide"
)

st.title("Payroll Reconciliation Tool")

# ---------------------------------------------------
# FILE UPLOAD
# ---------------------------------------------------

uploaded_file = st.file_uploader(
    "Upload Payroll Excel File",
    type=["xlsx", "xls"],
    key="file_upload"
)

# ---------------------------------------------------
# PROCESS FILE
# ---------------------------------------------------

if uploaded_file:

    try:

        # -------------------------------------------
        # GET SHEETS
        # -------------------------------------------

        sheet_names = get_sheet_names(uploaded_file)

        selected_sheet = st.selectbox(
            "Select Worksheet",
            sheet_names,
            key="sheet_select"
        )

        # -------------------------------------------
        # PREVIEW SHEET
        # -------------------------------------------

        preview_df = preview_sheet(
            uploaded_file,
            selected_sheet
        )

        st.subheader("Preview First Rows")

        st.dataframe(preview_df)

        # -------------------------------------------
        # HEADER ROW
        # -------------------------------------------

        header_row = st.number_input(
            "Header Row Number",
            min_value=0,
            max_value=20,
            value=0,
            step=1,
            key="header_row"
        )

        # -------------------------------------------
        # LOAD DATA
        # -------------------------------------------

        df = load_sheet_data(
            uploaded_file,
            selected_sheet,
            header_row
        )

        st.success(f"Loaded {len(df)} rows")

        # -------------------------------------------
        # SHOW COLUMNS
        # -------------------------------------------

        show_columns(df)

        # -------------------------------------------
        # PREVIEW DATA
        # -------------------------------------------

        show_data_preview(df)

        # -------------------------------------------
        # TOTAL TAX CONFIGURATION
        # -------------------------------------------

        st.subheader("Total Tax Configuration")

        add_total_tax = st.checkbox(
            "Add Total Tax Column",
            value=False,
            key="add_total_tax"
        )

        tax_columns = []
        if add_total_tax:
            tax_columns = st.multiselect(
                "Select Tax Columns To Sum (Total Tax = sum of selected columns)",
                df.columns.tolist(),
                key="tax_columns"
            )
            if tax_columns:
                valid_tax_cols = [c for c in tax_columns if c in df.columns]
                df["Total Tax"] = (
                    df[valid_tax_cols]
                    .apply(pd.to_numeric, errors="coerce")
                    .fillna(0)
                    .sum(axis=1)
                )

        # -------------------------------------------
        # ACCRUED MODE TOGGLE
        # -------------------------------------------

        st.subheader("Reconciliation Period Selection")

        accrued_mode = st.checkbox(
            "Enable Accrued Payroll Mode (adds 1 extra month after selected end month)",
            value=False,
            key="accrued_mode"
        )

        # -------------------------------------------
        # DATE COLUMN
        # -------------------------------------------

        date_column = st.selectbox(
            "Select Pay Date Column (for filtering)",
            df.columns.tolist(),
            key="date_column"
        )

        # -------------------------------------------
        # PERIOD SELECTION — Start Date + End Date
        # -------------------------------------------

        years = get_available_years(df, date_column)

        if len(years) > 0:

            default_start = datetime.date(min(years), 1, 1)
            default_end = datetime.date(max(years), 12, 31)

            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input(
                    "Reconciliation Start Date",
                    value=default_start,
                    key="start_date"
                )
            with col2:
                end_date = st.date_input(
                    "Reconciliation End Date",
                    value=default_end,
                    key="end_date"
                )

            cy_start = pd.Timestamp(start_date)
            cy_end = pd.Timestamp(end_date)

            # -------------------------------------------
            # FILTER DATA
            # -------------------------------------------

            if accrued_mode:

                st.subheader("Period Date Columns")

                period_begin_col_filter = st.selectbox(
                    "Select Period Begin Date Column",
                    df.columns.tolist(),
                    key="period_begin_filter"
                )

                period_end_col_filter = st.selectbox(
                    "Select Period End Date Column",
                    df.columns.tolist(),
                    key="period_end_filter"
                )

                filtered_df = filter_for_accrued_period(
                    df,
                    date_column,
                    period_begin_col_filter,
                    period_end_col_filter,
                    cy_start,
                    cy_end
                )

                # Compute extra month label for the success message
                if cy_end.month == 12:
                    em_year = cy_end.year + 1
                    em_month = 1
                else:
                    em_year = cy_end.year
                    em_month = cy_end.month + 1

                em_month_label = datetime.date(em_year, em_month, 1).strftime("%B %Y")
                st.success(
                    f"{len(filtered_df)} rows found for "
                    f"{start_date.strftime('%d %b %Y')} → {end_date.strftime('%d %b %Y')} "
                    f"(accrued mode — includes {em_month_label})"
                )

            else:

                period_begin_col_filter = None
                period_end_col_filter = None

                filtered_df = filter_by_period(
                    df,
                    date_column,
                    cy_start,
                    cy_end
                )

                st.success(
                    f"{len(filtered_df)} rows found for "
                    f"{start_date.strftime('%d %b %Y')} → {end_date.strftime('%d %b %Y')}"
                )

            # ---------------------------------------
            # RECONCILIATION UI
            # ---------------------------------------

            (
                pay_date_column,
                period_begin_column,
                period_end_column,
                sum_columns,
                keep_columns
            ) = reconciliation_selection_ui(filtered_df, accrued_mode)

            # Use the filter columns as fallback if UI columns not yet set
            if accrued_mode and period_begin_column is None:
                period_begin_column = period_begin_col_filter
            if accrued_mode and period_end_column is None:
                period_end_column = period_end_col_filter

            # ---------------------------------------
            # GENERATE REPORT
            # ---------------------------------------

            # Auto-include Total Tax in sum columns if it was computed
            effective_sum_columns = list(sum_columns)
            if add_total_tax and tax_columns and "Total Tax" in filtered_df.columns:
                if "Total Tax" not in effective_sum_columns:
                    effective_sum_columns.append("Total Tax")

            if len(effective_sum_columns) > 0:

                accrued_df = None

                if accrued_mode:

                    normal_df, accrued_df = generate_accrued_report(
                        filtered_df,
                        pay_date_column,
                        period_begin_column,
                        period_end_column,
                        effective_sum_columns,
                        keep_columns,
                        cy_start,
                        cy_end
                    )

                    grouped_df = normal_df

                else:

                    grouped_df = generate_grouped_report(
                        filtered_df,
                        pay_date_column,
                        effective_sum_columns,
                        keep_columns,
                        period_begin_column=period_begin_column,
                        period_end_column=period_end_column
                    )

                st.subheader("Grouped Payroll Report")
                st.caption(
                    "Edit the **Row Order** column to rearrange rows, "
                    "then click outside the cell to apply."
                )

                _grouped_display = grouped_df.copy()
                _grouped_display.insert(
                    0, "Row Order", range(1, len(_grouped_display) + 1)
                )

                _edited_grouped = st.data_editor(
                    _grouped_display,
                    column_config={
                        "Row Order": st.column_config.NumberColumn(
                            "Row Order",
                            help="Change numbers to reorder rows",
                            min_value=1,
                            step=1,
                            required=True,
                        )
                    },
                    hide_index=True,
                    use_container_width=True,
                    key="grouped_editor"
                )

                grouped_df = (
                    _edited_grouped
                    .sort_values("Row Order")
                    .drop(columns=["Row Order"])
                    .reset_index(drop=True)
                )

                if accrued_mode and accrued_df is not None and len(accrued_df) > 0:
                    st.subheader("Accrued Payroll (separate)")
                    st.caption(
                        "Edit the **Row Order** column to rearrange rows, "
                        "then click outside the cell to apply."
                    )

                    _accrued_display = accrued_df.copy()
                    _accrued_display.insert(
                        0, "Row Order", range(1, len(_accrued_display) + 1)
                    )

                    _edited_accrued = st.data_editor(
                        _accrued_display,
                        column_config={
                            "Row Order": st.column_config.NumberColumn(
                                "Row Order",
                                help="Change numbers to reorder rows",
                                min_value=1,
                                step=1,
                                required=True,
                            )
                        },
                        hide_index=True,
                        use_container_width=True,
                        key="accrued_editor"
                    )

                    accrued_df = (
                        _edited_accrued
                        .sort_values("Row Order")
                        .drop(columns=["Row Order"])
                        .reset_index(drop=True)
                    )

                # -----------------------------------
                # REVIEW CHECKS
                # -----------------------------------

                checks_df = generate_review_checks(
                    filtered_df,
                    grouped_df,
                    effective_sum_columns,
                    accrued_df
                )

                st.subheader("Review Checks")
                st.dataframe(checks_df)

                # -----------------------------------
                # DOWNLOAD
                # -----------------------------------

                excel_file = generate_excel_file(
                    grouped_df,
                    checks_df,
                    accrued_df
                )

                st.download_button(
                    label="Download Reconciliation Report",
                    data=excel_file,
                    file_name="payroll_reconciliation.xlsx",
                    mime=(
                        "application/"
                        "vnd.openxmlformats-officedocument."
                        "spreadsheetml.sheet"
                    ),
                    key="download_button"
                )

    except Exception as e:
        print("=="*50)
        print(f"Error processing file: {e}")

        st.error(f"Error: {str(e)}")
