import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def post(path, payload):
    try:
        r = requests.post(f"{BASE_URL}{path}", json=payload, timeout=10)
        return r.status_code, safe_json(r)
    except Exception as e:
        return 500, str(e)

def get(path):
    try:
        r = requests.get(f"{BASE_URL}{path}", timeout=10)
        return r.status_code, safe_json(r)
    except Exception as e:
        return 500, str(e)

def delete(path):
    try:
        r = requests.delete(f"{BASE_URL}{path}", timeout=10)
        return r.status_code, safe_json(r)
    except Exception as e:
        return 500, str(e)

def safe_json(response):
    try:
        return response.json()
    except:
        return response.text