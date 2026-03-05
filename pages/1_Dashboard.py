"""InvoiceGuard — Dashboard."""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from core.database import get_all_invoices, get_all_flags
from core import insights_generator
from core.ui import inject_css, metric_cards, insight_list

st.set_page_config(page_title="Dashboard | InvoiceGuard", page_icon="📊", layout="wide")
st.sidebar.markdown("# 🛡️ InvoiceGuard")
inject_css()
st.title("📊 Dashboard")

invoices = get_all_invoices()
flags    = get_all_flags()

# ── Metric cards ──────────────────────────────────────────────────────────────
total_overcharge      = sum(f.get("overcharge", 0) for f in flags)
flagged_invoice_count = len({f["invoice_id"] for f in flags})

metric_cards([
    {"label": "Total Overcharges",  "value": f"₹{total_overcharge:,.0f}", "color": "y"},
    {"label": "Flagged Invoices",   "value": str(flagged_invoice_count),  "color": "r"},
    {"label": "Invoices Processed", "value": str(len(invoices)),          "color": "g"},
])

st.markdown("")  # breathing room

# ── Charts ────────────────────────────────────────────────────────────────────
if flags:
    left, right = st.columns([3, 2], gap="large")

    PLOTLY_LAYOUT = dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=24, b=0),
        font=dict(color="#8b949e"),
    )

    # Horizontal bar — overcharge by vendor
    with left:
        st.caption("OVERCHARGE BY VENDOR")
        overcharge_by_vendor: dict[str, float] = {}
        for f in flags:
            inv = next((i for i in invoices if i.get("id") == f.get("invoice_id")), None)
            vendor = (inv.get("vendor_name", "Unknown") if inv else "Unknown") or "Unknown"
            overcharge_by_vendor[vendor] = overcharge_by_vendor.get(vendor, 0) + f.get("overcharge", 0)

        df_v = pd.DataFrame(
            sorted(overcharge_by_vendor.items(), key=lambda x: x[1]),
            columns=["Vendor", "Overcharge"],
        )

        AMBER_SCALE = ["#2d2208", "#5a3f0f", "#8c6317", "#bf8820", "#f0b429"]
        max_oc = df_v["Overcharge"].max() or 1
        bar_colors = [
            AMBER_SCALE[min(4, int(v / max_oc * 4.99))] for v in df_v["Overcharge"]
        ]

        fig_bar = go.Figure(go.Bar(
            x=df_v["Overcharge"],
            y=df_v["Vendor"],
            orientation="h",
            marker=dict(color=bar_colors, cornerradius=4),
            hovertemplate="<b>%{y}</b><br>₹%{x:,.0f}<extra></extra>",
        ))
        fig_bar.update_layout(
            **PLOTLY_LAYOUT,
            height=max(220, len(df_v) * 52),
            xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
            yaxis=dict(showgrid=False, tickfont=dict(size=12)),
        )
        st.plotly_chart(fig_bar, use_container_width=True, config={"displayModeBar": False})

    # Donut — flag type breakdown
    with right:
        st.caption("FLAGS BY TYPE")
        COLORS = {
            "GST_MISMATCH":      "#e85d4a",
            "DUPLICATE_INVOICE": "#f0b429",
            "RATE_EXCEEDED":     "#4f94ef",
            "CALCULATION_ERROR": "#3ecf8e",
            "MYSTERY_SURCHARGE": "#b44fef",
        }
        LABELS = {
            "GST_MISMATCH":      "GST Mismatch",
            "DUPLICATE_INVOICE": "Duplicate",
            "RATE_EXCEEDED":     "Rate Exceeded",
            "CALCULATION_ERROR": "Calc Error",
            "MYSTERY_SURCHARGE": "Mystery Surcharge",
        }
        type_counts = pd.Series([f.get("flag_type", "UNKNOWN") for f in flags]).value_counts()
        total_flags = len(flags)

        fig_pie = go.Figure(go.Pie(
            labels=[LABELS.get(t, t) for t in type_counts.index],
            values=type_counts.values,
            hole=0.62,
            marker=dict(
                colors=[COLORS.get(t, "#888") for t in type_counts.index],
                line=dict(color="rgba(0,0,0,0)", width=0),
            ),
            textinfo="label+percent",
            textfont=dict(size=10.5, color="#8b949e"),
            hovertemplate="<b>%{label}</b><br>%{value} flags · %{percent}<extra></extra>",
        ))
        fig_pie.update_layout(
            **PLOTLY_LAYOUT,
            height=280,
            showlegend=False,
            annotations=[dict(
                text=f"<b>{total_flags}</b><br><span style='font-size:10px;color:#6e7681'>flags</span>",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=20, color="#c9d1d9"),
            )],
        )
        st.plotly_chart(fig_pie, use_container_width=True, config={"displayModeBar": False})

else:
    st.info("No flags yet — upload and process invoices to see analytics here.")

st.markdown("---")

# ── AI Insights ───────────────────────────────────────────────────────────────
st.subheader("✦ AI Insights")
st.caption("Portfolio-level observations refreshed on every load.")
with st.container(border=True):
    with st.spinner("Generating insights..."):
        insights = insights_generator.generate_insights(flags, invoices)
    insight_list(insights)
