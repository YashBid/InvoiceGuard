"""InvoiceGuard — Rate cards."""
import streamlit as st
import pandas as pd
from pathlib import Path
from core.database import get_rate_card, insert_rate_cards, init_db
from core.ui import inject_css

st.set_page_config(page_title="Rate Cards | InvoiceGuard", page_icon="📋", layout="wide")
st.sidebar.markdown("# 🛡️ InvoiceGuard")
inject_css()
st.title("📋 Rate Cards")

rate_card = get_rate_card()
if rate_card:
    df = pd.DataFrame(rate_card)
    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.info("No rate cards loaded. Upload a CSV or use the sample.")

st.subheader("Upload rate card CSV")
st.caption("CSV should have columns: vendor_name, item_description, unit_rate, unit, valid_from, valid_until")
uploaded = st.file_uploader("Choose CSV", type=["csv"])
if uploaded:
    try:
        new_df = pd.read_csv(uploaded)
        required = ["vendor_name", "item_description", "unit_rate"]
        if all(c in new_df.columns for c in required):
            insert_rate_cards(new_df.to_dict("records"))
            st.success("Rate cards imported.")
            st.rerun()
        else:
            st.error(f"CSV must have columns: {required}")
    except Exception as e:
        st.error(str(e))

sample_path = Path(__file__).resolve().parent.parent / "data" / "sample_rate_card.csv"
if sample_path.exists():
    st.download_button(
        "📥 Download sample rate card CSV",
        sample_path.read_text(),
        "sample_rate_card.csv",
        mime="text/csv",
    )
