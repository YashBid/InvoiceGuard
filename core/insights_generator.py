"""Generate overall portfolio-level insights from all invoices using Groq."""
import os
from dotenv import load_dotenv

load_dotenv()

def _get_secret(key: str):
    val = os.getenv(key)
    if val:
        return val
    try:
        import streamlit as st
        return st.secrets.get(key)
    except Exception:
        return None

_GROQ_KEY = _get_secret("GROQ_API_KEY")


def generate_insights(flags: list, invoices: list) -> list[str]:
    """
    Generate 6-8 bullet-point insights summarising ALL processed invoices.
    Returned list items each start with •
    """
    if not flags and not invoices:
        return ["• No invoices processed yet — upload invoices to see insights."]

    # Build compact summary for the LLM
    total_overcharge = sum(f.get("overcharge", 0) for f in flags)
    flag_counts: dict = {}
    for f in flags:
        t = f.get("flag_type", "UNKNOWN")
        flag_counts[t] = flag_counts.get(t, 0) + 1

    vendor_overcharges: dict = {}
    vendor_flag_counts: dict = {}
    for f in flags:
        inv = next((i for i in invoices if i.get("id") == f.get("invoice_id")), None)
        if inv:
            v = inv.get("vendor_name", "Unknown")
            vendor_overcharges[v] = vendor_overcharges.get(v, 0) + f.get("overcharge", 0)
            vendor_flag_counts[v] = vendor_flag_counts.get(v, 0) + 1

    top_vendor = max(vendor_overcharges, key=vendor_overcharges.get) if vendor_overcharges else "N/A"
    top_vendor_amount = vendor_overcharges.get(top_vendor, 0)

    summary = f"""
Total invoices processed: {len(invoices)}
Total flags raised: {len(flags)}
Total overcharge exposure: ₹{total_overcharge:,.0f}
Flag type breakdown: {flag_counts}
Overcharge by vendor: {vendor_overcharges}
Vendor with most flags: {max(vendor_flag_counts, key=vendor_flag_counts.get) if vendor_flag_counts else 'N/A'} ({max(vendor_flag_counts.values()) if vendor_flag_counts else 0} flags)
Highest-risk vendor by ₹ exposure: {top_vendor} (₹{top_vendor_amount:,.0f})
"""

    if not _GROQ_KEY:
        # Fallback: compute without LLM
        bullets = [
            f"• {len(invoices)} invoices processed across {len(vendor_overcharges)} vendors.",
            f"• {len(flags)} total flags raised — ₹{total_overcharge:,.0f} in overcharges identified.",
        ]
        if flag_counts:
            top_type = max(flag_counts, key=flag_counts.get)
            bullets.append(f"• Most common issue: {top_type.replace('_', ' ').title()} ({flag_counts[top_type]} occurrences).")
        if top_vendor != "N/A":
            bullets.append(f"• Highest-risk vendor: {top_vendor} — ₹{top_vendor_amount:,.0f} in overcharges.")
        bullets.append("• Set GROQ_API_KEY in .env to enable AI-generated insights.")
        return bullets

    from groq import Groq
    client = Groq(api_key=_GROQ_KEY)

    prompt = f"""You are a senior finance controller for a D2C personal care and health products brand
(skincare, haircare, health supplements, gummies, nutraceuticals).
You are reviewing the invoice audit dashboard for this business.

Write 6 to 8 concise bullet points that explain what the dashboard shows and what actions the finance team should take.
Focus on patterns specific to this industry:
- GST errors on personal care products (skincare/haircare HSN 3304/3305 should be 18%;
  Ayurvedic HSN 3003/3004 should be 12%; GTA freight HSN 9965 should be 5%)
- Contract manufacturer (CMO) or toll manufacturer overcharges or duplicate billings
- Packaging material price inflation (bottles, jars, labels, cartons)
- Mystery surcharges common in this industry (development fees, formula charges,
  stability testing fees, artwork charges, tooling charges)
- Freight GST errors (5% for GTA, not 18%)
- Highest-risk vendors by ₹ exposure
- One clear priority action with estimated recovery amount

Include specific ₹ figures wherever available.
Return ONLY bullet points, each starting with •. No headers, no bold, no markdown.

Data:
{summary}"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=512,
        )
        raw = response.choices[0].message.content.strip()
        bullets = [line.strip() for line in raw.split("\n") if line.strip().startswith("•")]
        return bullets if bullets else ["• Unable to generate insights for the current dataset."]
    except Exception as e:
        return [f"• Groq insight generation failed: {str(e)[:80]}"]
