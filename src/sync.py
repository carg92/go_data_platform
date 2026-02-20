import os
from datetime import datetime, timezone
from notion_client import Client
from ems_parser import parse_ems

NOTION_TOKEN = os.environ["NOTION_TOKEN"]
DATABASE_ID = os.environ["NOTION_DATABASE_ID"]

# Column names in Notion (must match exactly)
COL_EMS_TEXT = "EMS"

COL_EMS_STATUS = "EMS_Status"
COL_EMS_AMOUNT = "EMS_Amount"
COL_EMS_DUE_DATE = "EMS_Due_Date"
COL_EMS_ISSUES = "EMS_Issues"
COL_PAYMENT_STATUS = "Payment_Status"
COL_LAST_SYNCED = "Last_Synced"

notion = Client(auth=NOTION_TOKEN)

def _get_rich_text(props, col_name: str) -> str:
    p = props.get(col_name)
    if not p:
        return ""
    rt = p.get("rich_text") or []
    return "".join([x.get("plain_text", "") for x in rt]).strip()

def run():
    cursor = None
    updated = 0

    while True:
        resp = notion.databases.query(
            database_id=DATABASE_ID,
            start_cursor=cursor
        ) if cursor else notion.databases.query(database_id=DATABASE_ID)

        for row in resp["results"]:
            props = row["properties"]
            ems_text = _get_rich_text(props, COL_EMS_TEXT)

            ems_status, ems_amount, ems_due_date, ems_issues = parse_ems(ems_text)

            payment_status = "Paid" if ems_status in ("PAID", "CUSTOMS_PAID") else ("Pending EMS" if ems_status == "PENDING" else "Needs Review")

            update_props = {
                COL_EMS_STATUS: {"select": {"name": ems_status}},
                COL_PAYMENT_STATUS: {"select": {"name": payment_status}},
                COL_LAST_SYNCED: {"date": {"start": datetime.now(timezone.utc).isoformat()}},
            }

            # Only set amount if we parsed one; otherwise leave as-is
            if ems_amount is not None:
                update_props[COL_EMS_AMOUNT] = {"number": ems_amount}

            if ems_due_date is not None:
                update_props[COL_EMS_DUE_DATE] = {"date": {"start": ems_due_date}}

            if ems_issues:
                update_props[COL_EMS_ISSUES] = {"rich_text": [{"text": {"content": ems_issues}}]}
            else:
                # clear issues
                update_props[COL_EMS_ISSUES] = {"rich_text": []}

            notion.pages.update(page_id=row["id"], properties=update_props)
            updated += 1

        if not resp.get("has_more"):
            break
        cursor = resp.get("next_cursor")

    print(f"Updated rows: {updated}")

if __name__ == "__main__":
    run()
