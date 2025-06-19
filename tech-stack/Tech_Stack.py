#!/usr/bin/env python3
"""
This script wraps ProjectDiscovery's `fingerprintx` CLI and uses Wappalyzer to detect technologies
used by alive HTTP/HTTPS services. It scans one or more host:port targets and outputs the
consolidated results as JSON to a local file.

Usage:
  python Tech_Stack.py <host:port> -o <name.json>

Examples:
  python3 Tech_Stack.py sbi.co.in:443 -o full_tech_results.json
  python3 Tech_Stack.py sbi.co.in:443, exampleDomain:port -o full_tech_results.json
"""
import subprocess
import json
import sys
import argparse
import httpx
import warnings
from urllib.parse import urlparse
from Wappalyzer import Wappalyzer, WebPage

# Suppress Wappalyzer regex warnings
warnings.filterwarnings("ignore", category=UserWarning)

def is_alive(url):
    try:
        r = httpx.get(url, timeout=10, follow_redirects=True)
        return r.status_code < 400, r.status_code
    except httpx.RequestError as e:
        return False, str(e)

def detect_tech_stack(url):
    result = {
        "url": url,
        "alive": False,
        "status": None,
        "technologies": [],
        "error": None
    }

    try:
        if not url.startswith("http"):
            url = "https://" + url
        result["url"] = url

        alive, status = is_alive(url)
        result["alive"] = alive
        result["status"] = status

        if not alive:
            return result

        webpage = WebPage.new_from_url(url)
        wappalyzer = Wappalyzer.latest()
        technologies = wappalyzer.analyze(webpage)
        result["technologies"] = sorted(list(technologies))

    except Exception as e:
        result["error"] = str(e)

    return result

def run_fingerprintx(target: str, verbose: bool = False, include_unknown: bool = False):
    cmd = ["fingerprintx", "--json", "-t", target]
    if verbose:
        cmd.append("-v")
    if include_unknown:
        cmd.append("-U")

    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        out, err = proc.communicate()
    except FileNotFoundError:
        print("Error: fingerprintx binary not found in PATH.", file=sys.stderr)
        sys.exit(1)

    if proc.returncode != 0:
        print(f"[!] fingerprintx failed for {target} (exit {proc.returncode}).", file=sys.stderr)
        print(err, file=sys.stderr)
        return []

    results = []
    for line in out.splitlines():
        if not line.strip():
            continue
        try:
            results.append(json.loads(line))
        except json.JSONDecodeError:
            print(f"[!] JSON parse error for line: {line}", file=sys.stderr)
    return results

def hostport_to_url(hostport: str):
    host, port = hostport.split(":")
    scheme = "https" if port == "443" else "http"
    return f"{scheme}://{host}"

def main():
    parser = argparse.ArgumentParser(
        description="Wrap fingerprintx CLI + Wappalyzer and write JSON results to a local file.")
    parser.add_argument(
        "-j", "--json",
        dest="json_file",
        help="JSON file containing subdomain scan results")
    parser.add_argument(
        "-o", "--output",
        dest="output",
        help="File to write JSON array. Defaults to tech_stack_results.json in CWD.")
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Pass -v for verbose fingerprintx output.")
    parser.add_argument(
        "-U", "--include-unknown",
        action="store_true",
        help="Include unknown fingerprints (pass -U to fingerprintx).")

    args = parser.parse_args()

    if not args.json_file:
        parser.error("No JSON file provided. Use -j/--json to specify the input JSON file.")

    try:
        with open(args.json_file, 'r') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error reading JSON file: {e}", file=sys.stderr)
        sys.exit(1)

    if 'alive' not in data:
        print("Error: 'alive' array not found in JSON file", file=sys.stderr)
        sys.exit(1)

    # Extract URLs from alive array
    targets = []
    for item in data['alive']:
        url = item['url']
        # Convert URL to host:port format
        parsed = urlparse(url)
        port = "443" if parsed.scheme == "https" else "80"
        target = f"{parsed.netloc}:{port}"
        targets.append(target)

    all_results = []
    for target in targets:
        print(f"[*] Scanning {target}...", file=sys.stderr)
        fingerprintx_data = run_fingerprintx(target, verbose=args.verbose, include_unknown=args.include_unknown)
        url = hostport_to_url(target)
        tech_data = detect_tech_stack(url)

        all_results.append({
            "target": target,
            "fingerprintx": fingerprintx_data,
            "wappalyzer": tech_data
        })

    output_file = args.output if args.output else 'tech_stack_results.json'

    try:
        with open(output_file, 'w') as f:
            json.dump(all_results, f, indent=2)
        print(f"[+] Results written to {output_file}")
    except IOError as e:
        print(f"Error writing to {output_file}: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
