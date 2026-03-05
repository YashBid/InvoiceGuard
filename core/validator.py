"""Run all validation checks; GST validation comes from Gemini extraction."""
from fuzzywuzzy import fuzz


def run_all_checks(parsed: dict, rate_card: list, db_invoices: list) -> list[dict]:
    flags = []
    flags += check_duplicates(parsed, db_invoices)
    flags += check_rate_card(parsed, rate_card)
    flags += check_calculation_errors(parsed)
    flags += check_mystery_surcharges(parsed, rate_card)
    flags += check_gst_from_extraction(parsed)
    return flags


def check_gst_from_extraction(parsed: dict) -> list:
    flags = []
    for item in parsed.get("line_items", []):
        if item.get("gst_correct") is False:
            billed_rate = (
                (item.get("cgst_rate") or 0)
                + (item.get("sgst_rate") or 0)
                + (item.get("igst_rate") or 0)
            )
            expected_rate = item.get("gst_expected_rate") or 0
            overcharge = item["amount"] * (billed_rate - expected_rate) / 100
            flags.append({
                "flag_type": "GST_MISMATCH",
                "description": item.get("gst_note") or f"GST mismatch on {item.get('description', 'item')}",
                "billed_amount": item["amount"] * (1 + billed_rate / 100),
                "correct_amount": item["amount"] * (1 + expected_rate / 100),
                "overcharge": overcharge,
                "severity": "warning",
            })
    return flags


def check_duplicates(parsed: dict, db_invoices: list) -> list:
    flags = []
    vendor_name = (parsed.get("vendor_name") or "").lower()
    invoice_number = parsed.get("invoice_number") or ""
    grand_total = parsed.get("grand_total") or 0

    for existing in db_invoices:
        existing_vendor = (existing.get("vendor_name") or "").lower()
        vendor_match = fuzz.ratio(vendor_name, existing_vendor)
        same_invoice_no = invoice_number == (existing.get("invoice_number") or "")
        same_amount = abs(grand_total - (existing.get("grand_total") or 0)) < 1

        if vendor_match > 85 and (same_invoice_no or same_amount):
            flags.append({
                "flag_type": "DUPLICATE_INVOICE",
                "description": f"Possible duplicate of invoice {existing.get('invoice_number')} from {existing.get('invoice_date', '')}",
                "billed_amount": grand_total,
                "correct_amount": 0,
                "overcharge": grand_total,
                "severity": "critical",
            })
    return flags


def check_rate_card(parsed: dict, rate_card: list) -> list:
    flags = []
    for item in parsed.get("line_items", []):
        desc = (item.get("description") or "").lower()
        unit_rate = item.get("unit_rate") or 0
        quantity = item.get("quantity") or 0
        for rc in rate_card:
            rc_desc = (rc.get("item_description") or "").lower()
            if fuzz.partial_ratio(desc, rc_desc) > 80:
                rc_rate = rc.get("unit_rate") or 0
                if unit_rate > rc_rate * 1.02:
                    overcharge = (unit_rate - rc_rate) * quantity
                    flags.append({
                        "flag_type": "RATE_EXCEEDED",
                        "description": f"{item.get('description')} billed at ₹{unit_rate} vs contracted ₹{rc_rate}",
                        "billed_amount": unit_rate * quantity,
                        "correct_amount": rc_rate * quantity,
                        "overcharge": overcharge,
                        "severity": "warning",
                    })
                break
    return flags


def check_calculation_errors(parsed: dict) -> list:
    flags = []
    for item in parsed.get("line_items", []):
        qty = item.get("quantity") or 0
        rate = item.get("unit_rate") or 0
        amount = item.get("amount") or 0
        expected = round(qty * rate, 2)
        actual = round(amount, 2)
        if abs(expected - actual) > 1:
            flags.append({
                "flag_type": "CALCULATION_ERROR",
                "description": f"{item.get('description')}: {qty} × ₹{rate} should be ₹{expected} not ₹{actual}",
                "billed_amount": actual,
                "correct_amount": expected,
                "overcharge": actual - expected,
                "severity": "warning",
            })
    return flags


def check_mystery_surcharges(parsed: dict, rate_card: list) -> list:
    flags = []
    rc_descriptions = [(r.get("item_description") or "").lower() for r in rate_card]
    for surcharge in parsed.get("surcharges", []):
        name = (surcharge.get("name") or "").lower()
        amount = surcharge.get("amount") or 0
        matched = any(fuzz.partial_ratio(name, rc) > 80 for rc in rc_descriptions)
        if not matched:
            flags.append({
                "flag_type": "MYSTERY_SURCHARGE",
                "description": f"Surcharge '{surcharge.get('name')}' not found in contract or rate card",
                "billed_amount": amount,
                "correct_amount": 0,
                "overcharge": amount,
                "severity": "warning",
            })
    return flags
