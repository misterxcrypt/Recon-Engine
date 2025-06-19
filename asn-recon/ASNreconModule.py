import socket
import requests
import subprocess
import json
from urllib.parse import urlparse

def extract_domain(url):
    parsed_url = urlparse(url)
    return parsed_url.netloc if parsed_url.netloc else parsed_url.path

def get_ip(domain):
    try:
        return socket.gethostbyname(domain)
    except Exception as e:
        print(f"[!] Error resolving domain to IP: {e}")
        return None

def get_asn(ip):
    try:
        response = requests.get(f"https://ipinfo.io/{ip}/json")
        if response.status_code == 200:
            data = response.json()
            org = data.get('org', '')
            if org.startswith('AS'):
                return org.split(' ')[0]  # Return ASXXXX
        return None
    except Exception as e:
        print(f"[!] Error getting ASN: {e}")
        return None

def whois_asn(asn):
    try:
        result = subprocess.check_output(["whois", asn], universal_newlines=True)
        return result
    except Exception as e:
        print(f"[!] Error running whois: {e}")
        return None

def parse_whois_output(output):
    parsed = {}
    if not output:
        return parsed
    for line in output.splitlines():
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()
            if key in parsed:
                if isinstance(parsed[key], list):
                    parsed[key].append(value)
                else:
                    parsed[key] = [parsed[key], value]
            else:
                parsed[key] = value
    return parsed

def get_ip_ranges_from_asn(asn):
    try:
        url = f"https://stat.ripe.net/data/announced-prefixes/data.json?resource={asn}"
        response = requests.get(url)
        data = response.json()
        return [item["prefix"] for item in data["data"]["prefixes"]]
    except:
        return []

def get_bgp_neighbors(asn):
    try:
        url = f"https://stat.ripe.net/data/asn-neighbours/data.json?resource={asn}"
        response = requests.get(url)
        data = response.json()
        neighbors = {
            # "left": [n["asn"] for n in data["data"].get("left", [])],   # upstream
            # "right": [n["asn"] for n in data["data"].get("right", [])], # downstream
            "all": [data["data"].get("neighbours", [])]
        }
        return neighbors
    except Exception as e:
        print(f"[!] Failed to get BGP neighbors: {e}")
        return {}

def main():
    url = input("Enter the URL: ").strip()
    domain = extract_domain(url)
    print(f"[*] Extracted domain: {domain}")

    ip = get_ip(domain)
    if not ip:
        return
    print(f"[*] IP Address: {ip}")

    asn = get_asn(ip)
    if not asn:
        return
    print(f"[*] ASN: {asn}")

    whois_data = whois_asn(asn)
    if not whois_data:
        return
    print(f"[*] Whois lookup completed.")

    parsed_data = parse_whois_output(whois_data)
    parsed_data["asn"] = asn
    parsed_data["ip"] = ip

    # Add BGP announced prefixes
    prefixes = get_ip_ranges_from_asn(asn)
    parsed_data["announced_prefixes"] = prefixes
    print(f"[+] Found {len(prefixes)} announced prefixes.")

    # Add BGP peer neighbors
    neighbors = get_bgp_neighbors(asn)
    parsed_data["bgp_neighbors"] = neighbors
    print(f"[+] Found {len(neighbors.get('all', []))} BGP neighbors.")

    output_filename = f"{domain.replace('.', '_')}_asn_bgp_recon.json"
    with open(output_filename, "w") as f:
        json.dump(parsed_data, f, indent=4)

    print(f"[+] Recon info saved to {output_filename}")

if __name__ == "__main__":
    main()
