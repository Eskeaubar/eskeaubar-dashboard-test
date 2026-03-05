import streamlit as st
import pandas as pd
import plotly.express as px

st.title("📞 Callcenter Analyse Dashboard")

uploaded_file = st.file_uploader("Upload CRM Excel", type=["xlsx"])

if uploaded_file:

    df = pd.read_excel(uploaded_file)

    required_cols = ["Onderwerp","Beschrijving","Gemaakt op","Gemaakt door"]

    for col in required_cols:
        if col not in df.columns:
            st.error(f"Kolom ontbreekt: {col}")
            st.stop()

    df["Beschrijving"] = df["Beschrijving"].astype(str).str.lower()
    df["Gemaakt op"] = pd.to_datetime(df["Gemaakt op"], dayfirst=True)
    df["datum"] = df["Gemaakt op"].dt.date

    split = df["Onderwerp"].astype(str).str.split(" - - ", expand=True)

    df["Onderwerp_type"] = split[0].fillna("Onbekend")
    df["Onderwerp_cat"] = split[1].fillna("Onbekend")
    df["Onderwerp_sub"] = split[2].fillna("Onbekend")

    df["KPI_Klacht"] = (
        (df["Onderwerp_type"]=="Klacht") |
        (df["Beschrijving"].str.contains("klacht|compensatie|ontevreden"))
    )

    df["KPI_Issue"] = (
        (df["Onderwerp_type"]=="Storing") |
        (df["Beschrijving"].str.contains("storing|error|bug|probleem"))
    )

    df["KPI_Churn"] = (
        (df["Onderwerp_type"]=="Opzegging") |
        (df["Beschrijving"].str.contains("opzeg|annul|stopzetten"))
    )

    st.subheader("KPI Overzicht")

    col1,col2,col3 = st.columns(3)

    col1.metric("Klachten", int(df["KPI_Klacht"].sum()))
    col2.metric("Issues", int(df["KPI_Issue"].sum()))
    col3.metric("Churn risico", int(df["KPI_Churn"].sum()))

    st.subheader("Calls per dag")

    calls_day = df.groupby("datum").size().reset_index(name="calls")

    fig = px.line(calls_day,x="datum",y="calls")

    st.plotly_chart(fig)

    st.subheader("Top subonderwerpen")

    top_sub = df["Onderwerp_sub"].value_counts().head(10)

    fig2 = px.bar(top_sub)

    st.plotly_chart(fig2)
