import urllib.request
import json
import sys

BASE_URL = "http://localhost:8000"

def make_request(endpoint, output_filename=None):
    url = f"{BASE_URL}{endpoint}"
    print(f"Testing {url}...")
    try:
        with urllib.request.urlopen(url) as response:
            if response.status == 200:
                data = json.loads(response.read().decode())
                print(f"✅ Success! Response:")
                print(json.dumps(data, indent=2)[:500] + "... (truncated)" if len(str(data)) > 500 else json.dumps(data, indent=2))
                
                if output_filename:
                    with open(output_filename, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2)
                    print(f"💾 Saved response to '{output_filename}'")
                return True
            else:
                print(f"Failed with status code: {response.status}")
                return False
    except urllib.error.URLError as e:
        print(f"Connection failed: {e}")
        print("   (Make sure the Docker container is running with 'docker-compose up')")
        return False
    except Exception as e:
        print(f"An error occurred: {e}")
        return False
    print("-" * 40)

def main():
    print("--- n8n Workflow Popularity Tracker API Verification ---\n")
    
    # 1. Check Health
    if not make_request("/health"):
        sys.exit(1)
        
    print("\n" + "-" * 40 + "\n")

    # 2. Check Workflows (Database Connection)
    make_request("/api/v1/workflows", output_filename="api_workflows.json")

    print("\n" + "-" * 40 + "\n")

    # 3. Check Analytics (Novelty Feature)
    make_request("/api/v1/analytics/geographic-divergence")

if __name__ == "__main__":
    main()
