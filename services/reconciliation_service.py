import pandas as pd


# ---------------------------------------------------------------------------
# PAYROLL CATEGORY CONSTANTS
# ---------------------------------------------------------------------------

CAT_NORMAL = "Normal Payroll"
CAT_PRIOR_PAID_CY = "Prior Year Payroll Paid in CY"
CAT_CY_PAID_NY = "CY Payroll Paid in NY"
CAT_SPLIT_BOY = "Split Payroll - Beginning of Year"
CAT_SPLIT_EOY = "Split Payroll - Year-End"


# ---------------------------------------------------------------------------
# CLASSIFICATION
# ---------------------------------------------------------------------------

def classify_payroll_run(
    pay_date,
    period_begin,
    period_end,
    cy_year
):
    """
    Classifies a single payroll run into one of 5 categories based on
    how the pay date and period dates relate to the current fiscal year.
    """

    if pd.isna(pay_date) or pd.isna(period_begin) or pd.isna(period_end):
        return CAT_NORMAL

    py_year = cy_year - 1
    ny_year = cy_year + 1

    pd_year = pay_date.year
    pb_year = period_begin.year
    pe_year = period_end.year

    # Category 2: pay date in CY, entire period in PY
    if pd_year == cy_year and pb_year <= py_year and pe_year <= py_year:
        return CAT_PRIOR_PAID_CY

    # Category 4: pay date in CY, period spans PY -> CY
    if pd_year == cy_year and pb_year <= py_year and pe_year == cy_year:
        return CAT_SPLIT_BOY

    # Category 3: pay date in NY, entire period in CY
    if pd_year == ny_year and pb_year == cy_year and pe_year == cy_year:
        return CAT_CY_PAID_NY

    # Category 5: pay date in NY, period spans CY -> NY
    if pd_year == ny_year and pb_year == cy_year and pe_year == ny_year:
        return CAT_SPLIT_EOY

    # Category 1: everything else with pay date in CY and period in CY
    return CAT_NORMAL


# ---------------------------------------------------------------------------
# WORKING DAYS PRORATION
# ---------------------------------------------------------------------------

def _working_days_in_range(start, end):
    """Count Mon-Fri working days between start and end (inclusive)."""
    if pd.isna(start) or pd.isna(end) or end < start:
        return 0
    days = pd.bdate_range(start=start, end=end)
    return len(days)


def calculate_proration_factor(
    period_begin,
    period_end,
    cy_year
):
    """
    Returns the fraction of the pay run that falls within cy_year.
    Used for Categories 4 (Split BOY) and 5 (Split EOY).
    Returns 1.0 for runs fully within CY, 0.0 on bad data.
    """

    if pd.isna(period_begin) or pd.isna(period_end):
        return 1.0

    cy_start = pd.Timestamp(cy_year, 1, 1)
    cy_end = pd.Timestamp(cy_year, 12, 31)

    # CY overlap window
    overlap_start = max(period_begin, cy_start)
    overlap_end = min(period_end, cy_end)

    total_days = _working_days_in_range(period_begin, period_end)

    if total_days == 0:
        return 1.0

    cy_days = _working_days_in_range(overlap_start, overlap_end)

    return cy_days / total_days


# ---------------------------------------------------------------------------
# GROUPED REPORT — NORMAL MODE (unchanged behaviour)
# ---------------------------------------------------------------------------

def generate_grouped_report(
    df,
    pay_date_column,
    sum_columns,
    keep_columns=None,
    period_begin_column=None,
    period_end_column=None
):

    temp_df = df.copy()

    # Normalize all date columns — strips time so 2025-01-17 00:00 and
    # 2025-01-17 12:30 are treated as the same date when grouping.
    date_cols = [pay_date_column]
    if period_begin_column and period_begin_column in temp_df.columns:
        date_cols.append(period_begin_column)
    if period_end_column and period_end_column in temp_df.columns and period_end_column not in date_cols:
        date_cols.append(period_end_column)

    for col in date_cols:
        temp_df[col] = pd.to_datetime(temp_df[col], errors="coerce").dt.normalize()

    temp_df = temp_df.dropna(subset=[pay_date_column])

    # Build composite group key — deduplicated
    group_cols = [pay_date_column]
    for col in [period_begin_column, period_end_column]:
        if col and col in temp_df.columns and col not in group_cols:
            group_cols.append(col)

    agg_dict = {}

    for col in sum_columns:
        agg_dict[col] = "sum"

    if keep_columns:
        for col in keep_columns:
            if col not in group_cols and col not in sum_columns:
                agg_dict[col] = "first"

    grouped_df = (
        temp_df
        .groupby(group_cols)
        .agg(agg_dict)
        .reset_index()
    )

    grouped_df = grouped_df.sort_values(by=group_cols)

    # Format date columns as date-only strings (no time component)
    for col in group_cols:
        if pd.api.types.is_datetime64_any_dtype(grouped_df[col]):
            grouped_df[col] = grouped_df[col].dt.strftime('%m/%d/%Y')

    return grouped_df


# ---------------------------------------------------------------------------
# GROUPED REPORT — ACCRUED MODE
# ---------------------------------------------------------------------------

def generate_accrued_report(
    df,
    pay_date_column,
    period_begin_column,
    period_end_column,
    sum_columns,
    keep_columns,
    cy_year
):
    """
    Returns (normal_df, accrued_df).

    normal_df  — Category 1 runs + CY-prorated amounts for Categories 4 & 5,
                 grouped by pay date.
    accrued_df — Categories 2, 3, 4 (NY portion), 5 (NY portion) with a
                 Payroll_Category and GL_Code column, grouped by pay date.
    """

    temp_df = df.copy()

    # Convert and normalize date columns (strip time component)
    for col in [pay_date_column, period_begin_column, period_end_column]:
        temp_df[col] = pd.to_datetime(temp_df[col], errors="coerce").dt.normalize()

    temp_df = temp_df.dropna(subset=[pay_date_column])

    # Classify every row
    temp_df["Payroll_Category"] = temp_df.apply(
        lambda r: classify_payroll_run(
            r[pay_date_column],
            r[period_begin_column],
            r[period_end_column],
            cy_year
        ),
        axis=1
    )

    # Proration factor for each row
    temp_df["_proration"] = temp_df.apply(
        lambda r: calculate_proration_factor(
            r[period_begin_column],
            r[period_end_column],
            cy_year
        ),
        axis=1
    )

    # -----------------------------------------------------------------------
    # Build normal (CY-recognised) rows
    # -----------------------------------------------------------------------

    normal_rows = []

    for _, row in temp_df.iterrows():
        cat = row["Payroll_Category"]
        factor = row["_proration"]

        if cat == CAT_NORMAL:
            normal_rows.append(row)

        elif cat in (CAT_SPLIT_BOY, CAT_SPLIT_EOY):
            # Only CY portion goes to normal reconciliation
            r = row.copy()
            for col in sum_columns:
                try:
                    r[col] = pd.to_numeric(r[col], errors="coerce") * factor
                except Exception:
                    pass
            normal_rows.append(r)

        # CAT_PRIOR_PAID_CY: excluded from CY expense reconciliation entirely
        # CAT_CY_PAID_NY: fully included in CY reconciliation — added below

        elif cat == CAT_CY_PAID_NY:
            normal_rows.append(row)

    # -----------------------------------------------------------------------
    # Build accrued rows
    # -----------------------------------------------------------------------

    accrued_rows = []

    for _, row in temp_df.iterrows():
        cat = row["Payroll_Category"]
        factor = row["_proration"]

        if cat == CAT_PRIOR_PAID_CY:
            r = row.copy()
            r["GL_Code"] = "2157"
            accrued_rows.append(r)

        elif cat == CAT_CY_PAID_NY:
            # Net liability cleared in NY — show in accrued with GL 2157
            r = row.copy()
            r["GL_Code"] = "2157"
            accrued_rows.append(r)

        elif cat in (CAT_SPLIT_BOY, CAT_SPLIT_EOY):
            # NY portion = (1 - factor) of each amount
            r = row.copy()
            ny_factor = 1.0 - factor
            for col in sum_columns:
                try:
                    r[col] = pd.to_numeric(r[col], errors="coerce") * ny_factor
                except Exception:
                    pass
            r["GL_Code"] = "2157"
            accrued_rows.append(r)

    # -----------------------------------------------------------------------
    # Aggregate normal
    # -----------------------------------------------------------------------

    # Composite group key for accrued aggregation
    group_cols = [pay_date_column]
    for col in [period_begin_column, period_end_column]:
        if col and col in temp_df.columns and col not in group_cols:
            group_cols.append(col)

    def _aggregate(rows, grp_cols, sum_cols, keep_cols):
        if not rows:
            return pd.DataFrame()
        frame = pd.DataFrame(rows)
        # Normalize date columns in the aggregated frame
        for col in grp_cols:
            if col in frame.columns:
                frame[col] = pd.to_datetime(frame[col], errors="coerce").dt.normalize()
        for col in sum_cols:
            frame[col] = pd.to_numeric(frame[col], errors="coerce").fillna(0)
        agg_dict = {col: "sum" for col in sum_cols}
        if keep_cols:
            for col in keep_cols:
                if col not in grp_cols and col not in sum_cols:
                    agg_dict[col] = "first"
        grouped = (
            frame
            .groupby(grp_cols)
            .agg(agg_dict)
            .reset_index()
            .sort_values(by=grp_cols)
        )
        # Format date columns as date-only strings
        for col in grp_cols:
            if col in grouped.columns and pd.api.types.is_datetime64_any_dtype(grouped[col]):
                grouped[col] = grouped[col].dt.strftime('%m/%d/%Y')
        return grouped

    normal_df = _aggregate(
        normal_rows, group_cols, sum_columns, keep_columns
    )

    # For accrued we also preserve Payroll_Category and GL_Code
    accrued_keep = list(keep_columns or []) + ["Payroll_Category", "GL_Code"]
    accrued_df = _aggregate(
        accrued_rows, group_cols, sum_columns, accrued_keep
    )

    return normal_df, accrued_df


# ---------------------------------------------------------------------------
# REVIEW CHECKS
# ---------------------------------------------------------------------------

def generate_review_checks(
    source_df,
    grouped_df,
    sum_columns,
    accrued_df=None
):

    checks = []

    checks.append({
        "Check": "Source Row Count",
        "Value": len(source_df)
    })

    checks.append({
        "Check": "Grouped Row Count",
        "Value": len(grouped_df)
    })

    if accrued_df is not None and len(accrued_df) > 0:
        checks.append({
            "Check": "Accrued Row Count",
            "Value": len(accrued_df)
        })

    for col in sum_columns:

        source_total = (
            pd.to_numeric(source_df[col], errors="coerce")
            .fillna(0)
            .sum()
        )

        grouped_total = (
            pd.to_numeric(grouped_df[col], errors="coerce")
            .fillna(0)
            .sum()
        )

        accrued_total = 0.0
        if accrued_df is not None and col in accrued_df.columns:
            accrued_total = (
                pd.to_numeric(accrued_df[col], errors="coerce")
                .fillna(0)
                .sum()
            )

        difference = source_total - grouped_total

        row = {
            "Check": f"{col} Validation",
            "Source Total": round(source_total, 2),
            "Grouped Total": round(grouped_total, 2),
            "Difference": round(difference, 2)
        }

        if accrued_df is not None:
            row["Accrued Total"] = round(accrued_total, 2)

        checks.append(row)

    checks_df = pd.DataFrame(checks)

    return checks_df
