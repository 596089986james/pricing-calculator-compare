import streamlit as st
import pandas as pd

st.set_page_config(page_title="Competitor Pricing Comparison", layout="wide")
st.title("TwelveLabs vs Competitor Pricing Calculator")
st.caption("Compare estimated costs for analyzing video content across different models.")

# User Inputs
st.sidebar.header("Input Parameters")

# Embedding Inputs
st.sidebar.subheader("Embedding Usage")
embed_video_hours = st.sidebar.number_input("Video Embedding (hrs)", min_value=0.0, value=0.0, step=1.0)
embed_image_k = st.sidebar.number_input("Image Embedding (per 1k)", min_value=0.0, value=0.0, step=100.0)
embed_text_k = st.sidebar.number_input("Text Embedding (per 1k)", min_value=0.0, value=0.0, step=100.0)
num_videos = st.sidebar.number_input("Number of Videos", min_value=0, value=6000, step=100)
avg_video_duration = st.sidebar.number_input("Avg Video Duration (min)", min_value=1, value=10)
total_video_hours = (num_videos * avg_video_duration) / 60
st.sidebar.markdown(f"**Total Video Hours:** {total_video_hours:.2f} hr")
total_analyze_queries = st.sidebar.number_input("Total Analyze Queries", min_value=0, value=10000, step=100)
avg_input_tokens = st.sidebar.number_input("Avg Input Tokens per Analyze", min_value=0, value=200)
avg_output_tokens = st.sidebar.number_input("Avg Output Tokens per Analyze", min_value=0, value=100)

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
twelvelabs_pricing = {
    "video": 1.25,  # $/hr for analyzed video
    "index": 2.5,  # $/hr for indexing
    "output": 7.5 / 1_000_000  # $/token
}

# Competitor Selection
selected_competitors = st.multiselect("Select Competitors to Compare", options=list(competitor_pricing.keys()))

all_models = ["TwelveLabs"] + selected_competitors

# Prepare Unit Price Comparison Table
unit_price_data = {
    "Video Indexing ($/hr)": [twelvelabs_pricing["index"]],
    "Analyzed Video Cost ($/hr + $/M tokens)": [twelvelabs_pricing["video"]],
    "Text Output ($/1M tokens)": [7.5],
    "Embedding Video ($/hr)": [2.5],
    "Embedding Image ($/1k)": [0.1],
    "Embedding Text ($/1k)": [0.07],
}
for name in selected_competitors:
    model = competitor_pricing[name]
    unit_price_data["Video Indexing ($/hr)"].append(0.0)
    combined_input_price = model["input"]  # use only one consistent unit price as specified
    unit_price_data["Analyzed Video Cost ($/hr + $/M tokens)"].append(combined_input_price)
    unit_price_data["Text Output ($/1M tokens)"].append(model.get("output", 0.0))
    unit_price_data["Embedding Video ($/hr)"].append(model.get("embed_video", 0.0))
    unit_price_data["Embedding Image ($/1k)"].append(model.get("embed_image", 0.0))
    unit_price_data["Embedding Text ($/1k)"].append(model.get("embed_text", 0.0))

unit_price_df = pd.DataFrame(unit_price_data, index=all_models).T

# Prepare Cost Breakdown Table
video_indexing_row = [total_video_hours * twelvelabs_pricing["index"]]
video_input_row = [0.0]
analyzed_video_row = [total_analyze_queries * (avg_video_duration / 60) * twelvelabs_pricing["video"]]
text_output_row = [total_analyze_queries * avg_output_tokens * twelvelabs_pricing["output"]]
embed_cost_tl = embed_video_hours * 2.5 + embed_image_k * 0.1 + embed_text_k * 0.07
embed_costs = [embed_cost_tl]
total_row = [video_indexing_row[0] + analyzed_video_row[0] + text_output_row[0] + embed_cost_tl]

for name in selected_competitors:
    model = competitor_pricing[name]
    video_indexing_row.append(0.0)
    video_input = total_video_hours * model["video"]
    analyzed_input = (
        total_analyze_queries * avg_input_tokens / 1_000_000 * model["input"] +
        total_analyze_queries * (avg_video_duration / 60) * model["input"]
    )
    output_cost = total_analyze_queries * avg_output_tokens / 1_000_000 * model["output"]
    video_input_row.append(video_input)
    analyzed_video_row.append(analyzed_input)
    text_output_row.append(output_cost)
    embed = embed_video_hours * model.get("embed_video", 0.0) + embed_image_k * model.get("embed_image", 0.0) + embed_text_k * model.get("embed_text", 0.0)
    embed_costs.append(embed)
    total_row.append(video_input + analyzed_input + output_cost + embed)

analyzed_combined_row = [analyzed_video_row[0] + video_input_row[0]]
for i in range(1, len(all_models)):
    analyzed_combined_row.append(analyzed_video_row[i] + video_input_row[i])

breakdown_df = pd.DataFrame({
    "Video Indexing Cost": video_indexing_row,
    "Analyzed Video Cost": analyzed_combined_row,
    "Text Output Cost": text_output_row,
    "Embedding Cost": embed_costs,
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
