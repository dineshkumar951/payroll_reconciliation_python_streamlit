import streamlit as st


def show_columns(df):

    st.subheader("Attributes / Columns")

    columns = list(df.columns)

    st.write(columns)


def show_data_preview(df):

    st.subheader("Data Preview")

    st.dataframe(df.head(20))