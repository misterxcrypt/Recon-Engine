import subprocess
import json
import os
import re
import sys
from datetime import datetime
from urllib.parse import urlparse

# ========== UTILITIES ===========

def extract_domain(input_url):
    parsed = urlparse(input_url)
    return parsed.netloc or parsed.path


def sanitize_filename(domain):
    return re.sub(r'\W+', '_', domain)


def parse_whois_output(output):
    data = {}
    for line in output.splitlines():
        if ':' not in line:
            continue
        key, val = line.split(':', 1)
        key = key.strip()
        val = val.strip()
        if not key or not val:
            continue
        if key in data:
            if isinstance(data[key], list):
                data[key].append(val)
            else:
                data[key] = [data[key], val]
        else:
            data[key] = val
    return data


def fetch_whois(domain):
    try:
        res = subprocess.run(['./whois', domain], capture_output=True, text=True, timeout=20)
        if res.returncode != 0:
            return {'error': 'WHOIS lookup failed'}
        return parse_whois_output(res.stdout)
    except Exception as e:
        return {'error': str(e)}

# ========== SUBDOMAIN ENUM & ENRICHMENT ===========

def fetch_subdomains(domain):
    try:
        res = subprocess.run(['./subfinder', '-d', domain, '-silent'], capture_output=True, text=True, timeout=60)
        return [d.strip() for d in res.stdout.splitlines() if d.strip()]
    except Exception as e:
        print(f"[!] subfinder error: {e}")
        return []


def enrich_subdomains(subdomains):
    if not subdomains:
        return {}
    # Create URLs with both HTTP and HTTPS schemes
    urls = []
    for sub in subdomains:
        urls.append(f"http://{sub}")
        urls.append(f"https://{sub}")
    
    cmd = [
        './httpx',
        '-json',
        '-status-code',
        '-tls-grab',
        '-title',
        '-content-length',
        '-web-server',
        '-cdn',
        '-follow-redirects',
        '-timeout', '30',
        '-retries', '2',
        '-no-color',
        '-v'
    ]
    try:
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = proc.communicate(input='\n'.join(urls), timeout=300)
        
        enriched = {}
        failed_urls = set()
        
        # Process stderr for failed connections
        for line in stderr.splitlines():
            if "Failed" in line and "Get" in line:
                try:
                    # Extract URL from the error message
                    url = line.split("'")[1]
                    failed_urls.add(url)
                except:
                    continue
        
        # Process stdout for successful responses
        for line in stdout.splitlines():
            try:
                item = json.loads(line)
                url = item.get('url') or item.get('input')
                if not url:
                    continue
                    
                enriched[url] = {
                    'url': url,
                    'status_code': item.get('status_code'),
                    'tls_version': item.get('tls', {}).get('tls_version'),
                    'content_length': item.get('content_length'),
                    'title': item.get('title'),
                    'server': item.get('webserver'),
                    'cdn': item.get('cdn_name')
                }
            except json.JSONDecodeError:
                continue
                
        # Add failed URLs to enriched with null status
        for url in failed_urls:
            if url not in enriched:
                enriched[url] = {
                    'url': url,
                    'status_code': None,
                    'tls_version': None,
                    'content_length': None,
                    'title': None,
                    'server': None,
                    'cdn': None
                }
            
    except Exception as e:
        print(f"[!] httpx error: {e}")
        return {}

    return enriched


def merge_data(subdomains, enriched):
    alive = []
    dead = []
    check = []
    id_counter = 1
    
    for url in enriched:
        try:
            item = enriched[url]
            protocol = url.split('://')[0]
            domain = url.split('://')[1]
            
            result = {
                'id': id_counter,
                'domain': domain,
                'protocol': protocol,
                'url': url,
                'status_code': item.get('status_code'),
                'tls_version': item.get('tls_version'),
                'content_length': item.get('content_length'),
                'title': item.get('title'),
                'server': item.get('server'),
                'cdn': item.get('cdn')
            }
            
            status_code = item.get('status_code')
            
            # 404 goes to dead
            if status_code is None or status_code == 404:
                dead.append(result)
            # 200 and 403 go to alive
            elif status_code == 200 or status_code == 403:
                alive.append(result)
            # All other status codes go to check
            else:
                check.append(result)
                
            id_counter += 1
        except Exception as e:
            continue
    
    return {'alive': alive, 'dead': dead, 'check': check}

# ========== MAIN ===========

def main():
    if len(sys.argv) != 2:
        print(f"Usage: python3 {os.path.basename(__file__)} <domain>")
        sys.exit(1)

    base = extract_domain(sys.argv[1].strip())

    print(f"[+] WHOIS lookup for: {base}")
    whois_data = fetch_whois(base)

    print(f"[+] Enumerating subdomains for: {base}")
    subs = fetch_subdomains(base)
    print(f"[+] {len(subs)} subdomains found")

    print("[+] Enriching subdomains via httpx...")
    enriched = enrich_subdomains(subs)

    print("[+] Merging results...")
    sub_results = merge_data(subs, enriched)

    output = {
        'whois': whois_data,
        'alive': sub_results['alive'],
        'dead': sub_results['dead'],
        'check': sub_results['check']
    }

    fname = f"{sanitize_filename(base)}_scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(fname, 'w') as f:
        json.dump(output, f, indent=4)
    print(f"[✓] Saved output to {fname}")
    print(f"[+] Found {len(sub_results['alive'])} alive endpoints, {len(sub_results['dead'])} dead endpoints, and {len(sub_results['check'])} endpoints to check")

if __name__ == '__main__':
    main()
