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
    pricing = {
        **default_pricing
    }
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
    reindex_times = reindex_frequency - (1 if first else 0)
    idx = pegasus_video_hours * pricing["index_cost_per_hour"] if first else 0
    reidx = pegasus_video_hours * pricing["index_cost_per_hour"] * max(0,reindex_times)
    inp = pegasus_generate_calls*365 * pricing["input_video_seconds_price"] * average_video_length_sec
    outp = pegasus_generate_calls*365 * pegasus_output_tokens_per_call/1e6 * pricing["output_token_cost_pegasus"]
    infra = pegasus_video_hours*pricing["infra_unit_price"]*12
    emb = emb_cost(times=(1 if first else reindex_frequency))
    df = pd.DataFrame({
        "Pegasus": {"Index":idx, "Reindex":reidx, "Input":inp, "Output":outp, "Infra":infra, "Embedding":emb}
    })
    st.header(f"Year {year} Breakdown")
    st.dataframe(df.style.format("${:,.0f}"))
    total_cost += df["Pegasus"].sum()

st.markdown("---")
st.success(f"Total {contract_years}yr Cost: ${total_cost:,.0f}")

# Competitor Pricing
st.header("⚔️ Competitor Pricing")
# totals
n_videos = pegasus_video_hours/(average_video_length_sec/3600)
q = pegasus_generate_calls*365*contract_years
rates = {
    "Google Embed": {"hour":3.60, "img":0.10, "txt":0.07},
    "Gemini 2.5 Pro (<=12min)":{"hour":1.25,"out":10},
    "Gemini 2.5 Pro (>12min)":{"hour":2.50,"out":15},
    "Gemini Flash":{"hour":0.30,"out":2.50},
    "GPT4.1-mini":{"hour":0.40,"out":1.00},
    "GPT4.1":{"hour":2.00,"out":8.00},
    "Nova Lite":{"hour":0.06,"out":0.24},
    "Nova Pro":{"hour":0.80,"out":3.20},
}
# unit table
unit = pd.DataFrame(rates).T.rename(columns={"hour":"Video $/hr","out":"Out $/1M","img":"Img Embed $/1k","txt":"Txt Embed $/1k"})
st.subheader("Unit Pricing")
st.dataframe(unit.style.format("${:,.2f}"))
# cost table
costs = {}
for m,r in rates.items():
    v_cost = q*(average_video_length_sec/3600)*r.get("hour",0)
    t_cost = q*pegasus_output_tokens_per_call/1e6*r.get("out",0)
    e_cost = n_videos*r.get("img",0)*image_embeddings_1k/1000 + n_videos*r.get("txt",0)*text_embeddings_1k/1000
    costs[m] = {"Video":v_cost,"Tokens":t_cost,"Embed":e_cost,"Total":v_cost+t_cost+e_cost}
ct = pd.DataFrame(costs).T
st.subheader("Cost Breakdown")
st.dataframe(ct.style.format("${:,.2f}"))
