"""InvoiceGuard — AI-powered invoice audit for Indian businesses."""
import streamlit as st
from core.database import init_db, load_demo_data
from core import extractor, llm_parser, validator, database, report_generator
from core.ui import inject_css

st.set_page_config(
    page_title="InvoiceGuard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.sidebar.markdown("# 🛡️ InvoiceGuard")
inject_css()

init_db()
load_demo_data()

st.title("🛡️ InvoiceGuard")
st.markdown("**AI-powered invoice audit for Indian businesses** — extract, validate, and flag overcharges, GST errors, duplicates, and mystery surcharges.")

st.markdown("")
with st.container(border=True):
    st.subheader("📤 Upload Invoices")
    files = st.file_uploader(
        "Drop invoices here — PDF, PNG, JPG, TIFF, WEBP",
        accept_multiple_files=True,
        type=["pdf", "png", "jpg", "jpeg", "tiff", "webp"],
    )

# Session state init
if "queue" not in st.session_state:
    st.session_state.queue = []
if "processing_done" not in st.session_state:
    st.session_state.processing_done = False

if files:
    existing_names = [q["filename"] for q in st.session_state.queue]
    new_files_added = False
    for f in files:
        if f.name not in existing_names:
            st.session_state.queue.append(
                {"filename": f.name, "vendor": "—", "status": "queued"}
            )
            new_files_added = True
    if new_files_added:
        st.session_state.processing_done = False

if st.session_state.queue:
    st.markdown("")
    with st.container(border=True):
        st.subheader("Processing Queue")

        # Columns: File | Vendor | Status
        header_cols = st.columns([4, 3, 2])
        for col, label in zip(header_cols, ["File", "Vendor", "Status"]):
            col.markdown(f"**{label}**")

        row_placeholders = [st.columns([4, 3, 2]) for _ in st.session_state.queue]

        def render_row(cols, item):
            status_icon = {"queued": "🔵", "processing": "🟡", "done": "🟢", "failed": "🔴", "skipped": "⚪"}
            cols[0].write(item["filename"])
            cols[1].write(item["vendor"])
            cols[2].write(f"{status_icon.get(item['status'], '')} {item['status']}")

        for i, item in enumerate(st.session_state.queue):
            render_row(row_placeholders[i], item)

        if not st.session_state.processing_done:
            if st.button("⚡ Process All", type="primary"):
                rate_card = database.get_rate_card()
                db_invoices = database.get_all_invoices()
                file_by_name = {f.name: f for f in files} if files else {}
                already_in_db = {i.get("filename") for i in db_invoices}

                for i, item in enumerate(st.session_state.queue):
                    if item["status"] == "done":
                        continue
                    st.session_state.queue[i]["status"] = "processing"
                    filename = item["filename"]

                    # Skip if already processed in a previous session
                    if filename in already_in_db:
                        st.session_state.queue[i].update({
                            "vendor": "Already in DB — skipped",
                            "status": "skipped",
                        })
                        continue

                    file = file_by_name.get(filename)
                    if not file:
                        st.session_state.queue[i]["status"] = "failed"
                        st.session_state.queue[i]["vendor"] = "File not found"
                        continue
                    try:
                        extracted = extractor.extract(file)
                        parsed, _ = llm_parser.parse_invoice(extracted)
                        flags = validator.run_all_checks(parsed, rate_card, db_invoices)
                        invoice_id = database.save_invoice(
                            parsed, flags, filename, extracted["method"]
                        )
                        db_invoices.append({
                            "id": invoice_id,
                            "vendor_name": parsed.get("vendor_name"),
                            "invoice_number": parsed.get("invoice_number"),
                            "invoice_date": parsed.get("invoice_date"),
                            "grand_total": parsed.get("grand_total"),
                        })
                        st.session_state.queue[i].update({
                            "vendor": parsed.get("vendor_name") or "Unknown",
                            "status": "done",
                        })
                    except Exception as e:
                        st.session_state.queue[i]["status"] = "failed"
                        st.session_state.queue[i]["vendor"] = str(e)[:50]

                st.session_state.processing_done = True
                st.rerun()

    # ── Post-processing actions ────────────────────────────────────────────────
    if st.session_state.processing_done:
        done = [q for q in st.session_state.queue if q["status"] == "done"]
        failed = [q for q in st.session_state.queue if q["status"] == "failed"]

        if done:
            st.success(f"✅ {len(done)} invoice{'s' if len(done) > 1 else ''} processed successfully.")
        if failed:
            st.warning(f"⚠️ {len(failed)} invoice{'s' if len(failed) > 1 else ''} failed to process.")

        col_report, col_dl = st.columns([1, 2])
        with col_report:
            if st.button("📋 View Audit Report", type="primary", use_container_width=True):
                st.switch_page("pages/2_Audit_Report.py")
        with col_dl:
            report_bytes = report_generator.generate(
                database.get_all_invoices(), database.get_all_flags()
            )
            st.download_button(
                "📥 Download Excel Report",
                report_bytes,
                "audit_report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
