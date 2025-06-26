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

all_models = ["TwelveLabs"] + selected_competitors

# Prepare Unit Price Comparison Table
unit_price_data = {
    "Video Input ($/hr)": [0.0],
    "Analyzed Video ($/hr)": [twelvelabs_pricing["video"]],
    "Text Output ($/1M tokens)": [7.5],
}
for name in selected_competitors:
    model = competitor_pricing[name]
    unit_price_data["Video Input ($/hr)"].append(model["video"])
    unit_price_data["Analyzed Video ($/hr)"].append(0.0)
    unit_price_data["Text Output ($/1M tokens)"].append(model["output"])
unit_price_df = pd.DataFrame(unit_price_data, index=all_models).T

# Prepare Cost Breakdown Table
video_input_row = [0.0]
analyzed_video_row = [total_analyze_queries * (avg_video_duration / 60) * twelvelabs_pricing["video"]]
video_indexing_row = [index_video_hours * twelvelabs_pricing["video"]]
text_output_row = [total_analyze_queries * avg_output_tokens * twelvelabs_pricing["output"]]
total_row = [video_input_row[0] + analyzed_video_row[0] + video_indexing_row[0] + text_output_row[0]]

for name in selected_competitors:
    model = competitor_pricing[name]
    video_input = total_analyze_queries * (avg_video_duration / 60) * model["video"]
    analyzed_video_row.append(0.0)
    video_indexing_row.append(0.0)
    text_output = total_analyze_queries * avg_output_tokens / 1_000_000 * model["output"]
    video_input_row.append(video_input)
    text_output_row.append(text_output)
    total_row.append(video_input + text_output)

breakdown_df = pd.DataFrame({
    "Video Input Cost": video_input_row,
    "Analyzed Video Cost": analyzed_video_row,
    "Video Indexing Cost": video_indexing_row,
    "Text Output Cost": text_output_row,
    "Total Cost": total_row,
}, index=all_models).T

# Prepare Total Cost Table
total_cost_df = pd.DataFrame({model: [cost] for model, cost in zip(all_models, total_row)}, index=["Total Cost"])

# Display Tables
st.header("🔍 Unit Price Comparison")
st.dataframe(unit_price_df.style.format("${:,.2f}"))

st.header("🧮 Cost Breakdown")
st.dataframe(breakdown_df.style.format("${:,.2f}"))

st.header("📊 Total Cost")
st.dataframe(total_cost_df.style.format("${:,.2f}"))
