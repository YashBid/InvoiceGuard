"""InvoiceGuard — Flagged items."""
import streamlit as st
import pandas as pd
from core.database import get_all_flags, get_all_invoices
from core.ui import inject_css

st.set_page_config(page_title="Flagged | InvoiceGuard", page_icon="🚩", layout="wide")
st.sidebar.markdown("# 🛡️ InvoiceGuard")
inject_css()
st.title("🚩 Flagged")

flags = get_all_flags()
invoices = get_all_invoices()
inv_by_id = {i["id"]: i for i in invoices}

if not flags:
    st.info("No flags yet. Upload and process invoices to see flagged items.")
    st.stop()

# Pre-compute flag count per invoice
flags_per_invoice: dict[int, list] = {}
for f in flags:
    fid = f["invoice_id"]
    flags_per_invoice.setdefault(fid, []).append(f)

# Filter — flag type only (show invoice if ANY of its flags match)
all_types = sorted({f["flag_type"] for f in flags})
type_filter = st.multiselect("Filter by flag type", options=all_types, default=all_types)

# Keep invoices that have at least one flag matching the selected types
filtered_inv_ids = {
    fid for fid, inv_flags in flags_per_invoice.items()
    if any(f["flag_type"] in type_filter for f in inv_flags)
}

# Build one row per invoice
rows = []
for inv_id in sorted(filtered_inv_ids):          # sorted keeps oldest first
    inv = inv_by_id.get(inv_id, {})
    inv_flags = flags_per_invoice[inv_id]

    # Only include flags that match the filter in the detail columns
    matching_flags = [f for f in inv_flags if f["flag_type"] in type_filter]

    flag_types   = ", ".join(sorted({f["flag_type"] for f in matching_flags}))
    descriptions = "  |  ".join(f["description"] for f in matching_flags)
    total_oc     = sum(f.get("overcharge", 0) for f in matching_flags)
    num_flags    = len(matching_flags)

    rows.append({
        "ID":                   inv_id,
        "Vendor":               inv.get("vendor_name", "—"),
        "Invoice #":            inv.get("invoice_number", "—"),
        "Flag Types":           flag_types,
        "Findings":             descriptions,
        "Billed (₹)":           sum(f.get("billed_amount", 0) for f in matching_flags),
        "Correct (₹)":          sum(f.get("correct_amount", 0) for f in matching_flags),
        "Overcharge (₹)":       total_oc,
        "# Flags":              num_flags,
    })

df = pd.DataFrame(rows) if rows else pd.DataFrame()

if df.empty:
    st.info("No flags match the selected filter.")
else:
    st.dataframe(df, use_container_width=True, hide_index=True)

total_shown_oc = sum(r["Overcharge (₹)"] for r in rows)
st.caption(
    f"Showing {len(rows)} flagged invoice{'s' if len(rows) != 1 else ''} "
    f"· ₹{total_shown_oc:,.0f} overcharge in view"
)
