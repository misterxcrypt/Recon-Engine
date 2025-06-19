import subprocess
import json
import re
import sys
import os

def get_script_dir():
    """Get the directory where the script is located"""
    return os.path.dirname(os.path.abspath(__file__))

def run_jsrecon(url):
    print("[>] Running jsrecon...")
    script_dir = get_script_dir()
    jsrecon_path = os.path.join(script_dir, "JSRecon")
    
    if not os.path.exists(jsrecon_path):
        print(f"[!] Error: JSRecon binary not found at {jsrecon_path}")
        return []
        
    result = subprocess.run(
        [jsrecon_path, "--url", url, "--show-sensitive"],
        capture_output=True, text=True
    )
    print("[+] Completed jsrecon.")
    output = result.stdout.strip().splitlines()
    return output

def run_linkfinder(url):
    print("[>] Running linkfinder...")
    script_dir = get_script_dir()
    linkfinder_path = os.path.join(script_dir, "linkfinder.py")
    
    if not os.path.exists(linkfinder_path):
        print(f"[!] Error: linkfinder.py not found at {linkfinder_path}")
        return []
        
    result = subprocess.run(
        ["python3", linkfinder_path, "-i", url, "-d", "-o", "cli"],
        capture_output=True, text=True
    )
    print("[+] Completed linkfinder.")

    lines = result.stdout.strip().splitlines()
    urls = []

    for line in lines:
        line = line.strip()
        if line.startswith("http") or line.startswith("/"):
            urls.append(line)
    return urls

def run_secretfinder(url):
    print("[>] Running SecretFinder...")
    script_dir = get_script_dir()
    secretfinder_path = os.path.join(script_dir, "SecretFinder.py")
    
    if not os.path.exists(secretfinder_path):
        print(f"[!] Error: SecretFinder.py not found at {secretfinder_path}")
        return {"urls": [], "findings": {}}
        
    result = subprocess.run(
        ["python3", secretfinder_path, "-i", url, "-e", "-o", "cli"],
        capture_output=True, text=True
    )
    print("[+] Completed SecretFinder.")

    lines = result.stdout.strip().splitlines()
    urls = []
    findings = {}

    for line in lines:
        line = line.strip()
        if line.startswith("[ + ] URL:"):
            match = re.search(r'\[ \+ \] URL: (.+)', line)
            if match:
                urls.append(match.group(1).strip())
        elif "->" in line:
            parts = line.split("->", 1)
            if len(parts) == 2:
                key = parts[0].strip()
                value = parts[1].strip()
                if key not in findings:
                    findings[key] = []
                findings[key].append(value)
    
    return {
        "urls": urls,
        "findings": findings
    }

def get_link_type(url):
    """Determine the type of link based on its extension"""
    if url.endswith('.js'):
        return 'javascript'
    elif url.endswith('.json'):
        return 'json'
    elif url.endswith('.php'):
        return 'php'
    elif url.endswith('.txt'):
        return 'txt'
    elif url.endswith(('.html', '.htm')):
        return 'html'
    elif url.endswith('.css'):
        return 'css'
    else:
        return 'link'

def is_domain_link(url, domain):
    """Check if the URL belongs to the specified domain"""
    if url.startswith(('http://', 'https://')):
        return domain in url
    elif url.startswith('/'):
        return True  # Relative paths are considered domain links
    return False

def process_jsrecon_results(results, domain):
    """Process jsrecon results and return links and secrets"""
    links = []
    secrets = []
    jsrecon_links = 0
    jsrecon_secrets = 0
    
    for item in results:
        if item.startswith(('http://', 'https://')):
            if is_domain_link(item, domain):
                link_type = get_link_type(item)
                links.append({
                    "url": item,
                    "type": link_type
                })
                jsrecon_links += 1
        elif item.startswith('/'):
            # Convert relative paths to absolute URLs
            absolute_url = f"https://{domain}{item}"
            link_type = get_link_type(absolute_url)
            links.append({
                "url": absolute_url,
                "type": link_type
            })
            jsrecon_links += 1
        else:
            secrets.append(item)
            jsrecon_secrets += 1
            
    return links, secrets, jsrecon_links, jsrecon_secrets

def process_linkfinder_results(results, domain):
    """Process linkfinder results and return links"""
    links = []
    linkfinder_count = 0
    
    for item in results:
        if item.startswith(('http://', 'https://')):
            if is_domain_link(item, domain):
                link_type = get_link_type(item)
                links.append({
                    "url": item,
                    "type": link_type
                })
                linkfinder_count += 1
        elif item.startswith('/'):
            # Convert relative paths to absolute URLs
            absolute_url = f"https://{domain}{item}"
            link_type = get_link_type(absolute_url)
            links.append({
                "url": absolute_url,
                "type": link_type
            })
            linkfinder_count += 1
            
    return links, linkfinder_count

def process_secretfinder_results(results, domain):
    """Process secretfinder results and return links and secrets"""
    links = []
    secrets = []
    secretfinder_urls = 0
    secretfinder_findings = sum(len(values) for values in results["findings"].values())
    
    for url in results["urls"]:
        if url.startswith(('http://', 'https://')):
            if is_domain_link(url, domain):
                link_type = get_link_type(url)
                links.append({
                    "url": url,
                    "type": link_type
                })
                secretfinder_urls += 1
        elif url.startswith('/'):
            # Convert relative paths to absolute URLs
            absolute_url = f"https://{domain}{url}"
            link_type = get_link_type(absolute_url)
            links.append({
                "url": absolute_url,
                "type": link_type
            })
            secretfinder_urls += 1
    
    for key, values in results["findings"].items():
        for value in values:
            secrets.append(f"{key}: {value}")
            
    return links, secrets, secretfinder_urls, secretfinder_findings

def main():
    if len(sys.argv) < 2:
        print("Usage: python jsDiscoveryModule.py <domain>")
        print("Example: python jsDiscoveryModule.py saptanglabs.com")
        sys.exit(1)

    domain = sys.argv[1]
    url = f"https://{domain}"  # Default to https

    # Get results from all tools
    print("\n[>] Running tools and collecting data...")
    jsrecon_results = run_jsrecon(url)
    linkfinder_results = run_linkfinder(url)
    secretfinder_results = run_secretfinder(url)

    # Initialize output structure
    output = {
        "URLS": [],
        "secrets": []
    }

    # Process all results
    jsrecon_links, jsrecon_secrets, jsrecon_links_count, jsrecon_secrets_count = process_jsrecon_results(jsrecon_results, domain)
    linkfinder_links, linkfinder_count = process_linkfinder_results(linkfinder_results, domain)
    secretfinder_links, secretfinder_secrets, secretfinder_urls, secretfinder_findings = process_secretfinder_results(secretfinder_results, domain)

    # Combine all links and secrets
    output["URLS"].extend(jsrecon_links)
    output["URLS"].extend(linkfinder_links)
    output["URLS"].extend(secretfinder_links)
    output["secrets"].extend(jsrecon_secrets)
    output["secrets"].extend(secretfinder_secrets)

    # Print statistics
    print("\n[+] Tool Statistics:")
    print(f"  JSRecon: {len(jsrecon_results)} total items")
    print(f"    - Links from {domain}: {jsrecon_links_count}")
    print(f"    - Secrets: {jsrecon_secrets_count}")
    print(f"  LinkFinder: {linkfinder_count} links from {domain}")
    print(f"  SecretFinder: {secretfinder_urls + secretfinder_findings} total items")
    print(f"    - URLs from {domain}: {secretfinder_urls}")
    print(f"    - Findings: {secretfinder_findings}")
    
    print("\n[+] Final Output Statistics:")
    print(f"  Total Links from {domain}: {len(output['URLS'])}")
    print(f"  Total Secrets: {len(output['secrets'])}")

    # Save to js-{domain}.json in the script's directory
    script_dir = get_script_dir()
    output_path = os.path.join(script_dir, f"js-{domain}.json")
    with open(output_path, "w") as f:
        json.dump(output, f, indent=4)

    print(f"\n[✓] Results saved to {output_path}")

if __name__ == "__main__":
    main()
