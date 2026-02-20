import os
from datetime import datetime, timezone
from notion_client import Client
from ems_parser import parse_ems

NOTION_TOKEN = os.environ["NOTION_TOKEN"]
DATABASE_ID = os.environ["NOTION_DATABASE_ID"]

notion = Client(auth=NOTION_TOKEN)

COL_EMS_TEXT = "EMS"
COL_EMS_STATUS = "EMS_Status"
COL_EMS_AMOUNT = "EMS_Amount"
COL_EMS_DUE_DATE = "EMS_Due_Date"
COL_EMS_ISSUES = "EMS_Issues"
COL_PAYMENT_STATUS = "Payment_Status"
COL_LAST_SYNCED = "Last_Synced"

def get_text(prop):
    if prop and prop["rich_text"]:
        return "".join([t["plain_text"] for t in prop["rich_text"]])
    return ""

def run():

    response = notion.databases.query(database_id=DATABASE_ID)

    for row in response["results"]:

        props = row["properties"]

        ems_text = get_text(props[COL_EMS_TEXT])

        status, amount, due_date, issues = parse_ems(ems_text)

        payment_status = (
            "Paid" if status in ["PAID","CUSTOMS_PAID"]
            else "Pending EMS" if status == "PENDING"
            else "Needs Review"
        )

        update = {
            COL_EMS_STATUS: {"select":{"name":status}},
            COL_PAYMENT_STATUS: {"select":{"name":payment_status}},
            COL_LAST_SYNCED: {"date":{"start":datetime.now(timezone.utc).isoformat()}}
        }

        if amount is not None:
            update[COL_EMS_AMOUNT] = {"number":amount}

        if due_date:
            update[COL_EMS_DUE_DATE] = {"date":{"start":due_date}}

        if issues:
            update[COL_EMS_ISSUES] = {"rich_text":[{"text":{"content":issues}}]}
        else:
            update[COL_EMS_ISSUES] = {"rich_text":[]}

        notion.pages.update(
            page_id=row["id"],
            properties=update
        )

if __name__ == "__main__":
    run()
