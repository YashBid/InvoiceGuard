"""Parse invoice using Groq (text) or Mistral Pixtral (image).
Domain: D2C brand — Personal Care & Health Products (skincare, haircare, supplements, gummies).
Returns (invoice_data: dict, insights: list[str]) — one API call per invoice.
"""
import os
import io
import json
import re
import base64
from dotenv import load_dotenv

load_dotenv()

def _get_secret(key: str) -> str | None:
    """Load from env first (local .env), then Streamlit secrets (cloud)."""
    val = os.getenv(key)
    if val:
        return val
    try:
        import streamlit as st
        return st.secrets.get(key)
    except Exception:
        return None

_GROQ_KEY    = _get_secret("GROQ_API_KEY")
_MISTRAL_KEY = _get_secret("MISTRAL_API_KEY")

_COMBINED_PROMPT = """You are an expert Indian invoice parser and GST auditor specialising in
D2C Personal Care & Health Products businesses (skincare, haircare, health supplements,
gummies, nutraceuticals, Ayurvedic products).

Extract all invoice fields AND generate audit insights in one response.
Return ONLY this JSON, no markdown, no explanation:

{
  "invoice_data": {
    "vendor_name": "str",
    "vendor_gstin": "str or null",
    "invoice_number": "str",
    "invoice_date": "YYYY-MM-DD or null",
    "line_items": [
      {
        "description": "str",
        "hsn_code": "str or null",
        "quantity": 0.0,
        "unit": "str",
        "unit_rate": 0.0,
        "amount": 0.0,
        "cgst_rate": 0.0,
        "sgst_rate": 0.0,
        "igst_rate": 0.0,
        "tax_amount": 0.0,
        "gst_correct": true,
        "gst_expected_rate": 0.0,
        "gst_note": "str or null"
      }
    ],
    "subtotal": 0.0,
    "total_tax": 0.0,
    "grand_total": 0.0,
    "surcharges": [{"name": "str", "amount": 0.0}],
    "extraction_confidence": 1.0
  },
  "insights": ["• insight 1", "• insight 2"]
}

=== GST RATE REFERENCE FOR THIS DOMAIN ===
Use this to set gst_correct and gst_expected_rate per line item:

PERSONAL CARE & COSMETICS (18% GST):
  HSN 3303 – Perfumes, eau de cologne
  HSN 3304 – Skincare: creams, serums, lotions, face wash, sunscreen, moisturiser
  HSN 3305 – Haircare: shampoo, conditioner, hair oil, hair mask, hair serum
  HSN 3306 – Oral care: toothpaste, mouthwash
  HSN 3307 – Deodorants, antiperspirants, shaving products
  HSN 3401 – Soaps: bathing bars, liquid body wash, handwash
  HSN 3301 – Essential oils (lavender, tea tree, rosemary etc.)
  HSN 1302 – Plant extracts: aloe vera, neem, turmeric extract → 12% GST

HEALTH SUPPLEMENTS & NUTRITION (check carefully):
  HSN 2106 – Health supplements, nutraceuticals, protein powders, gummies → 18% GST
  HSN 2936 – Vitamins & provitamins (bulk raw material) → 12% GST
  HSN 2101 – Coffee/tea-based health drinks → 18% GST
  HSN 1704 – Sugar confectionery incl. gummies (if classified as candy) → 18% GST
  HSN 2106 – Protein bars, nutrition bars → 18% GST
  HSN 3003 – Ayurvedic medicines (multi-ingredient, not patented) → 12% GST
  HSN 3004 – Ayurvedic proprietary medicines (patented/branded) → 12% GST
  HSN 0407 – Eggs (raw material) → 0% GST
  HSN 0401 – Milk / milk powder (raw material) → 0% GST
  HSN 1901 – Malt extracts, food preparations for infant use → 18% GST

PACKAGING MATERIALS:
  HSN 3923 – Plastic primary packaging: bottles, jars, tubes, pumps, caps → 18% GST
  HSN 7612 – Aluminium packaging containers, tubes → 18% GST
  HSN 4819 – Paper/cardboard cartons, boxes (secondary packaging) → 12% GST
  HSN 4821 – Paper labels, sticker labels → 12% GST
  HSN 3920 – Plastic sheets, shrink wrap → 18% GST

MANUFACTURING & SERVICES:
  HSN 9988 – Contract manufacturing / toll manufacturing / job work → 18% GST
  HSN 9983 – Marketing, advertising, digital marketing, lab testing services → 18% GST
  HSN 9965 – Freight/GTA (Goods Transport Agency) → 5% GST (NOT 18%)
  HSN 9992 – Education/training services → 18% GST
  HSN 8422 – Packaging machines (capital equipment) → 18% GST

RAW MATERIALS (common in personal care manufacturing):
  Glycerine (HSN 2905) → 18% GST
  Cetyl alcohol, stearic acid (HSN 2905) → 18% GST
  Sodium lauryl sulphate / SLES (HSN 3402) → 18% GST
  Carbomer, xanthan gum (HSN 3913/1301) → 18% GST
  Titanium dioxide (HSN 3206) → 18% GST

=== RULES ===
- Never hallucinate. Set null if a field is not visible.
- All amounts in INR as float.
- For each line item: verify the GST rate against the reference above.
  Set gst_correct to false if billed rate differs from expected.
  Set gst_expected_rate to the correct rate.
  Set gst_note explaining the mismatch (e.g. "GTA freight must be 5% not 18%", "Ayurvedic product should be 12% not 18%").
- extraction_confidence: 1.0 if clear, lower if blurry or partial.
- insights: 4–6 bullet points, finance-actionable for a D2C personal care brand.
  Focus on: GST errors on personal care items, contract manufacturer billing anomalies,
  packaging cost overruns, mystery surcharges (development fees, formula charges, stability testing),
  freight GST errors, duplicates, and one recommended recovery action with ₹ amount.
  Each bullet must start with •"""


def _clean_json(text: str) -> str:
    text = re.sub(r"^```(?:json)?\s*", "", text.strip())
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def _unpack(raw_response: str) -> tuple[dict, list[str]]:
    data = json.loads(_clean_json(raw_response))
    invoice_data = data.get("invoice_data", data)
    insights_raw = data.get("insights", [])
    insights = [b.strip() for b in insights_raw if str(b).strip()]
    if not insights:
        insights = ["• No specific insights generated for this invoice."]
    return invoice_data, insights


def parse_invoice(extracted: dict) -> tuple[dict, list[str]]:
    """
    Parse an invoice dict from extractor.py.
    Returns (invoice_data, insights).
    """
    if extracted["type"] == "text":
        return _parse_text(extracted["content"])
    else:
        return _parse_image(extracted["content"])


def _parse_text(text: str) -> tuple[dict, list[str]]:
    """Groq llama-3.3-70b-versatile for digital PDF text."""
    if not _GROQ_KEY:
        raise ValueError(
            "GROQ_API_KEY not set. Add it to your .env file. "
            "Get a free key at https://console.groq.com"
        )
    from groq import Groq
    client = Groq(api_key=_GROQ_KEY)
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "user",
                "content": _COMBINED_PROMPT + "\n\nInvoice text:\n" + text,
            }
        ],
        temperature=0.1,
        max_tokens=4096,
    )
    raw = response.choices[0].message.content
    return _unpack(raw)


def _parse_image(image) -> tuple[dict, list[str]]:
    """Mistral pixtral-12b-2409 for scanned PDF pages and image files."""
    if not _MISTRAL_KEY:
        raise ValueError(
            "MISTRAL_API_KEY not set. Add it to your .env file. "
            "Get a key at https://console.mistral.ai"
        )
    from mistralai import Mistral

    buf = io.BytesIO()
    image.save(buf, format="JPEG", quality=90)
    b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

    client = Mistral(api_key=_MISTRAL_KEY)
    response = client.chat.complete(
        model="pixtral-12b-2409",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": _COMBINED_PROMPT},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{b64}"},
                    },
                ],
            }
        ],
        temperature=0.1,
        max_tokens=4096,
    )
    raw = response.choices[0].message.content
    return _unpack(raw)
