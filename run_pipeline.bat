@echo off
cd /d "C:\Users\ITAdmin\OneDrive\Desktop\internship-radar"
"C:\Program Files\Python314\python.exe" daily_pipeline.py
"C:\Program Files\Python314\python.exe" send_email.py
