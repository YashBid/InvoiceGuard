"""InvoiceGuard — History."""
import streamlit as st
import pandas as pd
from core.database import get_all_invoices
from core.ui import inject_css

st.set_page_config(page_title="History | InvoiceGuard", page_icon="📜", layout="wide")
st.sidebar.markdown("# 🛡️ InvoiceGuard")
inject_css()
st.title("📜 History")

invoices = get_all_invoices()
if not invoices:
    st.info("No invoices yet. Upload and process invoices.")
    st.stop()

df = pd.DataFrame(invoices)
df = df.rename(columns={
    "id":             "ID",
    "filename":       "File",
    "vendor_name":    "Vendor",
    "vendor_gstin":   "GSTIN",
    "invoice_number": "Invoice #",
    "invoice_date":   "Date",
    "grand_total":    "Grand Total (₹)",
    "processed_at":   "Processed at",
})

# Show only relevant columns — no method, no confidence
cols_show = [c for c in ["ID", "File", "Vendor", "GSTIN", "Invoice #", "Date", "Grand Total (₹)", "Processed at"] if c in df.columns]
st.dataframe(df[cols_show], use_container_width=True, hide_index=True)
st.caption(f"Total: {len(invoices)} invoices.")
