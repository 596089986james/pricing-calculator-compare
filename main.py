import streamlit as st
import pandas as pd

st.set_page_config(page_title="Competitor Pricing Compare", layout="centered")

st.title("TwelveLabs - Competitor Pricing Compare")
st.caption("For more accurate pricing and advanced usage, please contact the finance team.")

# Default Pricing
default_pricing = {
    "index_cost_per_hour": 2.500,
    "infra_unit_price": 0.090,
    "search_cost_per_call": 0.004,
    "embedding_cost": {
        "video": 2.5,
        "audio": 0.5,
        "image": 0.1,
        "text": 0.07
    },
    "output_token_cost_pegasus": 7.5,
    "input_video_seconds_price": 0.00035
}

# Sidebar Inputs
st.sidebar.image("marengo.png", use_container_width=True)
marengo_video_hours = st.sidebar.number_input(
    "Marengo - Video Hours", min_value=0, step=100, value=10000, format="%d"
)
marengo_search_calls = st.sidebar.number_input(
    "Marengo - Daily Search API Calls", min_value=0, step=100, value=2000, format="%d"
)

st.sidebar.image("pegasus.png", use_container_width=True)
pegasus_video_hours = st.sidebar.number_input(
    "Pegasus - Video Hours", min_value=0, step=100, value=10000, format="%d"
)
pegasus_generate_calls = st.sidebar.number_input(
    "Pegasus - Daily Generate API Calls", min_value=0, step=100, value=2000, format="%d"
)
pegasus_output_tokens_per_call = st.sidebar.number_input(
    "Pegasus - Output Tokens per Call", min_value=0, step=1, value=200, format="%d"
)

average_video_length_sec = st.sidebar.number_input(
    "Average Video Length (sec)", min_value=1, step=1, value=90, format="%d"
)

# Contract Inputs
st.sidebar.header("Contract Setting")
contract_years = st.sidebar.number_input(
    "Number of Contract Years", min_value=1, step=1, value=1, format="%d"
)
reindex_frequency = st.sidebar.number_input(
    "Reindex Frequency (per year)",
    min_value=0, step=1, value=0, format="%d",
    help=(
        "Number of times the video is expected to be reindexed each year. "
        "Initial indexing is included in year 1."
    )
)

# Embedding Inputs
st.sidebar.header("🔍 Embedding Inputs")
video_embeddings_h = st.sidebar.number_input(
    "Video Embeddings (hour)", min_value=0, step=1, value=0, format="%d"
)
audio_embeddings_h = st.sidebar.number_input(
    "Audio Embeddings (hour)", min_value=0, step=1, value=0, format="%d"
)
image_embeddings_1k = st.sidebar.number_input(
    "Image Embeddings (per 1k)", min_value=0, step=1, value=0, format="%d"
)
text_embeddings_1k = st.sidebar.number_input(
    "Text Embeddings (per 1k)", min_value=0, step=1, value=0, format="%d"
)

# Advanced Unit Pricing
with st.expander("📊 Adjust Unit Pricing (Advanced)"):
    pricing = {
        "index_cost_per_hour": default_pricing["index_cost_per_hour"],
        "infra_unit_price": default_pricing["infra_unit_price"],
        "search_cost_per_call": default_pricing["search_cost_per_call"],
        "embedding_cost": default_pricing["embedding_cost"].copy(),
        "output_token_cost_pegasus": default_pricing["output_token_cost_pegasus"],
        "input_video_seconds_price": default_pricing["input_video_seconds_price"]
    }
    pricing["index_cost_per_hour"] = st.number_input(
        "Indexing ($/hr)", pricing["index_cost_per_hour"], format="%.3f"
    )
    pricing["infra_unit_price"] = st.number_input(
        "Infra Fee ($/hr/mo)", pricing["infra_unit_price"], format="%.3f"
    )
    pricing["search_cost_per_call"] = st.number_input(
        "Search API Call Cost ($/call)", pricing["search_cost_per_call"], format="%.3f"
    )
    pricing["embedding_cost"]["video"] = st.number_input(
        "Video Embedding ($/hour)", pricing["embedding_cost"]["video"], format="%.3f"
    )
    pricing["embedding_cost"]["audio"] = st.number_input(
        "Audio Embedding ($/hour)", pricing["embedding_cost"]["audio"], format="%.3f"
    )
    pricing["embedding_cost"]["image"] = st.number_input(
        "Image Embedding ($/1k)", pricing["embedding_cost"]["image"], format="%.3f"
    )
    pricing["embedding_cost"]["text"] = st.number_input(
        "Text Embedding ($/1k)", pricing["embedding_cost"]["text"], format="%.3f"
    )
    pricing["output_token_cost_pegasus"] = st.number_input(
        "Pegasus Output Tokens ($/1M)", pricing["output_token_cost_pegasus"], format="%.3f"
    )
    pricing["input_video_seconds_price"] = st.number_input(
        "Input Video Seconds ($/sec)", pricing["input_video_seconds_price"], format="%.5f"
    )

# Helper for Embedding Costs
def calculate_embedding_costs(times=1):
    return times * (
        video_embeddings_h * pricing["embedding_cost"]["video"] +
        audio_embeddings_h * pricing["embedding_cost"]["audio"] +
        (image_embeddings_1k * pricing["embedding_cost"]["image"]) / 1000 +
        (text_embeddings_1k * pricing["embedding_cost"]["text"]) / 1000
    )

# Yearly Breakdown for TwelveLabs
total_cost = 0
for year in range(1, contract_years + 1):
    is_first_year = (year == 1)
    mar_reindex_times = max(0, reindex_frequency - 1) if is_first_year else reindex_frequency
    peg_reindex_times = max(0, reindex_frequency - 1) if is_first_year else reindex_frequency
    embedding_times = 1 + mar_reindex_times if is_first_year else reindex_frequency

    mar_index = marengo_video_hours * pricing["index_cost_per_hour"] if is_first_year else 0
    peg_index = pegasus_video_hours * pricing["index_cost_per_hour"] if is_first_year else 0
    mar_reindex = marengo_video_hours * pricing["index_cost_per_hour"] * mar_reindex_times
    peg_reindex = pegasus_video_hours * pricing["index_cost_per_hour"] * peg_reindex_times

    peg_input = (
        pegasus_generate_calls * 365 * pricing["input_video_seconds_price"] * average_video_length_sec
    )
    peg_output = (
        pegasus_generate_calls * 365 * pegasus_output_tokens_per_call / 1_000_000 * pricing["output_token_cost_pegasus"]
    )

    mar_infra = marengo_video_hours * pricing["infra_unit_price"] * 12
    peg_infra = pegasus_video_hours * pricing["infra_unit_price"] * 12
    search_cost = marengo_search_calls * pricing["search_cost_per_call"] * 365
    embedding_cost = calculate_embedding_costs(times=embedding_times)

    marengo = {
        "Indexing": mar_index,
        "Reindexing": mar_reindex,
        "Search": search_cost,
        "Infra": mar_infra,
        "Embedding": embedding_cost,
        "Input Prompts": 0,
        "Output Tokens": 0
    }
    marengo["Total"] = sum(marengo.values())

    pegasus = {
        "Indexing": peg_index,
        "Reindexing": peg_reindex,
        "Infra": peg_infra,
        "Search": 0,
        "Embedding": 0,
        "Input Prompts": peg_input,
        "Output Tokens": peg_output
    }
    pegasus["Total"] = sum(pegasus.values())

    df = pd.DataFrame({"Marengo": marengo, "Pegasus": pegasus})
    st.header(f"📊 Cost Breakdown for Year {year}")
    st.dataframe(df.style.format("${:,.0f}"))

    total_cost += marengo["Total"] + pegasus["Total"]

# Final Total for TwelveLabs
st.markdown("---")
st.success(f"🎯 Total Estimated {contract_years}-Year Cost: ${total_cost:,.0f}")

# Competitor Pricing Section
st.header("⚔️ Competitor Pricing")

# Total counts
num_videos = pegasus_video_hours / (average_video_length_sec / 3600)
total_queries = pegasus_generate_calls * 365 * contract_years

# Competitor unit rates
competitor_pricing = {
    "Google Embed": {"video": 3.60, "image": 0.10, "text": 0.07},
    "Gemini 2.5 Pro (<=12 min)": {"video": 1.25, "output": 10},
    "Gemini 2.5 Pro (>12 min)":  {"video": 2.50, "output": 15},
    "Gemini 2.5 Flash":         {"video": 0.30, "output": 2.50},
    "GPT 4.1-mini":              {"video": 0.40, "output": 1.00},
    "GPT 4.1":                   {"video": 2.00, "output": 8.00},
    "Nova Lite":                 {"video": 0.06, "output": 0.24},
    "Nova Pro":                  {"video": 0.80, "output": 3.20}
}

# Show unit pricing# Show unit pricing\unit_df = pd.DataFrame(competitor_pricing).T.rename(columns={"video": "Video $/hr", "output": "Output $/1M tokens", "image": "Image Embed $/1k", "text": "Text Embed $/1k"})
st.subheader("Unit Pricing")
st.dataframe(unit_df.style.format("${:,.2f}"))

# Compute and show cost breakdown
rows = {}
for name, rates in competitor_pricing.items():
    video_cost = total_queries * (average_video_length_sec / 3600) * rates.get("video", 0)
    token_cost = total_queries * pegasus_output_tokens_per_call / 1_000_000 * rates.get("output", 0)
    embed_cost = (
        video_embeddings_h * rates.get("video", 0) + image_embeddings_1k * rates.get("image", 0) / 1000 + text_embeddings_1k * rates.get("text", 0) / 1000
    ) * contract_years
    rows[name] = {
        "Video Cost": video_cost,
        "Output Token Cost": token_cost,
        "Embedding Cost": embed_cost,
        "Total": video_cost + token_cost + embed_cost
    }

comp_df = pd.DataFrame(rows).T
st.subheader("Cost Breakdown")
st.dataframe(comp_df.style.format("${:,.2f}"))
