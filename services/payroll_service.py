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
