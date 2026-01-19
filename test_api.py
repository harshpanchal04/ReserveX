import requests
import json

def test_endpoint(url, payload):
    print(f"Testing {url} with {payload}...")
    try:
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Origin": "https://www.irctc.co.in",
            "Referer": "https://www.irctc.co.in/online-charts/"
        }
        response = requests.post(url, json=payload, headers=headers, verify=False, timeout=30) # nosec B501
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:200]}...")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

base_urls = [
    "https://www.irctc.co.in/online-charts/api/trainComposition",
    "https://www.irctc.co.in/online-charts/api/coachComposition",
    "https://www.irctc.co.in/online-charts/api/vacant-berth",
    "https://www.irctc.co.in/api/v1/trainComposition"
]

payload = {
    "trainNo": "12627",
    "jDate": "2025-12-16",
    "boardingStation": "SBC"
}

if __name__ == "__main__":
    requests.packages.urllib3.disable_warnings()
    for url in base_urls:
        if test_endpoint(url, payload):
            print(f"SUCCESS: {url}")
            break
