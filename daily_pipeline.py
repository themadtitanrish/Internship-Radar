
import os
import time
import sqlite3
import requests
from dotenv import load_dotenv


MAX_AGE_SECONDS = 24 * 60 * 60


def is_recent(posted_timestamp):
    if posted_timestamp is None:
        return False

    now = time.time()
    age_seconds = now - posted_timestamp
    return age_seconds <= MAX_AGE_SECONDS


load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
DB_FILE = "jobs.db"

def load_skills():
    with open("skills.txt", "r") as f:
        return f.read().strip()


MY_SKILLS = load_skills()



def fetch_arbeitnow():
    url = "https://www.arbeitnow.com/api/job-board-api"
    response = requests.get(url)
    if response.status_code != 200:
        return []

    jobs = response.json()["data"]
    results = []
    for job in jobs:
        title = job.get("title", "")
        tags = job.get("tags", [])

        
        posted_timestamp = job.get("created_at")

        matches_intern = "intern" in title.lower() or any("intern" in t.lower() for t in tags)

        if matches_intern and is_recent(posted_timestamp):
            results.append({
                "title": title,
                "company": job.get("company_name"),
                "location": job.get("location"),
                "url": job.get("url"),
                "description": job.get("description", "")[:500]  # trim long text
            })
    return results


def fetch_remoteok():
    url = "https://remoteok.com/api"
    headers = {"User-Agent": "Mozilla/5.0"}  # RemoteOK blocks requests with no browser-like header
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"RemoteOK error: {response.status_code}")
        return []

    jobs = response.json()

    results = []
    for job in jobs:
        title = job.get("position", "")
        tags = job.get("tags", [])

        
        posted_timestamp = job.get("epoch")

        matches_intern = "intern" in title.lower() or any("intern" in str(t).lower() for t in tags)

        if matches_intern and is_recent(posted_timestamp):
            results.append({
                "title": title,
                "company": job.get("company"),
                "location": job.get("location", "Remote"),
                "url": job.get("url"),
                "description": job.get("description", "")[:500]
            })
    return results



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
    
    for col_def in ["description TEXT", "fit_score INTEGER", "fit_reason TEXT"]:
        try:
            cursor.execute(f"ALTER TABLE jobs ADD COLUMN {col_def}")
        except sqlite3.OperationalError:
            pass
    conn.commit()
    return conn


def save_jobs(conn, jobs):
    cursor = conn.cursor()
    new_count = 0
    for job in jobs:
        try:
            cursor.execute(
                "INSERT INTO jobs (title, company, location, url, description) VALUES (?, ?, ?, ?, ?)",
                (job["title"], job["company"], job["location"], job["url"], job["description"])
            )
            new_count += 1
        except sqlite3.IntegrityError:
            pass  
    conn.commit()
    return new_count



def build_prompt(title, company, location, description):
    return f"""You are helping a beginner CS student evaluate internship fit.

Student's skills:
{MY_SKILLS}

Internship:
Title: {title}
Company: {company}
Location: {location}
Description: {description}

Rate how good a fit this internship is for the student, from 1 to 10.
Respond in EXACTLY this format, nothing else:
SCORE: <number>
REASON: <one short sentence>
"""


def call_groq(prompt):
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    body = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3
    }
    response = requests.post(GROQ_URL, headers=headers, json=body)
    if response.status_code != 200:
        print(f"Groq API error: {response.status_code} - {response.text}")
        return None
    return response.json()["choices"][0]["message"]["content"]


def parse_response(raw_text):
    score, reason = None, ""
    for line in raw_text.strip().split("\n"):
        if line.upper().startswith("SCORE:"):
            try:
                score = int(line.split(":", 1)[1].strip())
            except ValueError:
                score = None
        elif line.upper().startswith("REASON:"):
            reason = line.split(":", 1)[1].strip()
    return score, reason


def score_unscored_jobs(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, company, location, description FROM jobs WHERE fit_score IS NULL")
    jobs = cursor.fetchall()

    for job_id, title, company, location, description in jobs:
        prompt = build_prompt(title, company, location, description or "")
        raw = call_groq(prompt)
        if raw is None:
            continue
        score, reason = parse_response(raw)
        cursor.execute("UPDATE jobs SET fit_score = ?, fit_reason = ? WHERE id = ?", (score, reason, job_id))
        conn.commit()


def show_top_matches(conn, min_score=6):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT title, company, url, fit_score, fit_reason
        FROM jobs
        WHERE fit_score >= ?
        ORDER BY fit_score DESC
    """, (min_score,))
    rows = cursor.fetchall()

    print(f"\n===== TOP MATCHES (score >= {min_score}) =====\n")
    if not rows:
        print("No matches at this score yet.")
    for title, company, url, score, reason in rows:
        print(f"[{score}/10] {title} @ {company}")
        print(f"  Why: {reason}")
        print(f"  Link: {url}\n")


def main():
    print("Fetching from Arbeitnow...")
    a_jobs = fetch_arbeitnow()
    print(f"  Found: {len(a_jobs)} internships")

    print("Fetching from RemoteOK...")
    r_jobs = fetch_remoteok()
    print(f"  Found: {len(r_jobs)} internships")

    all_jobs = a_jobs + r_jobs

    conn = setup_database()
    new_count = save_jobs(conn, all_jobs)
    print(f"\nNew listings saved: {new_count}")

    print("\nScoring unscored jobs (this may take a few seconds per job)...")
    score_unscored_jobs(conn)

    show_top_matches(conn, min_score=6)
    conn.close()


if __name__ == "__main__":
    main()