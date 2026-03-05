# InvoiceGuard 🛡️

AI-powered invoice audit system for D2C Personal Care & Health Products brands.

## Deploy to Streamlit Community Cloud (5 minutes)

### 1. Push to GitHub
```bash
git init
git add .
git commit -m "initial commit"
git remote add origin https://github.com/YOUR_USERNAME/invoiceguard.git
git push -u origin main
```

> Make sure `.env` and `data/invoiceguard.db` are listed in `.gitignore` (already done).

### 2. Create Streamlit Cloud account
Go to **[share.streamlit.io](https://share.streamlit.io)** → Sign in with GitHub.

### 3. Deploy
1. Click **"New app"**
2. Select your repository and branch (`main`)
3. Set **Main file path**: `app.py`
4. Click **"Advanced settings"** → **Secrets** — add:

```toml
GROQ_API_KEY = "your_groq_api_key_here"
MISTRAL_API_KEY = "your_mistral_api_key_here"
```

5. Click **"Deploy"**

That's it — Streamlit Cloud handles dependencies (`requirements.txt`) and system packages (`packages.txt`) automatically.

---

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

## Notes
- SQLite database resets on each Streamlit Cloud restart (demo data reloads automatically)
- For persistent storage in production, swap SQLite for Postgres (Supabase free tier recommended)
