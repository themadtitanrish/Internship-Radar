

import os
import sqlite3
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD")
print("Email loaded:", EMAIL_ADDRESS)
print("Password length:", len(EMAIL_APP_PASSWORD) if EMAIL_APP_PASSWORD else "NOT FOUND")
DB_FILE = "jobs.db"


def ensure_notified_column(conn):
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE jobs ADD COLUMN notified INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    conn.commit()


def get_new_matches(conn, min_score=6):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, title, company, url, fit_score, fit_reason
        FROM jobs
        WHERE fit_score >= ? AND notified = 0
        ORDER BY fit_score DESC
    """, (min_score,))
    return cursor.fetchall()


def build_email_body(jobs):
    lines = ["Here are today's internship matches:\n"]
    for job_id, title, company, url, score, reason in jobs:
        lines.append(f"[{score}/10] {title} @ {company}")
        lines.append(f"Why: {reason}")
        lines.append(f"Link: {url}")
        lines.append("")  
    return "\n".join(lines)


def send_email(subject, body):
    msg["Subject"] = subject
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = EMAIL_ADDRESS

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_ADDRESS, EMAIL_APP_PASSWORD)
        server.send_message(msg)


def mark_as_notified(conn, job_ids):
    """Update the database so these jobs don't get emailed again tomorrow."""
    cursor = conn.cursor()
    for job_id in job_ids:
        cursor.execute("UPDATE jobs SET notified = 1 WHERE id = ?", (job_id,))
    conn.commit()


def main():
    if not EMAIL_ADDRESS or not EMAIL_APP_PASSWORD:
        print("EMAIL_ADDRESS or EMAIL_APP_PASSWORD missing from .env file.")
        return

    conn = sqlite3.connect(DB_FILE)
    ensure_notified_column(conn)

    jobs = get_new_matches(conn, min_score=6)

    if not jobs:
        print("No new matches to email today.")
        conn.close()
        return

    body = build_email_body(jobs)
    send_email("Internship Radar - Today's Matches", body)

    job_ids = [job[0] for job in jobs]  # job[0] is the id column
    mark_as_notified(conn, job_ids)

    print(f"Email sent with {len(jobs)} matches. Check your inbox.")
    conn.close()


if __name__ == "__main__":
    main()