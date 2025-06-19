#!/usr/bin/env python3
import subprocess
import json
import sys
import os
import time
import argparse

def run_command(command, description):
    """Run a command and handle its execution"""
    print(f"\n[+] {description}...")
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running {command[0]}: {e}", file=sys.stderr)
        sys.exit(1)

def merge_results(target):
    """Merge all JSON files into a single comprehensive result"""
    result = {"target": target}
    
    # Read ports.json
    with open('ports.json') as f:
        ports_data = json.load(f)
        result["open_ports"] = ports_data["open_ports"]
    
    # Read httpx_tech.json
    with open('httpx_tech.json') as f:
        http_data = json.load(f)
        result["http_tech"] = http_data["http"]
    
    # Read deepnmap.json
    with open('deepnmap.json') as f:
        nmap_data = json.load(f)
        result["services"] = nmap_data["services"]
        result["os"] = nmap_data["os"]
    
    return result

def cleanup_files():
    """Remove intermediate JSON files"""
    files_to_delete = ['ports.json', 'evasion.json', 'deepnmap.json', 'httpx_tech.json']
    for file in files_to_delete:
        try:
            os.remove(file)
            print(f"Cleaned up {file}")
        except FileNotFoundError:
            pass

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Complete reconnaissance of a target")
    parser.add_argument('target', help='Domain or IP to scan')
    parser.add_argument('--full', action='store_true', help='Perform full port scan (slower)')
    args = parser.parse_args()
    
    # Step 1: Port Scanning
    port_scan_cmd = ["python3", "1_port_scan.py", args.target]
    if args.full:
        port_scan_cmd.append("--full")
    run_command(port_scan_cmd, "Scanning ports" + (" (full scan)" if args.full else ""))
    
    # Step 2: WAF Evasion Configuration
    run_command(["python3", "0.5_waf_evasion.py", args.target], "Generating WAF evasion configuration")
    
    # Step 3: Deep Nmap Scan (requires sudo)
    if os.geteuid() != 0:
        print("Error: This script requires root privileges for Nmap OS detection", file=sys.stderr)
        sys.exit(1)
    run_command(["python3", "3_nmap_deep.py", "ports.json", "evasion.json"], "Running deep Nmap scan")
    
    # Step 4: HTTP Technology Enumeration
    run_command(["python3", "2_httpx_enrich.py", "ports.json"], "Enumerating HTTP technologies")
    
    # Merge all results
    print("\n[+] Merging results...")
    final_result = merge_results(args.target)
    
    # Save final result
    output_file = f"recon_{args.target}.json"
    with open(output_file, 'w') as f:
        json.dump(final_result, f, indent=2)
    
    # Cleanup intermediate files
    cleanup_files()
    
    print(f"\n[+] Reconnaissance complete! Results saved to {output_file}") 