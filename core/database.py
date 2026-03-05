"""SQLite database layer for InvoiceGuard."""
import json
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "invoiceguard.db"


def _get_conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables with UNIQUE constraints. DROP old tables first to fix any schema issues."""
    conn = _get_conn()
    conn.executescript("""
        DROP TABLE IF EXISTS flags;
        DROP TABLE IF EXISTS rate_cards;
        DROP TABLE IF EXISTS invoices;

        CREATE TABLE invoices (
            id   INTEGER PRIMARY KEY AUTOINCREMENT,
            filename             TEXT UNIQUE,
            vendor_name          TEXT,
            vendor_gstin         TEXT,
            invoice_number       TEXT,
            invoice_date         TEXT,
            grand_total          REAL,
            extraction_method    TEXT,
            extraction_confidence REAL,
            processed_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            raw_json             TEXT
        );

        CREATE TABLE flags (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id   INTEGER REFERENCES invoices(id),
            flag_type    TEXT,
            description  TEXT,
            billed_amount  REAL,
            correct_amount REAL,
            overcharge     REAL,
            severity       TEXT,
            status         TEXT DEFAULT 'pending',
            created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(invoice_id, flag_type, description)
        );

        CREATE TABLE rate_cards (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            vendor_name      TEXT,
            item_description TEXT,
            unit_rate        REAL,
            unit             TEXT,
            valid_from       TEXT,
            valid_until      TEXT,
            UNIQUE(vendor_name, item_description)
        );
    """)
    conn.commit()
    conn.close()


def load_demo_data():
    """Load demo data. INSERT OR IGNORE prevents duplicates."""
    conn = _get_conn()

    # Rate cards
    rate_cards = [
        ("GlowCraft Cosmetics Pvt Ltd", "Contract manufacturing per batch (skincare)", 45000.0, "batch",       "2024-01-01", "2025-12-31"),
        ("GlowCraft Cosmetics Pvt Ltd", "Stability testing per SKU",                    8000.0, "SKU",         "2024-01-01", "2025-12-31"),
        ("PurePackage Solutions",        "HDPE bottle 200ml",                              18.0, "unit",        "2024-01-01", "2025-12-31"),
        ("PurePackage Solutions",        "Airless pump bottle 50ml",                       32.0, "unit",        "2024-01-01", "2025-12-31"),
        ("NutraLabs India Pvt Ltd",      "Gummy manufacturing per batch",               55000.0, "batch",       "2024-01-01", "2025-12-31"),
        ("NutraLabs India Pvt Ltd",      "Capsule filling per 1000 units",               4500.0, "1000 units",  "2024-01-01", "2025-12-31"),
        ("SwiftShip Logistics",          "GTA freight per consignment",                  3500.0, "trip",        "2024-01-01", "2025-12-31"),
        ("SwiftShip Logistics",          "Express courier per kg",                         65.0, "kg",          "2024-01-01", "2025-12-31"),
        ("GreenLeaf Extracts Co.",       "Aloe vera extract",                            1200.0, "kg",          "2024-01-01", "2025-12-31"),
        ("GreenLeaf Extracts Co.",       "Rose essential oil",                           8500.0, "kg",          "2024-01-01", "2025-12-31"),
    ]
    for r in rate_cards:
        conn.execute(
            "INSERT OR IGNORE INTO rate_cards (vendor_name, item_description, unit_rate, unit, valid_from, valid_until) VALUES (?,?,?,?,?,?)", r
        )

    # 20 invoices
    invoices = [
        ("GlowCraft_INV-GC-2024-001_Mar2024.pdf",   "GlowCraft Cosmetics Pvt Ltd", "27AABCG1234R1Z5", "INV-GC-2024-001", "2024-03-10", 135000.0, "pdfplumber", 0.96),
        ("GlowCraft_INV-GC-2024-002_Mar2024.pdf",   "GlowCraft Cosmetics Pvt Ltd", "27AABCG1234R1Z5", "INV-GC-2024-002", "2024-03-28", 135000.0, "pdfplumber", 0.95),
        ("GlowCraft_INV-GC-2024-003_Ayurvedic.pdf", "GlowCraft Cosmetics Pvt Ltd", "27AABCG1234R1Z5", "INV-GC-2024-003", "2024-04-15",  97500.0, "pdfplumber", 0.94),
        ("GlowCraft_INV-GC-2024-004_May2024.pdf",   "GlowCraft Cosmetics Pvt Ltd", "27AABCG1234R1Z5", "INV-GC-2024-004", "2024-05-20",  96000.0, "pdfplumber", 0.97),
        ("PurePackage_PP-INV-2401_HDPE_Bottles.pdf",   "PurePackage Solutions", "29AABCP5678R1Z9", "PP/INV/2401", "2024-03-05",  54500.0, "pdfplumber", 0.97),
        ("PurePackage_PP-INV-2402_AirlessPumps.pdf",   "PurePackage Solutions", "29AABCP5678R1Z9", "PP/INV/2402", "2024-04-02",  38400.0, "pdfplumber", 0.94),
        ("PurePackage_PP-INV-2403_Labels_Cartons.pdf", "PurePackage Solutions", "29AABCP5678R1Z9", "PP/INV/2403", "2024-04-20",  65200.0, "pdfplumber", 0.96),
        ("PurePackage_PP-INV-2404_PumpBottles.pdf",    "PurePackage Solutions", "29AABCP5678R1Z9", "PP/INV/2404", "2024-05-28",  35000.0, "vision",    0.86),
        ("NutraLabs_NL-2024-0301_GummyBatch.pdf",    "NutraLabs India Pvt Ltd", "06AABCN9012R1Z3", "NL-2024-0301", "2024-03-15", 113500.0, "vision",    0.89),
        ("NutraLabs_NL-2024-0302_Capsules.pdf",      "NutraLabs India Pvt Ltd", "06AABCN9012R1Z3", "NL-2024-0302", "2024-04-10",  50000.0, "pdfplumber", 0.93),
        ("NutraLabs_NL-2024-0303_GummyBatch2.pdf",   "NutraLabs India Pvt Ltd", "06AABCN9012R1Z3", "NL-2024-0303", "2024-05-05", 126500.0, "vision",    0.88),
        ("NutraLabs_NL-2024-0304_Supplements.pdf",   "NutraLabs India Pvt Ltd", "06AABCN9012R1Z3", "NL-2024-0304", "2024-06-02",  67500.0, "pdfplumber", 0.95),
        ("SwiftShip_SS24-001_Freight_Mar.pdf", "SwiftShip Logistics", "33AABCS3456R1Z7", "SS/24/001", "2024-03-08",  18880.0, "pdfplumber", 0.92),
        ("SwiftShip_SS24-002_Courier_Mar.pdf", "SwiftShip Logistics", "33AABCS3456R1Z7", "SS/24/002", "2024-03-22",   8450.0, "vision",    0.87),
        ("SwiftShip_SS24-003_Freight_May.pdf", "SwiftShip Logistics", "33AABCS3456R1Z7", "SS/24/003", "2024-05-12",  14200.0, "pdfplumber", 0.91),
        ("SwiftShip_SS24-004_Freight_Jun.pdf", "SwiftShip Logistics", "33AABCS3456R1Z7", "SS/24/004", "2024-06-10",  23000.0, "pdfplumber", 0.92),
        ("GreenLeaf_GL-2401_AloeVera_50kg.pdf",     "GreenLeaf Extracts Co.", "24AABCG7890R1Z1", "GL-INV-2401", "2024-03-12",  60000.0, "pdfplumber", 0.95),
        ("GreenLeaf_GL-2402_RoseOil_10kg.pdf",      "GreenLeaf Extracts Co.", "24AABCG7890R1Z1", "GL-INV-2402", "2024-04-01",  85000.0, "pdfplumber", 0.97),
        ("GreenLeaf_GL-2403_AloeVera_20kg.pdf",     "GreenLeaf Extracts Co.", "24AABCG7890R1Z1", "GL-INV-2403", "2024-05-08",  27000.0, "pdfplumber", 0.93),
        ("GreenLeaf_GL-2404_EssentialOils_Jun.pdf", "GreenLeaf Extracts Co.", "24AABCG7890R1Z1", "GL-INV-2404", "2024-06-15",  45500.0, "vision",    0.88),
    ]
    for inv in invoices:
        conn.execute(
            "INSERT OR IGNORE INTO invoices (filename, vendor_name, vendor_gstin, invoice_number, invoice_date, grand_total, extraction_method, extraction_confidence, raw_json) VALUES (?,?,?,?,?,?,?,?,'{}') ",
            inv
        )
    conn.commit()

    # Fetch IDs by filename — never use hardcoded numbers
    id_map = {}
    for inv in invoices:
        row = conn.execute("SELECT id FROM invoices WHERE filename = ?", (inv[0],)).fetchone()
        if row:
            id_map[inv[0]] = row[0]

    # 14 flags — keyed by filename not hardcoded ID
    flags = [
        ("GlowCraft_INV-GC-2024-002_Mar2024.pdf",   "DUPLICATE_INVOICE",  "Possible duplicate of INV-GC-2024-001 from 2024-03-10 — same CMO, same amount ₹1,35,000",                        135000.0,    0.0, 135000.0, "critical"),
        ("SwiftShip_SS24-001_Freight_Mar.pdf",       "GST_MISMATCH",       "GTA freight (HSN 9965) billed at 18% GST; correct rate is 5% — excess tax ₹2,081",                               18880.0, 16799.0,   2081.0, "warning"),
        ("SwiftShip_SS24-003_Freight_May.pdf",       "GST_MISMATCH",       "GTA freight (HSN 9965) billed at 18% GST; correct rate is 5% — excess tax ₹1,573",                               14200.0, 12627.0,   1573.0, "warning"),
        ("GlowCraft_INV-GC-2024-003_Ayurvedic.pdf", "GST_MISMATCH",       "Ayurvedic skincare batch (HSN 3003) billed at 18% GST; correct rate is 12% — excess tax ₹4,958",                 97500.0, 92542.0,   4958.0, "warning"),
        ("GlowCraft_INV-GC-2024-004_May2024.pdf",   "RATE_EXCEEDED",      "Contract manufacturing billed at ₹48,000/batch vs contracted ₹45,000/batch (2 batches) — overcharge ₹6,000",     96000.0, 90000.0,   6000.0, "warning"),
        ("PurePackage_PP-INV-2404_PumpBottles.pdf",  "RATE_EXCEEDED",      "Airless pump bottle 50ml billed at ₹35/unit vs contracted ₹32/unit (1,000 units) — overcharge ₹3,000",           35000.0, 32000.0,   3000.0, "warning"),
        ("GreenLeaf_GL-2403_AloeVera_20kg.pdf",      "RATE_EXCEEDED",      "Aloe vera extract billed at ₹1,350/kg vs contracted ₹1,200/kg (20 kg) — overcharge ₹3,000",                      27000.0, 24000.0,   3000.0, "warning"),
        ("PurePackage_PP-INV-2401_HDPE_Bottles.pdf", "CALCULATION_ERROR",  "HDPE bottle 200ml: 3,000 × ₹18 should be ₹54,000 not ₹54,500 — arithmetic error ₹500",                          54500.0, 54000.0,    500.0, "warning"),
        ("NutraLabs_NL-2024-0301_GummyBatch.pdf",    "CALCULATION_ERROR",  "Gummy manufacturing: 2 batches × ₹55,000 = ₹1,10,000 not ₹1,13,500 — overcharged ₹3,500",                      113500.0,110000.0,   3500.0, "warning"),
        ("PurePackage_PP-INV-2403_Labels_Cartons.pdf","CALCULATION_ERROR", "Label printing: 10,000 units × ₹0.85 = ₹8,500 not ₹9,200 — billing error ₹700",                                  9200.0,  8500.0,    700.0, "warning"),
        ("NutraLabs_NL-2024-0302_Capsules.pdf",      "MYSTERY_SURCHARGE",  "Surcharge 'Artwork development charges' ₹5,000 not found in rate card or contract with NutraLabs",                5000.0,    0.0,   5000.0, "warning"),
        ("NutraLabs_NL-2024-0303_GummyBatch2.pdf",   "MYSTERY_SURCHARGE",  "Surcharge 'Formula development fee' ₹15,000 not found in contract with NutraLabs — query before payment",        15000.0,    0.0,  15000.0, "warning"),
        ("SwiftShip_SS24-004_Freight_Jun.pdf",       "MYSTERY_SURCHARGE",  "Surcharge 'Fuel surcharge' ₹2,000 not in rate card for SwiftShip Logistics",                                       2000.0,    0.0,   2000.0, "warning"),
        ("GreenLeaf_GL-2404_EssentialOils_Jun.pdf",  "MYSTERY_SURCHARGE",  "Surcharge 'Cold storage handling' ₹3,500 not in contract with GreenLeaf Extracts",                                3500.0,    0.0,   3500.0, "warning"),
    ]
    for filename, flag_type, description, billed, correct, overcharge, severity in flags:
        invoice_id = id_map.get(filename)
        if invoice_id:
            conn.execute(
                "INSERT OR IGNORE INTO flags (invoice_id, flag_type, description, billed_amount, correct_amount, overcharge, severity) VALUES (?,?,?,?,?,?,?)",
                (invoice_id, flag_type, description, billed, correct, overcharge, severity)
            )

    conn.commit()
    conn.close()


def get_all_invoices() -> list:
    conn = _get_conn()
    rows = conn.execute(
        "SELECT id, filename, vendor_name, vendor_gstin, invoice_number, invoice_date, grand_total, extraction_method, extraction_confidence, processed_at FROM invoices ORDER BY id ASC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_flags() -> list:
    conn = _get_conn()
    rows = conn.execute(
        "SELECT id, invoice_id, flag_type, description, billed_amount, correct_amount, overcharge, severity, status, created_at FROM flags ORDER BY id ASC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_flags_for_invoice(invoice_id: int) -> list:
    conn = _get_conn()
    rows = conn.execute(
        "SELECT * FROM flags WHERE invoice_id = ? ORDER BY created_at", (invoice_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_invoice_full(invoice_id: int) -> dict | None:
    conn = _get_conn()
    row = conn.execute("SELECT * FROM invoices WHERE id = ?", (invoice_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_rate_card() -> list:
    conn = _get_conn()
    rows = conn.execute(
        "SELECT vendor_name, item_description, unit_rate, unit, valid_from, valid_until FROM rate_cards"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def insert_rate_cards(rows: list) -> None:
    conn = _get_conn()
    for r in rows:
        conn.execute(
            "INSERT OR IGNORE INTO rate_cards (vendor_name, item_description, unit_rate, unit, valid_from, valid_until) VALUES (?,?,?,?,?,?)",
            (r.get("vendor_name"), r.get("item_description"), float(r.get("unit_rate", 0)),
             str(r.get("unit", "")), str(r.get("valid_from", "")), str(r.get("valid_until", "")))
        )
    conn.commit()
    conn.close()


def save_invoice(parsed: dict, flags: list, filename: str, extraction_method: str) -> int:
    conn = _get_conn()
    cur = conn.execute(
        "INSERT OR REPLACE INTO invoices (filename, vendor_name, vendor_gstin, invoice_number, invoice_date, grand_total, extraction_method, extraction_confidence, raw_json) VALUES (?,?,?,?,?,?,?,?,?)",
        (filename, parsed.get("vendor_name"), parsed.get("vendor_gstin"), parsed.get("invoice_number"),
         parsed.get("invoice_date"), parsed.get("grand_total"), extraction_method,
         parsed.get("extraction_confidence"), json.dumps(parsed))
    )
    invoice_id = cur.lastrowid
    for f in flags:
        conn.execute(
            "INSERT OR IGNORE INTO flags (invoice_id, flag_type, description, billed_amount, correct_amount, overcharge, severity) VALUES (?,?,?,?,?,?,?)",
            (invoice_id, f["flag_type"], f["description"], f["billed_amount"], f["correct_amount"], f["overcharge"], f["severity"])
        )
    conn.commit()
    conn.close()
    return invoice_id

# ── NO function calls at module level ─────────────────────────────────────────
# init_db() and load_demo_data() are called ONLY from app.py
