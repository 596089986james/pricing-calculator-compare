import streamlit as st
import pandas as pd

st.set_page_config(page_title="Competitor Pricing Comparison", layout="wide")
st.title("Pegasus vs Competitor Pricing Calculator")
st.caption("Compare estimated costs for analyzing video content across different models.")

# User Inputs
st.sidebar.header("Input Parameters")

# Core Inputs
num_videos = st.sidebar.number_input("Number of Videos", min_value=0, value=6000, step=100)
avg_video_duration = st.sidebar.number_input("Avg Video Duration (min)", min_value=1, value=10)
total_video_hours = (num_videos * avg_video_duration) / 60
st.sidebar.markdown(f"**Total Video Hours:** {total_video_hours:.2f} hr")

total_analyze_queries = st.sidebar.number_input("Total Analyze Queries", min_value=0, value=30000, step=100)
avg_input_tokens = st.sidebar.number_input("Avg Input Tokens per Analyze", min_value=0, value=200)
avg_output_tokens = st.sidebar.number_input("Avg Output Tokens per Analyze", min_value=0, value=100)

# Embedding Inputs
st.sidebar.divider()
st.sidebar.subheader("Embedding Usage")
embed_video_hours = st.sidebar.number_input("Video Embedding (hrs)", min_value=0.0, value=0.0, step=1.0)
embed_image_k = st.sidebar.number_input("Image Embedding (thousands)", min_value=0.0, value=0.0, step=1.0)
embed_text_k = st.sidebar.number_input("Text Embedding (thousands)", min_value=0.0, value=0.0, step=1.0)

# Contract Length Input
st.sidebar.divider()
contract_length = st.sidebar.number_input("Contract Length (months)", min_value=1, value=12, step=1)

# Competitor Model Pricing
competitor_pricing = {
    "Google Embed": {"embed_video": 3.60, "embed_image": 0.10, "embed_text": 0.07},
    "Gemini 2.5 Pro (<=12min)": {"video": 1.25, "input": 1.25, "output": 10},
    "Gemini 2.5 Pro (>12min)": {"video": 2.50, "input": 2.50, "output": 15},
    "Gemini 2.5 Flash": {"video": 0.30, "input": 0.30, "output": 2.50},
    "GPT 4.1-mini": {"video": 0.40, "input": 0.40, "output": 1.00},
    "GPT 4.1": {"video": 2.00, "input": 2.00, "output": 8.00},
    "Nova Lite": {"video": 0.06, "input": 0.06, "output": 0.24},
    "Nova Pro": {"video": 0.80, "input": 0.80, "output": 3.20},
}

# TwelveLabs Pricing
infra_rate = 0.09  # $ per hour indexed per month

twelvelabs_pricing = {
    "video": 1.25,  # $/hr for analyzed video
    "index": 2.5,   # $/hr for indexing
    "output": 7.5 / 1_000_000  # $/token
}

# Model Selection
selected_competitors = st.multiselect("Select Competitors to Compare", options=list(competitor_pricing.keys()))
all_models = ["TwelveLabs"] + selected_competitors

# Unit Price Comparison
tunit_price_data = {
    "Video Indexing ($/hr)": [twelvelabs_pricing["index"]],
    "Analyzed Video Cost ($/hr or $/M tokens)": [twelvelabs_pricing["video"]],
    "Text Output ($/1M tokens)": [7.5],
    "Embedding Video ($/hr)": [2.5],
    "Embedding Image ($/1k)": [0.1],
    "Embedding Text ($/1k)": [0.07],
    "Infra Cost ($/hr indexed/mo)": [infra_rate]
}
for name in selected_competitors:
    model = competitor_pricing[name]
    tunit_price_data["Video Indexing ($/hr)"].append(0.0)
    tunit_price_data["Analyzed Video Cost ($/hr + $/M tokens)"].append(model.get("input", 0.0))
    tunit_price_data["Text Output ($/1M tokens)"].append(model.get("output", 0.0))
    tunit_price_data["Embedding Video ($/hr)"].append(model.get("embed_video", 0.0))
    tunit_price_data["Embedding Image ($/1k)"].append(model.get("embed_image", 0.0))
    tunit_price_data["Embedding Text ($/1k)"].append(model.get("embed_text", 0.0))
    tunit_price_data["Infra Cost ($/hr indexed/mo)"].append(0.0)

unit_price_df = pd.DataFrame(tunit_price_data, index=all_models).T

# Cost Breakdown
tvideo_indexing_row = [total_video_hours * twelvelabs_pricing["index"]]
tanalyzed_video_row = [total_analyze_queries * (avg_video_duration / 60) * twelvelabs_pricing["video"]]
ttext_output_row = [total_analyze_queries * avg_output_tokens * twelvelabs_pricing["output"]]
tembed_costs = [embed_video_hours * 2.5 + embed_image_k * 0.1 + embed_text_k * 0.07]
tinfra_cost_row = [total_video_hours * infra_rate * contract_length]

for name in selected_competitors:
    model = competitor_pricing[name]
    tvideo_indexing_row.append(0.0)
    comp_analyze = (
        total_analyze_queries * avg_input_tokens / 1_000_000
        + total_analyze_queries * (avg_video_duration / 60)
    ) * model.get("input", 0.0)
    tanalyzed_video_row.append(comp_analyze)
    ttext_output_row.append(total_analyze_queries * avg_output_tokens / 1_000_000 * model.get("output", 0.0))
    tembed_costs.append(
        embed_video_hours * model.get("embed_video", 0.0)
        + embed_image_k * model.get("embed_image", 0.0)
        + embed_text_k * model.get("embed_text", 0.0)
    )
    tinfra_cost_row.append(0.0)

breakdown_df = pd.DataFrame({
    "Video Indexing Cost": tvideo_indexing_row,
    "Analyzed Video Cost": tanalyzed_video_row,
    "Text Output Cost": ttext_output_row,
    "Embedding Cost": tembed_costs,
    "Infra Cost": tinfra_cost_row
}, index=all_models).T
breakdown_df.loc["Total Cost"] = breakdown_df.sum()

# Display Tables
st.header("🔍 Unit Price Comparison")
st.dataframe(unit_price_df.style.format("${:,.2f}"))

st.header("🧮 Cost Breakdown")
st.dataframe(breakdown_df.style.format("${:,.2f}"))
