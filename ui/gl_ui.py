import streamlit as st

from services.excel_service import (
    get_sheet_names,
    preview_sheet,
    load_sheet_data
)

from services.gl_service import (
    SECTIONS,
    get_unique_values,
    filter_by_source_values,
    get_unique_gl_codes,
    build_bucket_from_section_selections,
    apply_gl_bucket_mapping
)

from ui.preview import show_columns, show_data_preview


def render():

    # ---------------------------------------------------
    # STEP 1: FILE UPLOAD
    # ---------------------------------------------------

    uploaded_file = st.file_uploader(
        "Upload GL Excel File",
        type=["xlsx", "xls"],
        key="gl_file_upload"
    )

    if not uploaded_file:
        return

    try:

        # ---------------------------------------------------
        # STEP 2: SELECT WORKSHEET
        # ---------------------------------------------------

        sheet_names = get_sheet_names(uploaded_file)

        selected_sheet = st.selectbox(
            "Select Worksheet",
            sheet_names,
            key="gl_sheet_select"
        )

        # ---------------------------------------------------
        # RAW PREVIEW (before header row is set)
        # ---------------------------------------------------

        preview_df = preview_sheet(uploaded_file, selected_sheet)

        st.subheader("Preview First Rows")
        st.dataframe(preview_df)

        # ---------------------------------------------------
        # STEP 3: HEADER ROW
        # ---------------------------------------------------

        header_row = st.number_input(
            "Header Row Number",
            min_value=0,
            max_value=20,
            value=0,
            step=1,
            key="gl_header_row"
        )

        # ---------------------------------------------------
        # STEP 4: LOAD AND PREVIEW DATA
        # ---------------------------------------------------

        df = load_sheet_data(uploaded_file, selected_sheet, header_row)

        st.success(f"Loaded {len(df)} rows")

        show_columns(df)
        show_data_preview(df)

        columns = df.columns.tolist()

        # ---------------------------------------------------
        # STEP 4: SELECT PR SOURCE COLUMN
        # ---------------------------------------------------

        st.subheader("PR Source Column Filter")

        pr_source_col = st.selectbox(
            "Select PR Source Column",
            columns,
            key="gl_pr_source_col",
            help="The column containing values like PRV, PRS, or other source identifiers"
        )

        # ---------------------------------------------------
        # STEP 5: SELECT VALUES TO INCLUDE
        # ---------------------------------------------------

        unique_vals = get_unique_values(df, pr_source_col)

        st.caption(
            f"**{len(unique_vals)}** unique values found in "
            f"**{pr_source_col}**"
        )

        selected_values = st.multiselect(
            "Select PR Source Values To Include",
            options=unique_vals,
            default=[],
            key="gl_pr_source_values",
            help="Only rows matching these values will be used in the GL report"
        )

        if not selected_values:
            st.warning("Select at least one value to continue.")
            return

        filtered_df = filter_by_source_values(df, pr_source_col, selected_values)

        st.success(
            f"{len(filtered_df)} rows match the selected PR source values "
            f"({len(df) - len(filtered_df)} rows excluded)"
        )

        # ---------------------------------------------------
        # STEP 6: GL CODES COLUMN + SECTION DISTRIBUTION
        # ---------------------------------------------------

        st.subheader("GL Code Section Distribution")

        gl_codes_col = st.selectbox(
            "Select GL Codes (Source Code) Column",
            columns,
            key="gl_codes_col",
            help="The column containing GL / source codes to distribute into sections"
        )

        unique_codes = get_unique_gl_codes(filtered_df, gl_codes_col)

        st.caption(
            f"**{len(unique_codes)}** unique GL codes found in filtered data"
        )

        st.write(
            "Select codes for each section. "
            "Each code can only belong to one section — "
            "once picked, it disappears from the sections below."
        )

        # ---------------------------------------------------
        # PER-SECTION MULTISELECTS
        # Codes used by earlier sections are excluded from
        # the options of every subsequent section.
        # ---------------------------------------------------

        used_codes: set = set()
        section_selections: dict = {}

        for sec in SECTIONS:
            available = [c for c in unique_codes if c not in used_codes]

            selected = st.multiselect(
                f"Codes for **{sec}**",
                options=available,
                default=[],
                key=f"gl_section_{sec.lower()}",
                help=f"GL codes that belong to {sec}"
            )

            section_selections[sec] = selected
            used_codes.update(selected)

        # ---------------------------------------------------
        # DISTRIBUTION SUMMARY
        # ---------------------------------------------------

        unassigned = [c for c in unique_codes if c not in used_codes]
        total_assigned = len(used_codes)

        section_counts = [
            f"{sec}: {len(codes)}"
            for sec, codes in section_selections.items()
            if codes
        ]

        if total_assigned > 0:
            st.caption(
                f"**{total_assigned}/{len(unique_codes)}** codes assigned — "
                + ", ".join(section_counts)
            )

        if unassigned:
            st.info(
                f"{len(unassigned)} code(s) not assigned to any section: "
                + ", ".join(str(c) for c in unassigned)
                + ". These will show an empty GL_Category."
            )

        # ---------------------------------------------------
        # APPLY MAPPING — ADD GL_Category COLUMN
        # ---------------------------------------------------

        bucket_df = build_bucket_from_section_selections(
            section_selections,
            unique_codes
        )

        result_df = apply_gl_bucket_mapping(
            filtered_df,
            gl_codes_col,
            bucket_df
        )

        st.subheader("Filtered GL Data with Section Category")
        st.caption(
            "GL_Category column added based on your section assignments above. "
            "This data is ready for further column configuration and comparison."
        )
        st.dataframe(result_df, use_container_width=True)

    except Exception as e:
        print("==" * 50)
        print(f"GL Error: {e}")
        st.error(f"Error: {str(e)}")
