import streamlit as st


def show_summary(df):

    st.subheader("Year Summary")

    st.metric(
        "Total Entries",
        len(df)
    )

    st.write("Filtered Data")

    st.dataframe(df.head(50))