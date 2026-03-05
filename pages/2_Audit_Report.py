import json
import streamlit as st
import pandas as pd
from core.database import get_all_invoices, get_invoice_full, get_flags_for_invoice
from core.ui import inject_css

st.set_page_config(page_title="Audit Report | InvoiceGuard", page_icon="📋", layout="wide")
st.sidebar.markdown("# 🛡️ InvoiceGuard")
inject_css()
st.title("📋 Audit Report")

invoices = get_all_invoices()
if not invoices:
    st.info("No invoices yet. Upload and process invoices from the main page.")
    st.stop()

# Invoice selector — most recent first
options = {
    f"{i.get('filename', 'Unknown')}  ({i.get('invoice_date', '—')})": i["id"]
    for i in reversed(invoices)
}
selected_label = st.selectbox("Select invoice", list(options.keys()))
invoice_id = options[selected_label]

inv = get_invoice_full(invoice_id)
flags = get_flags_for_invoice(invoice_id)

# Parse raw_json if available
raw = inv.get("raw_json") or "{}"
try:
    parsed = json.loads(raw)
except Exception:
    parsed = {}

line_items = parsed.get("line_items", [])
surcharges = parsed.get("surcharges", [])

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("---")
h1, h2, h3 = st.columns(3)
with h1:
    st.markdown("**Vendor**")
    st.markdown(f"### {inv.get('vendor_name') or '—'}")
    st.caption(f"GSTIN: {inv.get('vendor_gstin') or 'Not provided'}")
with h2:
    st.markdown("**Invoice Details**")
    st.markdown(f"**#** {inv.get('invoice_number') or '—'}")
    st.markdown(f"**Date:** {inv.get('invoice_date') or '—'}")
    st.markdown(f"**File:** {inv.get('filename') or '—'}")
with h3:
    st.markdown("**Financials**")
    grand_total = inv.get("grand_total") or 0
    subtotal = parsed.get("subtotal") or 0
    total_tax = parsed.get("total_tax") or 0
    st.metric("Grand Total", f"₹{grand_total:,.2f}")
    st.caption(f"Subtotal: ₹{subtotal:,.2f} | Tax: ₹{total_tax:,.2f}")

# ── Line Items ────────────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("📦 Line Items")
if line_items:
    rows = []
    for item in line_items:
        billed_gst = (
            (item.get("cgst_rate") or 0)
            + (item.get("sgst_rate") or 0)
            + (item.get("igst_rate") or 0)
        )
        gst_ok = item.get("gst_correct", True)
        rows.append({
            "Description": item.get("description", "—"),
            "HSN Code": item.get("hsn_code") or "—",
            "Qty": item.get("quantity", 0),
            "Unit": item.get("unit", "—"),
            "Unit Rate (₹)": item.get("unit_rate", 0),
            "Amount (₹)": item.get("amount", 0),
            "GST %": billed_gst,
            "Expected GST %": item.get("gst_expected_rate") or billed_gst,
            "GST ✓": "✅" if gst_ok else "❌",
            "GST Note": item.get("gst_note") or "",
        })
    df_items = pd.DataFrame(rows)

    def _highlight_gst(row):
        if row["GST ✓"] == "❌":
            return ["background-color: #e85d4a22"] * len(row)
        return [""] * len(row)

    st.dataframe(
        df_items.style.apply(_highlight_gst, axis=1),
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info("No line item data available (invoice may have been loaded as demo data without raw JSON).")

# ── Surcharges ────────────────────────────────────────────────────────────────
if surcharges:
    st.markdown("---")
    st.subheader("➕ Surcharges")
    df_surch = pd.DataFrame(surcharges)
    df_surch.columns = ["Name", "Amount (₹)"]
    st.dataframe(df_surch, use_container_width=True, hide_index=True)

# ── Flags / Findings ──────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("🚩 Findings & Flags")

if flags:
    total_overcharge = sum(f.get("overcharge", 0) for f in flags)

    FLAG_COLORS = {
        "GST_MISMATCH":       "#e85d4a",
        "DUPLICATE_INVOICE":  "#f0b429",
        "RATE_EXCEEDED":      "#4f94ef",
        "CALCULATION_ERROR":  "#3ecf8e",
        "MYSTERY_SURCHARGE":  "#b44fef",
    }

    flag_rows = []
    for f in flags:
        flag_rows.append({
            "Flag Type": f.get("flag_type", "—"),
            "Description": f.get("description", "—"),
            "Billed (₹)": f.get("billed_amount", 0),
            "Correct (₹)": f.get("correct_amount", 0),
            "Overcharge (₹)": f.get("overcharge", 0),
            "Severity": f.get("severity", "—").upper(),
        })

    df_flags = pd.DataFrame(flag_rows)

    def _color_flag(val):
        return f"color: {FLAG_COLORS.get(val, '#888')}; font-weight: bold"

    styled_flags = df_flags.style.map(_color_flag, subset=["Flag Type"])
    st.dataframe(styled_flags, use_container_width=True, hide_index=True)
    st.error(f"💸 Total overcharge on this invoice: **₹{total_overcharge:,.2f}**")
else:
    st.success("✅ No flags found — this invoice appears clean.")

# ── Recommended Actions ───────────────────────────────────────────────────────
if flags:
    st.markdown("---")
    st.subheader("✅ Recommended Actions")

    ACTION_TEMPLATES = {
        "GST_MISMATCH": "Request a GST correction credit note from {vendor} for ₹{overcharge:,.0f} — incorrect GST rate applied.",
        "RATE_EXCEEDED": "Dispute rate overcharge of ₹{overcharge:,.0f} with {vendor} — raise credit note request citing contract rate.",
        "DUPLICATE_INVOICE": "⚠️ HOLD PAYMENT — possible duplicate invoice from {vendor}. Verify with vendor before processing.",
        "CALCULATION_ERROR": "Request a corrected invoice from {vendor} — arithmetic error of ₹{overcharge:,.0f} detected.",
        "MYSTERY_SURCHARGE": "Request written justification from {vendor} for unlisted surcharge (₹{overcharge:,.0f}). Reject if not in contract.",
    }

    vendor = inv.get("vendor_name") or "vendor"
    seen_types = set()
    for f in flags:
        ftype = f.get("flag_type", "")
        template = ACTION_TEMPLATES.get(ftype)
        if template:
            action = template.format(vendor=vendor, overcharge=f.get("overcharge", 0))
            icon = "🔴" if f.get("severity") == "critical" else "🟡"
            st.markdown(f"{icon} {action}")
            seen_types.add(ftype)
