import pandas as pd


SECTIONS = ["Earnings", "Benefits", "Deduction", "EETax", "ERTax", "TotalTax", "NetAmount", "Accrued"]


def get_unique_values(df: pd.DataFrame, column: str) -> list:
    """Return sorted unique non-null values from a column as strings."""
    return sorted(
        df[column].dropna().astype(str).unique().tolist()
    )


def filter_by_source_values(
    df: pd.DataFrame,
    source_col: str,
    selected_values: list
) -> pd.DataFrame:
    """Return rows where source_col (as string) is in selected_values."""
    return df[
        df[source_col].astype(str).isin([str(v) for v in selected_values])
    ].copy()


def get_unique_gl_codes(df: pd.DataFrame, codes_col: str) -> list:
    """Return sorted unique non-null GL codes from a column as strings."""
    return sorted(
        df[codes_col].dropna().astype(str).unique().tolist()
    )


def build_bucket_from_section_selections(
    section_selections: dict,
    all_codes: list
) -> pd.DataFrame:
    """
    Build bucket DataFrame from per-section multiselect results.
    section_selections: {"Earnings": ["400", "200"], "Benefits": ["300"], ...}
    all_codes: full unique code list (unassigned codes get an empty Section).
    """
    rows = []
    assigned: set = set()
    for sec, codes in section_selections.items():
        for code in codes:
            rows.append({"GL Code": str(code), "Section": sec})
            assigned.add(str(code))
    for code in all_codes:
        if str(code) not in assigned:
            rows.append({"GL Code": str(code), "Section": ""})
    if rows:
        return pd.DataFrame(rows)
    return pd.DataFrame(columns=["GL Code", "Section"])


def apply_gl_bucket_mapping(
    df: pd.DataFrame,
    codes_col: str,
    bucket_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Add a GL_Category column to df by mapping each GL code to its assigned section.
    bucket_df must have columns ['GL Code', 'Section'].
    Unassigned codes get an empty string.
    """
    mapping = dict(zip(
        bucket_df["GL Code"].astype(str),
        bucket_df["Section"].fillna("")
    ))
    result = df.copy()
    result["GL_Category"] = (
        result[codes_col].astype(str).map(mapping).fillna("")
    )
    return result
