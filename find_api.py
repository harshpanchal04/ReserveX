import requests
import re
from urllib.parse import urljoin

BASE_URL = "https://www.irctc.co.in/online-charts/"

def find_api_endpoints():
    print(f"Fetching {BASE_URL}...")
    try:
        response = requests.get(BASE_URL, verify=False, timeout=30) # nosec B501
        html = response.text
    except Exception as e:
        print(f"Failed to fetch base URL: {e}")
        return

    # Find JS files
    js_files = re.findall(r'src="([^"]+\.js)"', html)
    print(f"Found {len(js_files)} JS files.")

    for js_file in js_files:
        full_url = urljoin(BASE_URL, js_file)
        print(f"Scanning {full_url}...")
        try:
            js_content = requests.get(full_url, verify=False, timeout=30).text # nosec B501
            
            # Look for API-like patterns
            # Patterns: "api/...", "/api/...", "coachComposition", "trainSchedule"
            matches = re.findall(r'["\']/?api/[^"\']+["\']', js_content)
            matches += re.findall(r'["\'][^"\']*coachComposition[^"\']*["\']', js_content)
            matches += re.findall(r'["\'][^"\']*schedule[^"\']*["\']', js_content)
            
            if matches:
                print(f"  Found potential endpoints in {js_file}:")
                for m in set(matches):
                    print(f"    - {m}")
        except Exception as e:
            print(f"  Failed to fetch {js_file}: {e}")

if __name__ == "__main__":
    requests.packages.urllib3.disable_warnings()
    find_api_endpoints()
