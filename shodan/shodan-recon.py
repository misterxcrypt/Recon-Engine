import requests

API_KEY = "fxyCUJDHaF9t9mUSNkqYalrDmobeeq60"
# query = "apache"
query = input("Enter your query:")

# Shodan Exploits API endpoint
url = f"https://exploits.shodan.io/api/search?query={query}&key={API_KEY}"
# url = f"https://api.shodan.io/shodan/host/{ip}?key={API_KEY}"

# Send GET request
response = requests.get(url)

# Check if request was successful
if response.status_code == 200:
    data = response.json()
    print(data)
    print(f"Found {data['total']} exploits for query '{query}':\n")
    for exploit in data.get("matches", []):
        print(f"Title: {exploit.get('description', 'N/A')}")
        print(f"Source: {exploit.get('source', 'N/A')}")
        print(f"Type: {exploit.get('type', 'N/A')}")
        print(f"CVE: {', '.join(exploit.get('cve', [])) if exploit.get('cve') else 'N/A'}")
        print(f"URL: {exploit.get('source')}/{exploit.get('id')}")
        print("-" * 60)
else:
    print(f"Error: {response.status_code} - {response.text}")

