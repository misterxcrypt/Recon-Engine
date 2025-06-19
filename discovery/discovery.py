#!/usr/bin/env python3
import os
import sys
import json
from termcolor import cprint
import subprocess
from datetime import datetime
import shutil

def print_banner():
    cprint(r"""
--------------------------------------
      Recon Engine - Main Module
--------------------------------------
""", 'cyan')

def merge_urls_files(domain, output_dir):
    """Merge URL arrays from different files into urls-{domain}.json"""
    try:
        # Read all URL files
        urls_file = os.path.join(output_dir, f"urls-{domain}.json")
        js_file = os.path.join(output_dir, f"js-{domain}.json")
        directory_file = os.path.join(output_dir, f"directory-{domain}.json")
        
        # Initialize combined URLs array
        combined_urls = []
        
        # Read and merge urls-{domain}.json if it exists
        if os.path.exists(urls_file):
            with open(urls_file, 'r') as f:
                data = json.load(f)
                combined_urls.extend(data.get("URLS", []))
        
        # Read and merge js-{domain}.json if it exists
        if os.path.exists(js_file):
            with open(js_file, 'r') as f:
                data = json.load(f)
                combined_urls.extend(data.get("URLS", []))
            # Remove the js file after merging
            os.remove(js_file)
        
        # Read and merge directory-{domain}.json if it exists
        if os.path.exists(directory_file):
            with open(directory_file, 'r') as f:
                data = json.load(f)
                combined_urls.extend(data.get("URLS", []))
            # Remove the directory file after merging
            os.remove(directory_file)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_urls = []
        for url in combined_urls:
            url_str = json.dumps(url, sort_keys=True)
            if url_str not in seen:
                seen.add(url_str)
                unique_urls.append(url)
        
        # Save merged URLs
        with open(urls_file, 'w') as f:
            json.dump({"URLS": unique_urls}, f, indent=4)
        
        cprint(f"[+] Merged URLs saved to {urls_file}", 'green')
        return True
        
    except Exception as e:
        cprint(f"[-] Error merging URL files: {str(e)}", 'red')
        return False

def extract_secrets(domain, output_dir):
    """Extract secrets from js-{domain}.json and save to js-secrets-{domain}.json"""
    try:
        js_file = os.path.join(output_dir, f"js-{domain}.json")
        secrets_file = os.path.join(output_dir, f"js-secrets-{domain}.json")
        
        if os.path.exists(js_file):
            with open(js_file, 'r') as f:
                data = json.load(f)
                secrets = data.get("secrets", [])
            
            # Save secrets to new file
            with open(secrets_file, 'w') as f:
                json.dump({"secrets": secrets}, f, indent=4)
            
            cprint(f"[+] Secrets saved to {secrets_file}", 'green')
            return True
            
    except Exception as e:
        cprint(f"[-] Error extracting secrets: {str(e)}", 'red')
        return False

def collect_output_files(module_name, domain, output_dir):
    """Collect output files from a module and move them to the main output directory"""
    module_dir = os.path.join(os.getcwd(), module_name)
    
    # Define expected output files for each module
    expected_files = {
        "urldiscovery": [
            f"urls-{domain}.json",
            f"waybackurls-{domain}.json"
        ],
        "jsrecon": [
            f"js-{domain}.json"
        ],
        "directory-discovery": [
            f"directory-{domain}.json"
        ]
    }
    
    # Collect and move files
    moved_files = []
    for filename in expected_files.get(module_name, []):
        source_path = os.path.join(module_dir, filename)
        if os.path.exists(source_path):
            dest_path = os.path.join(output_dir, filename)
            shutil.move(source_path, dest_path)
            moved_files.append(filename)
            cprint(f"[+] Moved {filename} to output directory", 'green')
    
    return moved_files

def run_module(module_name, domain, output_dir):
    """Run a specific module and return its output file path"""
    # cprint(f"\n[+] Running {module_name} module...", 'green')
    
    # # Create module-specific output directory
    # module_output_dir = os.path.join(output_dir, module_name)
    # os.makedirs(module_output_dir, exist_ok=True)
    
    # Run the module
    try:
        if module_name == "urldiscovery":
            cmd = ["python3", "urldiscovery/URL_DiscoveryModule.py", domain]
        elif module_name == "jsrecon":
            cmd = ["python3", "jsrecon/jsDiscoveryModule.py", domain]
        elif module_name == "directory-discovery":
            cmd = ["python3", "directory-discovery/dirFuzzModule.py", domain]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            cprint(f"[-] Error running {module_name}: {result.stderr}", 'red')
            return None
            
        cprint(f"[+] {module_name} completed successfully", 'green')
        
        # Collect and move output files
        moved_files = collect_output_files(module_name, domain, output_dir)
        if not moved_files:
            cprint(f"[-] No output files found for {module_name}", 'yellow')
        
        return moved_files
        
    except Exception as e:
        cprint(f"[-] Error running {module_name}: {str(e)}", 'red')
        return None

def main():
    if len(sys.argv) < 2:
        cprint("Usage: python main.py <domain>", 'red')
        sys.exit(1)
    
    domain = sys.argv[1]
    print_banner()
    
    # Create timestamp-based output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join("outputs", f"{domain}_{timestamp}")
    os.makedirs(output_dir, exist_ok=True)
    
    cprint(f"[+] Starting recon for domain: {domain}", 'green')
    cprint(f"[+] Output directory: {output_dir}", 'green')
    
    # Run modules in sequence
    modules = ["urldiscovery", "jsrecon", "directory-discovery"]
    
    for module in modules:
        module_output = run_module(module, domain, output_dir)
        if not module_output:
            cprint(f"[-] Skipping remaining modules due to {module} failure", 'yellow')
            break
    
    # First extract secrets before merging URLs
    if extract_secrets(domain, output_dir):
        cprint("[+] Successfully extracted secrets", 'green')
    else:
        cprint("[-] Failed to extract secrets", 'red')
    
    # Then merge URL files
    if merge_urls_files(domain, output_dir):
        cprint("[+] Successfully merged URL files", 'green')
    else:
        cprint("[-] Failed to merge URL files", 'red')
    
    cprint("\n[+] Recon completed!", 'green')
    cprint(f"[+] Results saved in: {output_dir}", 'green')

if __name__ == "__main__":
    main() 