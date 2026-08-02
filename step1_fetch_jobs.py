

import requests
URL = "https://www.arbeitnow.com/api/job-board-api"


def fetch_jobs():

    response = requests.get(URL)

    if response.status_code != 200:
        print(f"Something went wrong. Status code: {response.status_code}")
        return []

    data = response.json()

    jobs = data["data"]
    return jobs


def filter_internships(jobs):
    """Keep only listings that look like internships."""

    internships = []

    for job in jobs:
        title = job.get("title", "")
        tags = job.get("tags", [])

        title_has_intern = "intern" in title.lower()
        tags_have_intern = any("intern" in tag.lower() for tag in tags)

        if title_has_intern or tags_have_intern:
            internships.append(job)

    return internships


def main():
    print("Fetching jobs from Arbeitnow API...\n")
    jobs = fetch_jobs()
    print(f"Total jobs pulled: {len(jobs)}\n")

    internships = filter_internships(jobs)
    print(f"Internship-looking listings found: {len(internships)}\n")

    for job in internships:
        print("-" * 60)
        print(f"Title:    {job.get('title')}")
        print(f"Company:  {job.get('company_name')}")
        print(f"Remote:   {job.get('remote')}")
        print(f"Location: {job.get('location')}")
        print(f"Link:     {job.get('url')}")

    if not internships:
        print("No internships matched right now.")
        print("This is normal — this API leans toward EU/remote jobs.")
        print("We'll add more sources (like RemoteOK) in the next step.")


if __name__ == "__main__":
    main()
