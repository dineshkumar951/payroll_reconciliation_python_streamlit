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
    keep_columns=None
):

    temp_df = df.copy()

    temp_df[pay_date_column] = pd.to_datetime(
        temp_df[pay_date_column],
        errors="coerce"
    )

    temp_df = temp_df.dropna(subset=[pay_date_column])

    agg_dict = {}

    for col in sum_columns:
        agg_dict[col] = "sum"

    if keep_columns:
        for col in keep_columns:
            if col != pay_date_column and col not in sum_columns:
                agg_dict[col] = "first"

    grouped_df = (
        temp_df
        .groupby(pay_date_column)
        .agg(agg_dict)
        .reset_index()
    )

    grouped_df = grouped_df.sort_values(by=pay_date_column)

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

    # Convert date columns
    for col in [pay_date_column, period_begin_column, period_end_column]:
        temp_df[col] = pd.to_datetime(temp_df[col], errors="coerce")

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

    def _aggregate(rows, group_col, sum_cols, keep_cols):
        if not rows:
            return pd.DataFrame()
        frame = pd.DataFrame(rows)
        for col in sum_cols:
            frame[col] = pd.to_numeric(frame[col], errors="coerce").fillna(0)
        agg_dict = {col: "sum" for col in sum_cols}
        if keep_cols:
            for col in keep_cols:
                if col != group_col and col not in sum_cols:
                    agg_dict[col] = "first"
        grouped = (
            frame
            .groupby(group_col)
            .agg(agg_dict)
            .reset_index()
            .sort_values(by=group_col)
        )
        return grouped

    normal_df = _aggregate(
        normal_rows, pay_date_column, sum_columns, keep_columns
    )

    # For accrued we also preserve Payroll_Category and GL_Code
    accrued_keep = list(keep_columns or []) + ["Payroll_Category", "GL_Code"]
    accrued_df = _aggregate(
        accrued_rows, pay_date_column, sum_columns, accrued_keep
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
