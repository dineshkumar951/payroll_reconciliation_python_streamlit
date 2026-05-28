import pandas as pd


def get_sheet_names(file):

    excel_file = pd.ExcelFile(file)

    return excel_file.sheet_names


def preview_sheet(file, sheet_name):

    preview_df = pd.read_excel(
        file,
        sheet_name=sheet_name,
        header=None,
        nrows=10
    )

    # Convert columns to string
    preview_df.columns = [
        str(col)
        for col in preview_df.columns
    ]

    return preview_df


def load_sheet_data(
    file,
    sheet_name,
    header_row
):

    df = pd.read_excel(
        file,
        sheet_name=sheet_name,
        header=header_row
    )

    # -----------------------------------
    # REMOVE UNNAMED COLUMNS
    # -----------------------------------

    df = df.loc[
        :,
        ~df.columns.astype(str)
        .str.contains("^Unnamed")
    ]

    # -----------------------------------
    # REMOVE EMPTY ROWS
    # -----------------------------------

    df = df.dropna(how="all")

    # -----------------------------------
    # CONVERT COLUMN NAMES TO STRING
    # -----------------------------------

    df.columns = [
        str(col).strip()
        for col in df.columns
    ]

    # -----------------------------------
    # HANDLE DUPLICATE COLUMNS
    # -----------------------------------

    new_columns = []

    for i, col in enumerate(df.columns):

        if col in new_columns:
            col = f"{col}_{i}"

        new_columns.append(col)

    df.columns = new_columns

    return df