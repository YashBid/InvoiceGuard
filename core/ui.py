"""InvoiceGuard — shared UI helpers.

CSS strategy: ONLY targets our custom .ig-* classes +
a minimal set of safe Streamlit overrides (sidebar bg, nav link,
container border, button hover). No global font overrides.
"""
import streamlit as st

_CSS = """
/* ═══ SIDEBAR ═══════════════════════════════════════════════════════════ */
[data-testid="stSidebar"] {
  background-color: #0d1117 !important;
  border-right: 1px solid #21262d !important;
}
[data-testid="stSidebar"] h1 {
  padding-bottom: 12px !important;
  margin-bottom: 0 !important;
}
[data-testid="stSidebarNavLink"][aria-selected="true"] {
  background: rgba(240,180,41,0.1) !important;
  color: #f0b429 !important;
  border-left: 3px solid #f0b429 !important;
}


/* ═══ CONTAINERS ════════════════════════════════════════════════════════ */
[data-testid="stVerticalBlockBorderWrapper"] {
  border-color: #21262d !important;
  border-radius: 14px !important;
  transition: border-color 0.2s !important;
}
[data-testid="stVerticalBlockBorderWrapper"]:hover {
  border-color: rgba(240,180,41,0.3) !important;
}

/* ═══ BUTTONS ═══════════════════════════════════════════════════════════ */
.stButton > button[kind="primary"]:hover {
  box-shadow: 0 4px 20px rgba(240,180,41,0.35) !important;
  transform: translateY(-1px) !important;
  transition: all 0.15s !important;
}
.stDownloadButton > button:hover {
  border-color: #f0b429 !important;
  color: #f0b429 !important;
  transition: all 0.15s !important;
}

/* ═══ FILE UPLOADER ══════════════════════════════════════════════════════ */
[data-testid="stFileUploaderDropzone"] {
  border-radius: 12px !important;
  border: 1.5px dashed #30363d !important;
  transition: border-color 0.2s !important;
}
[data-testid="stFileUploaderDropzone"]:hover {
  border-color: rgba(240,180,41,0.5) !important;
}

/* ═══ DATAFRAMES ═════════════════════════════════════════════════════════ */
[data-testid="stDataFrame"] {
  border: 1px solid #21262d !important;
  border-radius: 10px !important;
  overflow: hidden !important;
}

/* ═══ ALERTS ═════════════════════════════════════════════════════════════ */
[data-testid="stAlert"] {
  border-radius: 10px !important;
  border-left-width: 4px !important;
}

/* ═══ CUSTOM METRIC CARDS ════════════════════════════════════════════════ */
.ig-metrics {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 14px;
  margin-bottom: 6px;
}
.ig-card {
  position: relative;
  background: linear-gradient(135deg, #161b22 0%, #0d1117 100%);
  border: 1px solid #21262d;
  border-radius: 14px;
  padding: 22px 24px 18px;
  overflow: hidden;
  transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
  cursor: default;
}
.ig-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 32px rgba(0,0,0,0.4);
}
.ig-card::before {
  content: '';
  position: absolute;
  top: -40px; right: -40px;
  width: 120px; height: 120px;
  border-radius: 50%;
  opacity: 0.06;
  filter: blur(20px);
}
.ig-card.y { border-left: 3px solid #f0b429; }
.ig-card.y::before { background: #f0b429; }
.ig-card.y:hover { border-color: rgba(240,180,41,0.5); }
.ig-card.r { border-left: 3px solid #e85d4a; }
.ig-card.r::before { background: #e85d4a; }
.ig-card.r:hover { border-color: rgba(232,93,74,0.5); }
.ig-card.g { border-left: 3px solid #3ecf8e; }
.ig-card.g::before { background: #3ecf8e; }
.ig-card.g:hover { border-color: rgba(62,207,142,0.5); }

.ig-label {
  font-size: 10.5px;
  font-weight: 600;
  letter-spacing: 0.8px;
  text-transform: uppercase;
  color: #6e7681;
  margin-bottom: 10px;
}
.ig-val {
  font-size: 28px;
  font-weight: 700;
  letter-spacing: -0.5px;
  line-height: 1.1;
}
.ig-card.y .ig-val { color: #f0b429; }
.ig-card.r .ig-val { color: #e85d4a; }
.ig-card.g .ig-val { color: #3ecf8e; }

/* ═══ INSIGHT PILLS ══════════════════════════════════════════════════════ */
.ig-insights {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 4px 0;
}
.ig-insight {
  display: flex;
  gap: 10px;
  align-items: flex-start;
  padding: 10px 14px;
  background: rgba(255,255,255,0.03);
  border: 1px solid #21262d;
  border-radius: 8px;
  font-size: 13.5px;
  line-height: 1.55;
  color: #c9d1d9;
  transition: border-color 0.15s, background 0.15s;
}
.ig-insight:hover {
  border-color: rgba(240,180,41,0.25);
  background: rgba(240,180,41,0.03);
}
.ig-bullet {
  flex-shrink: 0;
  margin-top: 2px;
  width: 6px; height: 6px;
  border-radius: 50%;
  background: #f0b429;
  opacity: 0.7;
}

/* ═══ FLAG CHIPS (inline badge) ══════════════════════════════════════════ */
.ig-chip {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.2px;
}
.ig-chip-y { background: rgba(240,180,41,0.12); color: #f0b429; }
.ig-chip-r { background: rgba(232,93,74,0.12);  color: #e85d4a; }
.ig-chip-g { background: rgba(62,207,142,0.12); color: #3ecf8e; }
.ig-chip-b { background: rgba(79,148,239,0.12); color: #4f94ef; }
.ig-chip-p { background: rgba(180,79,239,0.12); color: #b44fef; }
"""


def inject_css() -> None:
    st.markdown(f"<style>{_CSS}</style>", unsafe_allow_html=True)


def metric_cards(cards: list[dict]) -> None:
    """Premium metric card row.
    cards: [{"label": str, "value": str, "color": "y"|"r"|"g"}]
    """
    inner = "".join(
        f'<div class="ig-card {c["color"]}">'
        f'<div class="ig-label">{c["label"]}</div>'
        f'<div class="ig-val">{c["value"]}</div>'
        f'</div>'
        for c in cards
    )
    st.markdown(f'<div class="ig-metrics">{inner}</div>', unsafe_allow_html=True)


def insight_list(points: list[str]) -> None:
    """Render insight bullet points as styled cards."""
    items = ""
    for p in points:
        text = p.lstrip("•–- ").strip()
        if text:
            items += (
                f'<div class="ig-insight">'
                f'<div class="ig-bullet"></div>'
                f'<span>{text}</span>'
                f'</div>'
            )
    st.markdown(f'<div class="ig-insights">{items}</div>', unsafe_allow_html=True)
