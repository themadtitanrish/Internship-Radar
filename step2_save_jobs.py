import sqlite3
import requests

URL = "https://www.arbeitnow.com/api/job-board-api"
DB_FILE = "jobs.db"


def fetch_jobs():
    response = requests.get(URL)

    if response.status_code != 200:
        print(f"Something went wrong. Status code: {response.status_code}")
        return []

    data = response.json()
    return data["data"]


def filter_internships(jobs):
    internships = []
    for job in jobs:
        title = job.get("title", "")
        tags = job.get("tags", [])
        title_has_intern = "intern" in title.lower()
        tags_have_intern = any("intern" in tag.lower() for tag in tags)
        if title_has_intern or tags_have_intern:
            internships.append(job)
    return internships


def setup_database():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            company TEXT,
            location TEXT,
            url TEXT UNIQUE
        )
    """)

    conn.commit()

    return conn


def save_jobs(conn, jobs):
    """Insert jobs into the database, skipping duplicates."""
    cursor = conn.cursor()
    new_count = 0
    skipped_count = 0

    for job in jobs:
        title = job.get("title")
        company = job.get("company_name")
        location = job.get("location")
        url = job.get("url")

        try:
            cursor.execute(
                "INSERT INTO jobs (title, company, location, url) VALUES (?, ?, ?, ?)",
                (title, company, location, url)
            )
            new_count += 1
        except sqlite3.IntegrityError:
            skipped_count += 1

    conn.commit()
    return new_count, skipped_count


def main():
    print("Fetching jobs from Arbeitnow API...\n")
    jobs = fetch_jobs()
    print(f"Total jobs pulled: {len(jobs)}")

    internships = filter_internships(jobs)
    print(f"Internship-looking listings found: {len(internships)}\n")

    conn = setup_database()
    new_count, skipped_count = save_jobs(conn, internships)

    print(f"New listings saved: {new_count}")
    print(f"Already had (skipped): {skipped_count}")

    # Quick sanity check: show everything currently in the database
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM jobs")
    total_in_db = cursor.fetchone()[0]
    print(f"\nTotal internships saved in database so far: {total_in_db}")

    conn.close()


if __name__ == "__main__":
    main()
