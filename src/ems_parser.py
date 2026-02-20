import re
from datetime import datetime

def parse_ems(text: str):
    if not text:
        return "UNKNOWN", None, None, "Empty EMS"

    raw = text.upper()

    status = "UNKNOWN"
    if "PENDIENTE" in raw:
        status = "PENDING"
    elif "CRUCE" in raw and "PAGADO" in raw:
        status = "CUSTOMS_PAID"
    elif "PAGADO" in raw:
        status = "PAID"

    # Amount: first numeric after optional $
    amount_match = re.search(r"\$?\s*(\d+(?:\.\d{1,2})?)", raw)
    amount = float(amount_match.group(1)) if amount_match else None

    # Due date: dd/mm/yyyy (take first occurrence)
    due_date_iso = None
    date_match = re.search(r"(\d{2}/\d{2}/\d{4})", raw)
    if date_match:
        try:
            due_date_iso = datetime.strptime(date_match.group(1), "%d/%m/%Y").date().isoformat()
        except:
            pass

    issues = None
    if status == "UNKNOWN":
        issues = "Unrecognized EMS format"
    if status == "PAID" and amount is None:
        issues = "Paid without amount (verify)"
    if status == "PENDING" and due_date_iso is None:
        # not an error, but useful
        issues = issues or "Pending without due date"

    return status, amount, due_date_iso, issues
