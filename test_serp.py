import os
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('SERPAPI_API_KEY')
print(f"Key found: {api_key[:5]}...{api_key[-5:] if api_key else 'None'}")

url = "https://serpapi.com/search"
params = {
    "engine": "google_local",
    "q": "automotive oil change garage 392150",
    "api_key": api_key
}

try:
    response = requests.get(url, params=params, timeout=30)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        results = data.get('local_results', [])
        print(f"Found {len(results)} results.")
        for r in results[:2]:
            print(f"- {r.get('title')}")
    else:
        print(f"Error: {response.text}")
except Exception as e:
    print(f"Exception: {e}")
