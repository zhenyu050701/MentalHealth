import streamlit as st
import pandas as pd
import plotly.express as px

def show_analytics():
    st.header("📊 Assessment Analytics")
    
    try:
        if not client:
            return

        db = client[st.secrets["db_name"]]
        collection = db[st.secrets["collection_name"]]
        raw_data = list(collection.find())

        if not raw_data:
            st.warning("No data available yet. Complete an assessment first!")
            return

        # Convert and clean data
        clean_data = convert_mongo_docs(raw_data)
        df = pd.DataFrame(clean_data)
        df = clean_gender_data(df)  # Clean gender column

        ## -----------------------------------------------
        ## 🥧 PIE CHART: Gender Distribution
        ## -----------------------------------------------
        st.subheader("👥 Gender Distribution")
        gender_counts = df["Gender"].value_counts().reset_index()
        gender_counts.columns = ["Gender", "Count"]
        
        fig_gender = px.pie(
            gender_counts, 
            values="Count", 
            names="Gender",
            color="Gender",
            color_discrete_map={"Male": "#1f77b4", "Female": "#ff7f0e"},
            hole=0.3
        )
        fig_gender.update_traces(textinfo="label+percent")
        st.plotly_chart(fig_gender, use_container_width=True)

        ## -----------------------------------------------
        ## 📊 BAR CHART: Stress vs Sleep Quality
        ## -----------------------------------------------
        if "Stress Level" in df.columns and "Sleep Quality" in df.columns:
            st.subheader("😰 Stress Level vs. 💤 Sleep Quality")

            fig_stress_sleep = px.bar(
                df.groupby(["Stress Level", "Sleep Quality"]).size().reset_index(name="Count"),
                x="Stress Level",
                y="Count",
                color="Sleep Quality",
                barmode="group",
                title="Stress vs. Sleep Quality"
            )
            st.plotly_chart(fig_stress_sleep, use_container_width=True)

        ## -----------------------------------------------
        ## 🥧 PIE CHART: % of Anxious Users with Low Social Support
        ## -----------------------------------------------
        if "Anxiety Level" in df.columns and "Social Support" in df.columns:
            st.subheader("📉 Anxious Users with Low Social Support")

            anxious_users = df[df["Anxiety Level"] == "High"]
            low_support_count = (anxious_users["Social Support"] == "Low").sum()
            high_support_count = (anxious_users["Social Support"] != "Low").sum()

            pie_data = pd.DataFrame({"Support Level": ["Low", "High"], "Count": [low_support_count, high_support_count]})

            fig_pie_anxiety = px.pie(
                pie_data,
                values="Count",
                names="Support Level",
                title="Anxiety vs. Social Support",
                color_discrete_sequence=["red", "green"]
            )
            st.plotly_chart(fig_pie_anxiety, use_container_width=True)

        ## -----------------------------------------------
        ## 🎯 SCATTER PLOT: Anxiety vs. Self-Harm Cases
        ## -----------------------------------------------
        if "Anxiety Level" in df.columns and "Self-Harm Thoughts" in df.columns:
            st.subheader("📈 Anxiety Level vs. Self-Harm Cases")

            fig_scatter_anxiety = px.scatter(
                df,
                x="Anxiety Level",
                y="Self-Harm Thoughts",
                color="Anxiety Level",
                size_max=10,
                title="Anxiety vs. Self-Harm Cases"
            )
            st.plotly_chart(fig_scatter_anxiety, use_container_width=True)

    except Exception as e:
        st.error(f"Error loading analytics: {str(e)}")
