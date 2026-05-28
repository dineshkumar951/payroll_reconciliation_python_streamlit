import streamlit as st
import pandas as pd

from services.excel_service import (
    get_sheet_names,
    preview_sheet,
    load_sheet_data
)

from services.payroll_service import (
    get_available_years,
    filter_by_year,
    filter_for_accrued_year
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
        # ACCRUED MODE TOGGLE
        # -------------------------------------------

        st.subheader("Year Selection")

        accrued_mode = st.checkbox(
            "Enable Accrued Payroll Mode (13-month range: full CY + 1 month of NY)",
            value=False,
            key="accrued_mode"
        )

        # -------------------------------------------
        # DATE COLUMN
        # -------------------------------------------

        date_column = st.selectbox(
            "Select Pay Date Column (for year detection)",
            df.columns.tolist(),
            key="date_column"
        )

        # -------------------------------------------
        # YEAR SELECTION
        # -------------------------------------------

        years = get_available_years(df, date_column)

        if len(years) > 0:

            selected_year = st.selectbox(
                "Select Current Fiscal Year (CY)",
                years,
                key="year_select"
            )

            # -------------------------------------------
            # FILTER DATA
            # -------------------------------------------

            if accrued_mode:

                # Period column selectors shown before filtering so we can
                # use them in the filter
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

                filtered_df = filter_for_accrued_year(
                    df,
                    date_column,
                    period_begin_col_filter,
                    period_end_col_filter,
                    selected_year
                )

                st.success(
                    f"{len(filtered_df)} rows found for CY {selected_year} "
                    f"(accrued mode — includes up to 1 month of {selected_year + 1})"
                )

            else:

                period_begin_col_filter = None
                period_end_col_filter = None

                filtered_df = filter_by_year(
                    df,
                    date_column,
                    selected_year
                )

                st.success(
                    f"{len(filtered_df)} rows found for {selected_year}"
                )

            # ---------------------------------------
            # RECONCILIATION UI
            # ---------------------------------------

            (
                pay_date_column,
                period_begin_column,
                period_end_column,
                sum_columns,
                keep_columns,
                add_total_tax,
                tax_columns
            ) = reconciliation_selection_ui(filtered_df, accrued_mode)

            # Use the filter columns as fallback if UI columns not yet set
            if accrued_mode and period_begin_column is None:
                period_begin_column = period_begin_col_filter
            if accrued_mode and period_end_column is None:
                period_end_column = period_end_col_filter

            # ---------------------------------------
            # GENERATE REPORT
            # ---------------------------------------

            if len(sum_columns) > 0:

                accrued_df = None

                if accrued_mode:

                    normal_df, accrued_df = generate_accrued_report(
                        filtered_df,
                        pay_date_column,
                        period_begin_column,
                        period_end_column,
                        sum_columns,
                        keep_columns,
                        selected_year,
                        add_total_tax,
                        tax_columns
                    )

                    grouped_df = normal_df

                else:

                    grouped_df = generate_grouped_report(
                        filtered_df,
                        pay_date_column,
                        sum_columns,
                        keep_columns,
                        period_begin_column=period_begin_column,
                        period_end_column=period_end_column,
                        add_total_tax=add_total_tax,
                        tax_columns=tax_columns
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

                check_columns = sum_columns.copy()
                if add_total_tax and tax_columns:
                    check_columns.append("Total Tax")

                checks_df = generate_review_checks(
                    filtered_df,
                    grouped_df,
                    check_columns,
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
