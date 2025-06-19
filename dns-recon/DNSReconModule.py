import subprocess
import json
import re
from urllib.parse import urlparse

def extract_domain(url):
    parsed_url = urlparse(url)
    if parsed_url.netloc:
        return parsed_url.netloc
    return parsed_url.path  # if no scheme like https://

def run_msdnsscan(domain):
    try:
        result = subprocess.run(
            ['python3', 'msdnsscan.py', '-d', domain, '-a'],
            capture_output=True, text=True, check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print("[!] Error running msdnsscan:", e)
        return ""

def parse_msdnsscan_output(output):
    sections = {
        "A_Records": [],
        "NS_Records": [],
        "CNAME_Records": [],
        "MX_Records": [],
        "PTR_Records": [],
        "SOA_Records": [],
        "SRV_Records": [],
        "TXT_Records": [],
        "SPF_Records": [],
        "DMARC_Records": [],
        "DKIM_Records": [],
        "Zone_Transfer_Records": [],
        "Subdomains": []
    }
    
    current_section = None
    lines = output.splitlines()

    for line in lines:
        line = line.strip()
        
        if line.startswith("A Records"):
            current_section = "A_Records"
        elif line.startswith("NS Records"):
            current_section = "NS_Records"
        elif line.startswith("CNAME records"):
            current_section = "CNAME_Records"
        elif line.startswith("MX Records"):
            current_section = "MX_Records"
        elif line.startswith("PTR Records"):
            current_section = "PTR_Records"
        elif line.startswith("SOA Records"):
            current_section = "SOA_Records"
        elif line.startswith("SRV Records"):
            current_section = "SRV_Records"
        elif line.startswith("TXT Records"):
            current_section = "TXT_Records"
        elif line.startswith("Email Records"):
            current_section = "Email_Records"
        elif line.startswith("Zone Transfer Records"):
            current_section = "Zone_Transfer_Records"
        elif "Checking for subdomains" in line:
            current_section = "Subdomains"
        
        elif current_section and line and not line.startswith("[info]") and not line.startswith("--------------------------------------------------"):
            if current_section == "Email_Records":
                if "[spf record]" in line.lower():
                    sections["SPF_Records"].append(line)
                elif "dmarc data not found" in line.lower():
                    sections["DMARC_Records"].append("Not Found")
                elif "dkim data not found" in line.lower():
                    sections["DKIM_Records"].append("Not Found")
            elif current_section == "Subdomains":
                parts = re.split(r'\s-\s', line)
                if len(parts) >= 2:
                    subdomain_info = {
                        "Subdomain": parts[0],
                        "IP": parts[1],
                        "Details": parts[2] if len(parts) >= 3 else ""
                    }
                    sections["Subdomains"].append(subdomain_info)
            else:
                sections[current_section].append(line)
    
    return sections

def main():
    url = input("Enter the URL (e.g., https://saptanglabs.com): ").strip()
    domain = extract_domain(url)
    print(f"[*] Extracted domain: {domain}")
    
    print("[*] Running MSDNS Scan...")
    output = run_msdnsscan(domain)
    if output:
        print("[*] Parsing results...")
        parsed_data = parse_msdnsscan_output(output)
        filename = f"{domain}_dns_scan.json"
        with open(filename, 'w') as f:
            json.dump(parsed_data, f, indent=4)
        print(f"[+] Results saved to {filename}")
    else:
        print("[!] No output captured.")

if __name__ == "__main__":
    main()
