import subprocess
import json
import os
import sys

def get_script_dir():
    """Get the directory where the script is located"""
    return os.path.dirname(os.path.abspath(__file__))

def run_gau(domain):
    print("[>] Running gau...")
    try:
        script_dir = get_script_dir()
        gau_path = os.path.join(script_dir, "gau")
        
        if not os.path.exists(gau_path):
            print(f"[!] Error: gau binary not found at {gau_path}")
            return []
            
        result = subprocess.run(
            [gau_path, domain, "--json"], capture_output=True, text=True
        )
        print("[+] Completed gau.")
        lines = result.stdout.strip().splitlines()
        parsed = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                parsed.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return parsed
    except Exception as e:
        print(f"[!] Error running gau: {e}")
        return []

def run_gospider(url):
    print("[>] Running gospider...")
    try:
        script_dir = get_script_dir()
        gospider_path = os.path.join(script_dir, "gospider")
        
        if not os.path.exists(gospider_path):
            print(f"[!] Error: gospider binary not found at {gospider_path}")
            return []
            
        result = subprocess.run(
            [gospider_path, "-s", url, "--json", "--js", "--subs", "--sitemap", "--robots"],
            capture_output=True, text=True
        )
        print("[+] Completed gospider.")
        lines = result.stdout.strip().splitlines()
        parsed = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                parsed.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return parsed
    except Exception as e:
        print(f"[!] Error running gospider: {e}")
        return []

def run_hakrawler(url):
    print("[>] Running hakrawler...")
    try:
        script_dir = get_script_dir()
        hakrawler_path = os.path.join(script_dir, "hakrawler")
        
        if not os.path.exists(hakrawler_path):
            print(f"[!] Error: hakrawler binary not found at {hakrawler_path}")
            return []
            
        cmd = f'echo {url} | {hakrawler_path} -json -subs -u'
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True
        )
        print("[+] Completed hakrawler.")
        lines = result.stdout.strip().splitlines()
        parsed = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                parsed.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return parsed
    except Exception as e:
        print(f"[!] Error running hakrawler: {e}")
        return []

def run_waybackurls(domain):
    print("[>] Running waybackurls...")
    try:
        script_dir = get_script_dir()
        waybackurls_path = os.path.join(script_dir, "waybackurls")
        
        if not os.path.exists(waybackurls_path):
            print(f"[!] Error: waybackurls binary not found at {waybackurls_path}")
            return []
            
        cmd = f'echo {domain} | {waybackurls_path}'
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True
        )
        print("[+] Completed waybackurls.")
        urls = result.stdout.strip().splitlines()
        return urls
    except Exception as e:
        print(f"[!] Error running waybackurls: {e}")
        return []

def process_gau_results(results, domain):
    processed = []
    for item in results:
        try:
            url = item.get("url", "")
            if not url:
                continue
                
            # Only keep URLs from the input domain
            if domain not in url:
                continue
                
            # Determine type based on file extension
            if url.endswith(('.js', '.jsx')):
                url_type = "javascript"
            elif url.endswith(('.css', '.scss', '.less')):
                url_type = "css"
            elif url.endswith(('.json')):
                url_type = "json"
            elif url.endswith(('.txt', '.text', '.log')):
                url_type = "txt"
            elif url.endswith(('.jpg', '.jpeg', '.png', '.gif', '.svg', '.ico', '.webp')):
                url_type = "image"
            elif url.endswith(('.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx')):
                url_type = "document"
            elif url.endswith(('.xml', '.rss', '.atom')):
                url_type = "xml"
            elif url.endswith(('.php', '.asp', '.aspx', '.jsp')):
                url_type = "server_script"
            elif url.endswith(('.html', '.htm')):
                url_type = "html"
            else:
                url_type = "link"
                
            processed.append({
                "url": url,
                "type": url_type
            })
        except Exception as e:
            continue
    return processed

def process_gospider_results(results, domain):
    processed = []
    for item in results:
        try:
            # Get the URL from the output field
            url = item.get("output", "")
            if not url:
                continue
                
            # Get the domain from input
            input_domain = item.get('input', '').replace('https://', '').replace('http://', '').strip('/')
            
            # Handle different types of relative URLs
            if url.startswith('/'):
                # Handle absolute paths
                url = f"https://{input_domain}{url}"
            elif url.startswith('./'):
                # Handle relative paths starting with ./
                url = f"https://{input_domain}/{url[2:]}"  # Remove ./ and prepend domain
            elif not url.startswith(('http://', 'https://')):
                # Handle other relative paths
                url = f"https://{input_domain}/{url}"
            
            # Only keep URLs from the input domain
            if domain not in url:
                continue
            
            # Determine type based on file extension
            if url.endswith(('.js', '.jsx')):
                url_type = "javascript"
            elif url.endswith(('.css', '.scss', '.less')):
                url_type = "css"
            elif url.endswith(('.json')):
                url_type = "json"
            elif url.endswith(('.txt', '.text', '.log')):
                url_type = "txt"
            elif url.endswith(('.jpg', '.jpeg', '.png', '.gif', '.svg', '.ico', '.webp')):
                url_type = "image"
            elif url.endswith(('.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx')):
                url_type = "document"
            elif url.endswith(('.xml', '.rss', '.atom')):
                url_type = "xml"
            elif url.endswith(('.php', '.asp', '.aspx', '.jsp')):
                url_type = "server_script"
            elif url.endswith(('.html', '.htm')):
                url_type = "html"
            else:
                url_type = "link"
                
            processed.append({
                "url": url,
                "type": url_type
            })
        except Exception as e:
            continue
    return processed

def process_hakrawler_results(results, domain):
    processed = []
    for item in results:
        try:
            url = item.get("URL", "")
            if not url:
                continue
                
            # Only keep URLs from the input domain
            if domain not in url:
                continue
                
            # Determine type based on file extension
            if url.endswith(('.js', '.jsx')):
                url_type = "javascript"
            elif url.endswith(('.css', '.scss', '.less')):
                url_type = "css"
            elif url.endswith(('.json')):
                url_type = "json"
            elif url.endswith(('.txt', '.text', '.log')):
                url_type = "txt"
            elif url.endswith(('.jpg', '.jpeg', '.png', '.gif', '.svg', '.ico', '.webp')):
                url_type = "image"
            elif url.endswith(('.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx')):
                url_type = "document"
            elif url.endswith(('.xml', '.rss', '.atom')):
                url_type = "xml"
            elif url.endswith(('.php', '.asp', '.aspx', '.jsp')):
                url_type = "server_script"
            elif url.endswith(('.html', '.htm')):
                url_type = "html"
            else:
                url_type = "link"
                
            processed.append({
                "url": url,
                "type": url_type
            })
        except Exception as e:
            continue
    return processed

def main():
    if len(sys.argv) < 2:
        print("Usage: python URL_DiscoveryModule.py <domain>")
        print("Example: python URL_DiscoveryModule.py saptanglabs.com")
        sys.exit(1)

    domain = sys.argv[1]
    url = f"https://{domain}"  # Default to https

    # Get results from all tools
    gau_results = run_gau(domain)
    print(f"[+] gau found {len(gau_results)} URLs")
    
    gospider_results = run_gospider(url)
    print(f"[+] gospider found {len(gospider_results)} URLs")
    
    hakrawler_results = run_hakrawler(url)
    print(f"[+] hakrawler found {len(hakrawler_results)} URLs")
    
    waybackurls_results = run_waybackurls(domain)
    print(f"[+] waybackurls found {len(waybackurls_results)} URLs")
    
    script_dir = get_script_dir()
    waybackurls_path = os.path.join(script_dir, f"waybackurls-{domain}.json")
    with open(waybackurls_path, "w") as f:
        json.dump({"waybackurls": waybackurls_results}, f, indent=4)

    # Process and combine all URLs
    gau_processed = process_gau_results(gau_results, domain)
    print(f"[+] gau processed {len(gau_processed)} URLs from {domain}")
    
    gospider_processed = process_gospider_results(gospider_results, domain)
    print(f"[+] gospider processed {len(gospider_processed)} URLs from {domain}")
    
    hakrawler_processed = process_hakrawler_results(hakrawler_results, domain)
    print(f"[+] hakrawler processed {len(hakrawler_processed)} URLs from {domain}")

    # Combine all URLs without removing duplicates
    all_urls = []
    all_urls.extend(gau_processed)
    all_urls.extend(gospider_processed)
    all_urls.extend(hakrawler_processed)
    print(f"[+] Total URLs from {domain} in urls-{domain}.json: {len(all_urls)}")

    # Save combined results to urls-{domain}.json
    urls_path = os.path.join(script_dir, f"urls-{domain}.json")
    with open(urls_path, "w") as f:
        json.dump({"URLS": all_urls}, f, indent=4)
    print(f"[✓] Results saved to: {waybackurls_path} and {urls_path}")

if __name__ == "__main__":
    main()

