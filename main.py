import streamlit as st
import pandas as pd

st.set_page_config(page_title="Competitor Pricing Compare", layout="centered")

st.title("TwelveLabs - Competitor Pricing Compare")
st.caption("For more accurate pricing and advanced usage, please contact the finance team.")

# Default Pricing
default_pricing = {
    "index_cost_per_hour": 2.5,
    "infra_unit_price": 0.09,
    "search_cost_per_call": 0.004,
    "embedding_cost": {"video": 2.5, "audio": 0.5, "image": 0.1, "text": 0.07},
    "output_token_cost_pegasus": 7.5,
    "input_video_seconds_price": 0.00035,
}

# Sidebar Inputs
st.sidebar.image("marengo.png", use_container_width=True)
marengo_video_hours = st.sidebar.number_input("Marengo - Video Hours", min_value=0, step=100, value=10000)
marengo_search_calls = st.sidebar.number_input("Marengo - Daily Search API Calls", min_value=0, step=100, value=2000)

st.sidebar.image("pegasus.png", use_container_width=True)
pegasus_video_hours = st.sidebar.number_input("Pegasus - Video Hours", min_value=0, step=100, value=10000)
pegasus_generate_calls = st.sidebar.number_input("Pegasus - Daily Generate API Calls", min_value=0, step=100, value=2000)
pegasus_input_tokens_per_call = st.sidebar.number_input("Pegasus - Input Tokens per Call", min_value=0, step=1, value=200)
pegasus_output_tokens_per_call = st.sidebar.number_input("Pegasus - Output Tokens per Call", min_value=0, step=1, value=200)

average_video_length_sec = st.sidebar.number_input("Average Video Length (sec)", min_value=1, step=1, value=90)

# Contract Settings
st.sidebar.header("Contract Setting")
contract_years = st.sidebar.number_input("Number of Contract Years", min_value=1, step=1, value=1)
reindex_frequency = st.sidebar.number_input(
    "Reindex Frequency (per year)", min_value=0, step=1, value=0,
    help="# times to reindex per year; initial indexing included in year 1"
)

# Embedding Inputs
st.sidebar.header("🔍 Embedding Inputs")
video_embeddings_h = st.sidebar.number_input("Video Embeddings (hours)", min_value=0, step=1, value=0)
audio_embeddings_h = st.sidebar.number_input("Audio Embeddings (hours)", min_value=0, step=1, value=0)
image_embeddings_1k = st.sidebar.number_input("Image Embeddings (per 1k)", min_value=0, step=1, value=0)
text_embeddings_1k = st.sidebar.number_input("Text Embeddings (per 1k)", min_value=0, step=1, value=0)

# Advanced Pricing
with st.expander("📊 Adjust Unit Pricing (Advanced)"):
    pricing = {**default_pricing}
    pricing["index_cost_per_hour"] = st.number_input("Indexing ($/hr)", value=pricing["index_cost_per_hour"], format="%.3f")
    pricing["infra_unit_price"] = st.number_input("Infra Fee ($/hr/mo)", value=pricing["infra_unit_price"], format="%.3f")
    pricing["search_cost_per_call"] = st.number_input("Search API Call ($/call)", value=pricing["search_cost_per_call"], format="%.3f")
    pricing["embedding_cost"]["video"] = st.number_input("Video Embedding ($/hr)", value=pricing["embedding_cost"]["video"], format="%.3f")
    pricing["embedding_cost"]["audio"] = st.number_input("Audio Embedding ($/hr)", value=pricing["embedding_cost"]["audio"], format="%.3f")
    pricing["embedding_cost"]["image"] = st.number_input("Image Embedding ($/1k)", value=pricing["embedding_cost"]["image"], format="%.3f")
    pricing["embedding_cost"]["text"] = st.number_input("Text Embedding ($/1k)", value=pricing["embedding_cost"]["text"], format="%.3f")
    pricing["output_token_cost_pegasus"] = st.number_input("Pegasus Output ($/1M)", value=pricing["output_token_cost_pegasus"], format="%.3f")
    pricing["input_video_seconds_price"] = st.number_input("Pegasus Input ($/sec)", value=pricing["input_video_seconds_price"], format="%.5f")

# Embedding cost helper
def emb_cost(times=1):
    return times * (
        video_embeddings_h * pricing["embedding_cost"]["video"] +
        audio_embeddings_h * pricing["embedding_cost"]["audio"] +
        image_embeddings_1k * pricing["embedding_cost"]["image"]/1000 +
        text_embeddings_1k * pricing["embedding_cost"]["text"]/1000
    )

# Calculate TwelveLabs costs
total_cost = 0
for year in range(1, contract_years+1):
    first = (year==1)
    reindex_times = max(0, reindex_frequency - (1 if first else 0))
    # Marengo costs
    mar_index = marengo_video_hours * pricing["index_cost_per_hour"] if first else 0
    mar_reindex = marengo_video_hours * pricing["index_cost_per_hour"] * reindex_times
    mar_search = marengo_search_calls * pricing["search_cost_per_call"] * 365
    mar_infra = marengo_video_hours * pricing["infra_unit_price"] * 12
    mar_emb = emb_cost(times=(1 if first else reindex_frequency))
    # Pegasus costs
    peg_index = pegasus_video_hours * pricing["index_cost_per_hour"] if first else 0
    peg_reindex = pegasus_video_hours * pricing["index_cost_per_hour"] * reindex_times
    peg_input = pegasus_generate_calls*365 * pricing["input_video_seconds_price"] * average_video_length_sec
    peg_output = pegasus_generate_calls*365 * pegasus_output_tokens_per_call/1e6 * pricing["output_token_cost_pegasus"]
    peg_infra = pegasus_video_hours*pricing["infra_unit_price"]*12
    peg_emb = emb_cost(times=(1 if first else reindex_frequency))

    df = pd.DataFrame({
        "Marengo": {
            "Index": mar_index,
            "Reindex": mar_reindex,
            "Search": mar_search,
            "Infra": mar_infra,
            "Embedding": mar_emb
        },
        "Pegasus": {
            "Index": peg_index,
            "Reindex": peg_reindex,
            "Input Prompts": peg_input,
            "Output Tokens": peg_output,
            "Infra": peg_infra,
            "Embedding": peg_emb
        }
    })
    st.header(f"Year {year} Breakdown")
    st.dataframe(df.style.format("${:,.0f}"))
    total_cost += df["Marengo"].sum() + df["Pegasus"].sum()

st.markdown("---")
st.success(f"Total {contract_years}yr Cost: ${total_cost:,.0f}")

# Competitor Pricing
st.header("⚔️ Competitor Pricing")
# totals
daily_queries = pegasus_generate_calls * 365 * contract_years
total_videos = pegasus_video_hours / (average_video_length_sec / 3600)

# Competitor rates
rates = {
    "Google Embed": {"embed_video": 3.60, "embed_image": 0.10, "embed_text": 0.07},
    "Gemini 2.5 Pro (<=12min)": {"analyze": 1.25, "input_tok": 1.25, "output_tok": 10},
    "Gemini 2.5 Pro (>12min)": {"analyze": 2.50, "input_tok": 2.50, "output_tok": 15},
    "Gemini Flash": {"analyze": 0.30, "input_tok": 0.30, "output_tok": 2.50},
    "GPT4.1-mini": {"analyze": 0.40, "input_tok": 0.40, "output_tok": 1.00},
    "GPT4.1": {"analyze": 2.00, "input_tok": 2.00, "output_tok": 8.00},
    "Nova Lite": {"analyze": 0.06, "input_tok": 0.06, "output_tok": 0.24},
    "Nova Pro": {"analyze": 0.80, "input_tok": 0.80, "output_tok": 3.20},
}

# Build unit pricing table
data = {}
for name, r in rates.items():
    data[name] = {
        "Analyze $/hr": r.get("analyze", 0),
        "Input $/1M tokens": r.get("input_tok", 0),
        "Output $/1M tokens": r.get("output_tok", 0),
        "Video Embed $/hr": r.get("embed_video", 0),
        "Image Embed $/1k": r.get("embed_image", 0),
        "Text Embed $/1k": r.get("embed_text", 0),
    }
unit_df = pd.DataFrame(data).T
st.subheader("Unit Pricing")
st.dataframe(unit_df.style.format("${:,.2f}"))

# Build competitor cost breakdown
costs = {}
for name, r in rates.items():
    video_cost = daily_queries * (average_video_length_sec / 3600) * r.get("analyze", 0)
    input_cost = daily_queries * pegasus_input_tokens_per_call / 1e6 * r.get("input_tok", 0)
    output_cost = daily_queries * pegasus_output_tokens_per_call / 1e6 * r.get("output_tok", 0)
    embed_cost = (
        total_videos * r.get("embed_video", 0)
        + image_embeddings_1k * r.get("embed_image", 0) / 1000
        + text_embeddings_1k * r.get("embed_text", 0) / 1000
    )
    costs[name] = {
        "Video Cost": video_cost,
        "Input Token Cost": input_cost,
        "Output Token Cost": output_cost,
        "Embedding Cost": embed_cost,
        "Total": video_cost + input_cost + output_cost + embed_cost
    }
ct_df = pd.DataFrame(costs).T
st.subheader("Cost Breakdown")
st.dataframe(ct_df.style.format("${:,.2f}"))
