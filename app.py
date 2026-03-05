import streamlit as st
import pandas as pd
import plotly.express as px
import re

st.set_page_config(page_title="Callcenter Performance Monitor", layout="wide")

st.title("📞 Callcenter Performance Monitor")

uploaded_file = st.file_uploader("Upload CRM Excel", type=["xlsx"])

if uploaded_file:

    df = pd.read_excel(uploaded_file)

    required_cols = ["Onderwerp","Beschrijving","Gemaakt op","Gemaakt door"]

    for col in required_cols:
        if col not in df.columns:
            st.error(f"Kolom ontbreekt: {col}")
            st.stop()

    # =====================
    # DATA PREP
    # =====================

    df["Beschrijving"] = df["Beschrijving"].astype(str).str.lower()

    df["Gemaakt op"] = pd.to_datetime(df["Gemaakt op"], dayfirst=True, errors="coerce")

    df["datum"] = df["Gemaakt op"].dt.date

    start_date = df["Gemaakt op"].min()
    end_date = df["Gemaakt op"].max()

    split = df["Onderwerp"].astype(str).str.split(r"\s-\s-\s", expand=True)

    df["Onderwerp_type"] = split[0].fillna("Onbekend")
    df["Onderwerp_cat"] = split[1].fillna("Onbekend")
    df["Onderwerp_sub"] = split[2].fillna("Onbekend")

    total_calls = len(df)

    # =====================
    # KPI DEFINITIES
    # =====================

    klacht_terms = "klacht|klagen|compensatie|ontevreden|niet tevreden"
    issue_terms = "storing|werkt niet|kan niet|fout|error|bug|probleem|issue|vastgelopen|crash|timeout|mislukt|faalt"
    churn_terms = "opzeg|annul|beëindig|beeindig|stopzetten"

    df["KPI_FormeleKlacht"] = (
        (df["Onderwerp_type"]=="Klacht") |
        (df["Beschrijving"].str.contains(klacht_terms))
    )

    df["KPI_IssueSignaal"] = (
        (df["Onderwerp_type"]=="Storing") |
        (df["Beschrijving"].str.contains(issue_terms))
    )

    df["KPI_ChurnRisico"] = (
        (df["Onderwerp_type"]=="Opzegging") |
        (df["Beschrijving"].str.contains(churn_terms))
    )

    # =====================
    # EXCLUSIVE KPI
    # =====================

    def exclusive(row):

        if row["KPI_FormeleKlacht"]:
            return "Formele klacht"

        if row["KPI_ChurnRisico"]:
            return "Churn risico"

        if row["KPI_IssueSignaal"]:
            return "Issue signaal"

        return "Geen"

    df["KPI_Exclusive"] = df.apply(exclusive, axis=1)

    # =====================
    # KPI OVERVIEW
    # =====================

    st.subheader("KPI Overzicht")

    col1,col2,col3,col4 = st.columns(4)

    col1.metric("Total calls", total_calls)

    col2.metric(
        "Klachten",
        int(df["KPI_FormeleKlacht"].sum()),
        f"{round(df['KPI_FormeleKlacht'].mean()*100,2)}%"
    )

    col3.metric(
        "Issues",
        int(df["KPI_IssueSignaal"].sum()),
        f"{round(df['KPI_IssueSignaal'].mean()*100,2)}%"
    )

    col4.metric(
        "Churn risico",
        int(df["KPI_ChurnRisico"].sum()),
        f"{round(df['KPI_ChurnRisico'].mean()*100,2)}%"
    )

    st.write(f"Periode: {start_date.date()} t/m {end_date.date()}")

    # =====================
    # TOP CATEGORIES
    # =====================

    st.subheader("Top Call Categorieën")

    top_cat = df["Onderwerp_cat"].value_counts().head(10)

    fig = px.bar(top_cat)

    st.plotly_chart(fig, use_container_width=True)

    top_sub = df["Onderwerp_sub"].value_counts().head(15)

    fig2 = px.bar(top_sub)

    st.plotly_chart(fig2, use_container_width=True)

    # =====================
    # ISSUE ANALYSE
    # =====================

    st.subheader("Belangrijkste Problemen")

    issue_df = df[df["KPI_IssueSignaal"]]

    issue_top = issue_df["Onderwerp_sub"].value_counts().head(10)

    fig3 = px.bar(issue_top)

    st.plotly_chart(fig3, use_container_width=True)

    # =====================
    # KLACHT ANALYSE
    # =====================

    st.subheader("Top Klachten")

    klacht_df = df[df["KPI_FormeleKlacht"]]

    klacht_top = klacht_df["Onderwerp_sub"].value_counts().head(10)

    fig4 = px.bar(klacht_top)

    st.plotly_chart(fig4, use_container_width=True)

    # =====================
    # TRENDS PER DAG
    # =====================

    st.subheader("KPI Trends")

    trends = df.groupby("datum").agg({

        "KPI_FormeleKlacht":"sum",
        "KPI_IssueSignaal":"sum",
        "KPI_ChurnRisico":"sum"

    }).reset_index()

    fig5 = px.line(trends, x="datum",
                   y=["KPI_FormeleKlacht","KPI_IssueSignaal","KPI_ChurnRisico"])

    st.plotly_chart(fig5, use_container_width=True)

    # =====================
    # MEDEWERKER ANALYSE
    # =====================

    st.subheader("Activiteit per Medewerker")

    agent = df.groupby("Gemaakt door").agg({

        "KPI_FormeleKlacht":"sum",
        "KPI_IssueSignaal":"sum",
        "KPI_ChurnRisico":"sum",
        "Onderwerp":"count"

    }).rename(columns={"Onderwerp":"calls"}).reset_index()

    agent = agent[agent["calls"] >= 50]

    st.dataframe(agent)

    # =====================
    # OVERIG ANALYSE
    # =====================

    st.subheader("Overig Analyse")

    overig = df[df["Onderwerp_sub"]=="Overig"]

    st.write("Aantal Overig calls:", len(overig))

    # categorisatie regels

    rules = {

    "Inloggen":"inlog|login|wachtwoord|2fa|auth|verific",
    "Factuur":"factuur|invoice|betaling|betaal|incasso|aanman|credit|btw|tarief|prijs",
    "Adverteren":"advert|adverteer|plaats|plaatsing|listing|promot|campagn",
    "Website":"website|portaal|portal|pagina|link|url|knop|menu|formulier",
    "Export":"export|ead|kfz|eur1|vtg|document|uitvoer|douane",
    "Account":"account|profiel|gegevens|email|telefoon|gebruiker|rechten"

    }

    def suggest(text):

        for k,v in rules.items():

            if re.search(v,text):

                return k

        return "Overig (onduidelijk)"

    overig["Voorgestelde categorie"] = overig["Beschrijving"].apply(suggest)

    st.dataframe(overig.head(100))

    # =====================
    # EXPORT
    # =====================

    st.subheader("Download Analyse")

    excel = overig.to_excel("overig_analyse.xlsx")

    with open("overig_analyse.xlsx","rb") as f:

        st.download_button(
            label="Download Overig Analyse Excel",
            data=f,
            file_name="overig_analyse.xlsx"
        )
