import streamlit as st
import pandas as pd

st.set_page_config(page_title="Competitor Pricing Comparison", layout="wide")
st.title("TwelveLabs vs Competitor Pricing Calculator")
st.caption("Compare estimated costs for analyzing video content across different models.")

# User Inputs
st.sidebar.header("Input Parameters")
index_video_hours = st.sidebar.number_input("Index Video Hours", min_value=0, value=1000, step=100)
total_analyze_queries = st.sidebar.number_input("Total Analyze Queries", min_value=0, value=10000, step=100)
avg_video_duration = st.sidebar.number_input("Avg Video Duration (min)", min_value=1, value=10)
avg_output_tokens = st.sidebar.number_input("Avg Output Tokens per Analyze", min_value=0, value=1000)

# Competitor Model Pricing
competitor_pricing = {
    "Gemini 2.5 Pro (<=12min)": {"video": 1.25, "input": 1.25, "output": 10},
    "Gemini 2.5 Pro (>12min)": {"video": 2.50, "input": 2.50, "output": 15},
    "Gemini 2.5 Flash": {"video": 0.30, "input": 0.30, "output": 2.50},
    "GPT 4.1-mini": {"video": 0.40, "input": 0.40, "output": 1.00},
    "GPT 4.1": {"video": 2.00, "input": 2.00, "output": 8.00},
    "Nova Lite": {"video": 0.06, "input": 0.06, "output": 0.24},
    "Nova Pro": {"video": 0.80, "input": 0.80, "output": 3.20},
}

# TwelveLabs Pricing
twelvelabs_pricing = {
    "video": 2.5,  # $/hr
    "output": 7.5 / 1_000_000  # $/token
}

# Competitor Selection
selected_competitors = st.multiselect("Select Competitors to Compare", options=list(competitor_pricing.keys()))

# Calculation
comparison = {
    "TwelveLabs": {
        "Indexing Cost": index_video_hours * twelvelabs_pricing["video"],
        "Output Token Cost": total_analyze_queries * avg_output_tokens * twelvelabs_pricing["output"],
    }
}
comparison["TwelveLabs"]["Total Cost"] = sum(comparison["TwelveLabs"].values())

for name in selected_competitors:
    model = competitor_pricing[name]
    comp_cost = {
        "Indexing Cost": index_video_hours * model["video"],
        "Output Token Cost": total_analyze_queries * avg_output_tokens / 1_000_000 * model["output"]
    }
    comp_cost["Total Cost"] = sum(comp_cost.values())
    comparison[name] = comp_cost

# Display Table
df = pd.DataFrame(comparison).T
st.header("💡 Estimated Cost Comparison")
st.dataframe(df.style.format("${:,.2f}"))
