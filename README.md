# InvoiceGuard 🛡️

AI-powered invoice audit system for D2C Personal Care & Health Products brands.


## Run locally
```bash
pip install -r requirements.txt
# add GROQ_API_KEY and MISTRAL_API_KEY to .env
streamlit run app.py
```

## Tech stack
- **Streamlit** — UI
- **Groq** `llama-3.3-70b-versatile` — text extraction + GST audit
- **Mistral** `pixtral-12b-2409` — scanned/image invoice OCR
- **pdfplumber** — digital PDF text extraction
- **SQLite** — local storage
- **Plotly** — charts
