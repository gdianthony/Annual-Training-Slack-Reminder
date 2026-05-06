import csv
import os
from datetime import date, datetime
import requests

CSV_PATH = "training_due.csv"
LOG_PATH = "sent_log.csv"
REMINDER_DAYS = {30, 14, 7}

SLACK_WEBHOOK_URL = os.environ["SLACK_WEBHOOK_URL"]


def already_sent(first_name, last_name, due_date, days_until_due):
    try:
        with open(LOG_PATH, "r", newline="") as file:
            reader = csv.DictReader(file)
            for row in reader:
                if (
                    row["first_name"] == first_name
                    and row["last_name"] == last_name
                    and row["training_duedate"] == due_date
                    and int(row["days_until_due"]) == days_until_due
                ):
                    return True
    except FileNotFoundError:
        return False

    return False


def log_sent(first_name, last_name, due_date, days_until_due):
    file_exists = os.path.exists(LOG_PATH)

    with open(LOG_PATH, "a", newline="") as file:
        fieldnames = [
            "sent_date",
            "first_name",
            "last_name",
            "training_duedate",
            "days_until_due",
        ]

        writer = csv.DictWriter(file, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        writer.writerow({
            "sent_date": date.today().isoformat(),
            "first_name": first_name,
            "last_name": last_name,
            "training_duedate": due_date,
            "days_until_due": days_until_due,
        })


def send_slack_message(first_name, last_name, due_date, days_until_due):
    message = (
        f"⚠️ *Annual Training Reminder*\n\n"
        f"{first_name} {last_name}'s annual training is due in "
        f"*{days_until_due} days* on *{due_date}*.\n\n"
        f"Reminder needed today."
    )

    response = requests.post(
        SLACK_WEBHOOK_URL,
        json={"text": message},
        timeout=10,
    )

    response.raise_for_status()


def main():
    today = date.today()

    with open(CSV_PATH, "r", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            first_name = row["first_name"].strip()
            last_name = row["last_name"].strip()
            due_date_text = row["training_duedate"].strip()

            due_date = datetime.strptime(due_date_text, "%Y-%m-%d").date()
            days_until_due = (due_date - today).days

            if days_until_due in REMINDER_DAYS:
                if already_sent(first_name, last_name, due_date_text, days_until_due):
                    continue

                send_slack_message(
                    first_name,
                    last_name,
                    due_date_text,
                    days_until_due,
                )

                log_sent(
                    first_name,
                    last_name,
                    due_date_text,
                    days_until_due,
                )


if __name__ == "__main__":
    main()
