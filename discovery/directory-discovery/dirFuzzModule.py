import subprocess
import json
import re
from urllib.parse import urlparse
import sys
import os

# def run_hakrawler(url):
#     print("[*] Running hakrawler...")
#     try:
#         cmd = f'echo "{url}" | hakrawler -d 2 -u | grep {url}'
#         result = subprocess.check_output(cmd, shell=True, text=True)
#         urls = result.strip().split('\n')
#         return {"hakrawler_results": urls}
#     except subprocess.CalledProcessError as e:
#         print(f"[!] Error running hakrawler: {e}")
#         return {"hakrawler_results": []}

# def run_gospider(url):
#     print("[*] Running gospider...")
#     try:
#         cmd = f'gospider -s "{url}" --json --js --subs --sitemap --robots | grep {url}'
#         result = subprocess.check_output(cmd, shell=True, text=True)
#         urls = []
#         for line in result.strip().split('\n'):
#             try:
#                 data = json.loads(line)
#                 urls.append(data.get("output", ""))
#             except json.JSONDecodeError:
#                 continue
#         return {"gospider_results": urls}
#     except subprocess.CalledProcessError as e:
#         print(f"[!] Error running gospider: {e}")
#         return {"gospider_results": []}

def get_script_dir():
    """Get the directory where the script is located"""
    return os.path.dirname(os.path.abspath(__file__))

def get_url_type(url):
    """Determine the type of URL based on its extension"""
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
    elif url.endswith(('.jpg', '.jpeg', '.png', '.gif', '.svg', '.ico')):
        return 'image'
    elif url.endswith(('.pdf', '.doc', '.docx', '.xls', '.xlsx')):
        return 'document'
    else:
        return 'link'

def process_ffuf_output(output_path):
    """Process the ffuf output file and extract URLs with their types"""
    try:
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        urls = []
        for result in data.get('results', []):
            url = result.get('url', '')
            if url:
                url_type = get_url_type(url)
                urls.append({
                    "url": url,
                    "type": url_type
                })
        
        return urls
    except Exception as e:
        print(f"[!] Error processing ffuf output: {e}")
        return []

def run_ffuf(url, domain):
    print("[*] Running ffuf...")
    try:
        script_dir = get_script_dir()
        ffuf_path = os.path.join(script_dir, "ffuf")
        wordlist_path = os.path.join(script_dir, "raft-medium-directories.txt")
        ffuf_output_path = os.path.join(script_dir, f"ffuf-{domain}.json")
        final_output_path = os.path.join(script_dir, f"directory-{domain}.json")
        
        if not os.path.exists(ffuf_path):
            print(f"[!] Error: ffuf binary not found at {ffuf_path}")
            return {"ffuf_results": []}
            
        if not os.path.exists(wordlist_path):
            print(f"[!] Error: wordlist not found at {wordlist_path}")
            return {"ffuf_results": []}
            
        cmd = f'{ffuf_path} -u {url.rstrip("/")}/FUZZ -w {wordlist_path} -t 1000 -of json -o {ffuf_output_path} -fc 404 -ac'
        print(cmd)
        subprocess.check_output(cmd, shell=True, text=True)

        # Process the ffuf output file
        urls = process_ffuf_output(ffuf_output_path)
        
        # Save the processed results
        with open(final_output_path, 'w') as f:
            json.dump({"URLS": urls}, f, indent=4)
            
        print(f"[+] Found {len(urls)} URLs")
        return {"ffuf_results": urls}

    except subprocess.CalledProcessError as e:
        print(f"[!] Error running ffuf: {e}")
        return {"ffuf_results": []}
    except Exception as e:
        print(f"[!] Unexpected error: {e}")
        return {"ffuf_results": []}

def main():
    if len(sys.argv) < 2:
        print("Usage: python dirFuzzModule.py <domain>")
        print("Example: python dirFuzzModule.py saptanglabs.com")
        sys.exit(1)

    domain = sys.argv[1]
    url = f"https://{domain}"  # Default to https

    # Run ffuf with the domain
    run_ffuf(url, domain)
    script_dir = get_script_dir()
    output_path = os.path.join(script_dir, f"directory-{domain}.json")
    print(f"[+] All outputs saved to {output_path}")

if __name__ == "__main__":
    main()
