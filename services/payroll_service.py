import calendar

import pandas as pd


def get_available_years(df, date_column):

    temp_df = df.copy()

    temp_df[date_column] = pd.to_datetime(
        temp_df[date_column],
        errors="coerce"
    )

    years = (
        temp_df[date_column]
        .dropna()
        .dt.year
        .unique()
    )

    years = sorted(years)

    return years


def filter_by_year(df, date_column, year):

    temp_df = df.copy()

    temp_df[date_column] = pd.to_datetime(
        temp_df[date_column],
        errors="coerce"
    )

    filtered_df = temp_df[
        temp_df[date_column].dt.year == year
    ]

    return filtered_df


def filter_by_period(df, date_column, cy_start, cy_end):
    """Filter rows where pay date falls within [cy_start, cy_end] (inclusive)."""
    temp_df = df.copy()
    temp_df[date_column] = pd.to_datetime(temp_df[date_column], errors="coerce")
    mask = (
        (temp_df[date_column] >= cy_start) &
        (temp_df[date_column] <= cy_end)
    )
    return temp_df[mask].copy()


def filter_for_accrued_period(
    df,
    pay_date_column,
    period_begin_column,
    period_end_column,
    cy_start,
    cy_end
):
    """
    Returns data for selected period + 1 extra accrued month.

    Includes:
      - Rows where pay date is in [cy_start, cy_end]
      - Rows where pay date falls in the month immediately after cy_end
        AND period begin is within [cy_start, cy_end]
        (CY work paid in the accrued extra month)
    """
    temp_df = df.copy()

    # Compute extra month boundaries (month after cy_end)
    if cy_end.month == 12:
        em_year = cy_end.year + 1
        em_month = 1
    else:
        em_year = cy_end.year
        em_month = cy_end.month + 1
    em_last_day = calendar.monthrange(em_year, em_month)[1]
    extra_month_start = pd.Timestamp(em_year, em_month, 1)
    extra_month_end = pd.Timestamp(em_year, em_month, em_last_day)

    temp_df[pay_date_column] = pd.to_datetime(temp_df[pay_date_column], errors="coerce")
    temp_df[period_begin_column] = pd.to_datetime(temp_df[period_begin_column], errors="coerce")
    temp_df[period_end_column] = pd.to_datetime(temp_df[period_end_column], errors="coerce")

    in_period = (
        (temp_df[pay_date_column] >= cy_start) &
        (temp_df[pay_date_column] <= cy_end)
    )

    accrual_extra = (
        (temp_df[pay_date_column] >= extra_month_start) &
        (temp_df[pay_date_column] <= extra_month_end) &
        (temp_df[period_begin_column] >= cy_start) &
        (temp_df[period_begin_column] <= cy_end)
    )

    return temp_df[in_period | accrual_extra].copy()


def filter_for_accrued_year(
    df,
    pay_date_column,
    period_begin_column,
    period_end_column,
    cy_year
):
    """
    Returns 13 months of data: full CY + first month of NY.
    Excludes any pay run whose period begin date falls entirely in NY (cy_year+1).
    A row is included if:
      - pay date is in CY, OR
      - pay date is in NY but period begin date is still in CY
        (CY work paid in NY — categories 3 & 5)
    """

    temp_df = df.copy()
    ny_year = cy_year + 1

    temp_df[pay_date_column] = pd.to_datetime(
        temp_df[pay_date_column], errors="coerce"
    )
    temp_df[period_begin_column] = pd.to_datetime(
        temp_df[period_begin_column], errors="coerce"
    )
    temp_df[period_end_column] = pd.to_datetime(
        temp_df[period_end_column], errors="coerce"
    )

    pay_date_year = temp_df[pay_date_column].dt.year
    period_begin_year = temp_df[period_begin_column].dt.year

    # Include rows where pay date is in CY
    in_cy = pay_date_year == cy_year

    # Include rows where pay date is in NY but period began in CY (accrual)
    accrual_paid_in_ny = (
        (pay_date_year == ny_year) &
        (period_begin_year == cy_year)
    )

    mask = in_cy | accrual_paid_in_ny

    filtered_df = temp_df[mask].copy()

    return filtered_df
