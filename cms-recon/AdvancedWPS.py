#!/usr/bin/env python3
import argparse
import subprocess
import json
import sys
import os
import re
from datetime import datetime
from urllib.parse import urlparse
import requests
from typing import List, Dict

API_TOKEN = "BOPD6V1PDhIlFd73KI4jW3XwzacNIIQmopUG5CPuSFE"
OUTPUT_DIR = 'wpscan_reports'
THROTTLE = 1
ENUM_OPTS = ['p', 't', 'u', 'tt', 'm', 'cb', 'dbe']
CLEAR_LOCAL_CACHE = True

def normalize_url(domain: str) -> str:
    if not domain.startswith(('http://', 'https://')):
        domain = 'https://' + domain
    return domain.rstrip('/')

def get_wpscan_version() -> str:
    try:
        proc = subprocess.run(['wpscan', '--version'], capture_output=True, text=True)
        if proc.returncode == 0:
            return proc.stdout.splitlines()[0]
    except Exception:
        pass
    return 'unknown'

def is_wordpress(url: str, timeout: float = 10.0) -> bool:
    try:
        resp = requests.get(url, timeout=timeout, allow_redirects=True)
        html = resp.text.lower()
        if 'wp-content' in html or 'wp-includes' in html:
            return True
        head = requests.head(url, timeout=timeout, allow_redirects=True)
        if 'x-pingback' in head.headers:
            return True
        login = requests.get(f'{url}/wp-login.php', timeout=timeout)
        if login.status_code == 200 and 'wordpress' in login.text.lower():
            return True
    except requests.RequestException:
        pass
    return False

def fallback_fingerprint(url: str) -> dict:
    info = {}
    try:
        resp = requests.get(url, timeout=10)
        html = resp.text
        match = re.search(r'<!--\s*This site is optimized with the Yoast SEO plugin v([\d\.]+)', html)
        if match:
            info['yoast_version'] = match.group(1)
        meta = re.search(r'<meta name="generator" content="WordPress\s*([\d\.]+)"', html, re.IGNORECASE)
        if meta:
            info['meta_generator'] = meta.group(1)
    except Exception:
        pass
    try:
        head = requests.head(url, timeout=10, allow_redirects=True)
        if 'x-pingback' in head.headers:
            info['x_pingback'] = head.headers.get('x-pingback')
    except Exception:
        pass
    return info

def run_wpscan(url: str, use_random_ua: bool = False) -> dict:
    cmd = [
        './wpscan',
        '--url', url,
        '--api-token', API_TOKEN,
        '--no-banner',
        '--format', 'json'
    ]
    if ENUM_OPTS:
        cmd.extend(['--enumerate', ','.join(ENUM_OPTS)])
    if CLEAR_LOCAL_CACHE:
        cmd.append('--clear-cache')
    if THROTTLE is not None:
        cmd.extend(['--throttle', str(THROTTLE)])
    if use_random_ua:
        cmd.append('--random-user-agent')

    proc = subprocess.run(cmd, capture_output=True, text=True)
    result = {}
    if proc.returncode != 0:
        try:
            details = proc.stderr.strip() or proc.stdout.strip()
            result = json.loads(details)
            if 'scan_aborted' in result and '403' in result['scan_aborted'] and not use_random_ua:
                return run_wpscan(url, use_random_ua=True)
        except Exception:
            result = {
                'error': f'WPScan failed (exit code {proc.returncode})',
                'details': proc.stderr.strip() or proc.stdout.strip()
            }
    else:
        try:
            result = json.loads(proc.stdout)
        except json.JSONDecodeError:
            result = {'error': 'Failed to parse WPScan output', 'details': proc.stdout.strip()}
    return result

def scan_domain(domain: str, wpscan_version: str) -> dict:
    normalized = normalize_url(domain)
    report = {'domain': domain, 'is_wordpress': False, 'wpscan_version': wpscan_version}

    if not is_wordpress(normalized):
        report['message'] = 'Not a WordPress-based domain'
        return report

    report['is_wordpress'] = True
    cms_info = run_wpscan(normalized)
    report['cms_info'] = cms_info
    if isinstance(cms_info, dict) and ('scan_aborted' in cms_info or cms_info.get('error')):
        report['fallback_info'] = fallback_fingerprint(normalized)
    return report

def save_report(data: dict, domain: str):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    safe = domain.replace('https://', '').replace('http://', '').replace('/', '_')
    path = os.path.join(OUTPUT_DIR, f'{safe}_{timestamp}.json')
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)
    print(f'[+] Report saved: {path}')

def run_scan(domains: List[str]) -> List[Dict]:
    results = []
    wpscan_version = get_wpscan_version()
    for d in domains:
        print(f'[*] Scanning: {d}')
        rpt = scan_domain(d, wpscan_version)
        results.append(rpt)
    return results

def main():
    parser = argparse.ArgumentParser(description='Check domains for WordPress & scan with WPScan.')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-d', '--domains', nargs='+', help='Domains to scan')
    group.add_argument('-f', '--file', help='File with domains, one per line')
    args = parser.parse_args()

    domains = args.domains if args.domains else []
    if args.file:
        try:
            with open(args.file) as fh:
                domains.extend([l.strip() for l in fh if l.strip()])
        except Exception as e:
            print(f'Error reading file: {e}', file=sys.stderr)
            sys.exit(1)

    results = run_scan(domains)
    for res in results:
        save_report(res, res.get('domain', 'unknown'))

if __name__ == '__main__':
    main()
