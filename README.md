##Internship Radar

I got tired of manually checking job boards every day looking for internships, so I built this instead.

It pulls fresh internship listings from the last 24 hours from a couple of free job APIs (Arbeitnow and RemoteOK), saves them so I don't see the same one twice, and then uses an LLM to score how good a fit each one actually is for my skills. If something scores well it emails me automatically, so I don't have to remember to check anything.

Built with Python, SQLite, the Groq API for scoring, and Windows Task Scheduler to run it every day on its own.

Still figuring out what to add next, maybe more job sources or an easier way to update my skills without opening the code.