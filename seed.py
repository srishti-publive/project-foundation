import requests

BASE = "http://localhost:8000/api"

def seed(tasks):
    for t in tasks:
        requests.post(f"{BASE}/tasks/create/", json=t)
    print(f"Seeded {len(tasks)} tasks")