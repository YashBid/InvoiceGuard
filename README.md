<div align="center">
  <h1>🛡️ InvoiceGuard</h1>
  <p><strong>AI-powered invoice audit system for D2C Personal Care & Health Products brands.</strong></p>

  <p>
    <a href="https://streamlit.io/"><img src="https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white" alt="Streamlit"/></a>
    <a href="https://groq.com/"><img src="https://img.shields.io/badge/Groq-f55036?style=for-the-badge&logo=groq&logoColor=white" alt="Groq"/></a>
    <a href="https://mistral.ai/"><img src="https://img.shields.io/badge/Mistral-F54D27?style=for-the-badge&logo=mistral&logoColor=white" alt="Mistral"/></a>
    <a href="https://www.sqlite.org/"><img src="https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white" alt="SQLite"/></a>
  </p>
</div>

<br/>

## 🎯 What is InvoiceGuard?

**InvoiceGuard** is an AI-powered invoice audit tool specifically tailored for Indian businesses. It automates the tedious process of extracting, validating, and flagging discrepancies in invoices. 

Whether it's overcharges, GST calculation errors, duplicate submissions, or mystery surcharges, InvoiceGuard catches them all.

### ✨ Key Features
- **Intelligent Extraction:** Uses advanced LLMs to extract data from digital PDFs, PNGs, JPGs, TIFFs, and WEBPs.
- **GST & Rate Auditing:** Automatically cross-checks extracted invoice details against predefined rate cards and GST rules.
- **Robust Flagging:** Instantly identifies duplicates, calculation mismatches, and overcharges.
- **Export & Reporting:** Generate comprehensive Excel audit reports with a single click.




## 🚀 Quick Start (Local Development)

Run InvoiceGuard locally in just a few steps!

### 1. Prerequisites
Ensure you have Python 3.8+ installed. You will also need API keys from:
- [Groq](https://console.groq.com/keys)
- [Mistral AI](https://console.mistral.ai/api-keys/)

### 2. Setup
Clone the repository and install the dependencies:
```bash
git clone https://github.com/YOUR_USERNAME/invoiceguard.git
cd invoiceguard
pip install -r requirements.txt
```

### 3. Environment Variables
Create a `.env` file in the root directory and add your API keys:
```env
GROQ_API_KEY="your_groq_api_key_here"
MISTRAL_API_KEY="your_mistral_api_key_here"
```

### 4. Run the App
Launch the Streamlit server:
```bash
streamlit run app.py
```


## 🛠️ Tech Stack

- **Frontend:** [Streamlit](https://streamlit.io/)
- **Text Extraction & Auditing:** [Groq](https://groq.com/) 
- **OCR (Images/Scans):** [Mistral AI](https://mistral.ai/) 
- **PDF Parsing:** `pdfplumber`
- **Database:** SQLite
- **Data Visualization:** Plotly


---

<div align="center">
  <i>Built with ❤️ for Indian Businesses.</i>
</div>
