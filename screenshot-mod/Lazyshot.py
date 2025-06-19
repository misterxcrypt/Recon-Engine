#!/usr/bin/env python3
import sys
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from urllib.parse import urlparse
from termcolor import cprint
import json
import time

OUTPUT_DIR = 'outputs'

cprint(r"""
--------------------------------------
      LazyShot - Screenshot Tool
--------------------------------------
""", 'cyan')


def parse_url(url):
    parsed = urlparse(url.strip())
    if parsed.scheme in ('http', 'https'):
        return url.strip()
    elif parsed.path:
        return 'http://' + parsed.path
    return None


def take_screenshot(url, output_dir):
    normalized = parse_url(url)
    if not normalized:
        return False

    cprint(f"[DEBUG] Processing: {normalized}", 'yellow')
    os.makedirs(output_dir, exist_ok=True)

    chrome_opts = Options()
    chrome_opts.add_argument("--headless=new")
    chrome_opts.add_argument("--disable-gpu")
    chrome_opts.add_argument("--no-sandbox")
    chrome_opts.add_argument("--window-size=1280,1024")

    # 👇 Tell Selenium to use the headless shell instead of Chrome
    chrome_opts.binary_location = "chromedriver"

    service = Service()  # No executable_path needed here

    driver = webdriver.Chrome(service=service, options=chrome_opts)
    driver.get(normalized)
    time.sleep(5)

    parsed = urlparse(normalized)
    filename = f"screenshot-{parsed.netloc.replace('.', '_')}.png"
    filepath = os.path.join(output_dir, filename)
    driver.save_screenshot(filepath)
    driver.quit()

    cprint(f"[✓] Saved screenshot: {filepath}", 'green')
    return True


def main():
    if len(sys.argv) < 2:
        cprint("Usage: python Lazyshot.py <input.json> [--out folder]", 'red')
        sys.exit(1)

    input_file = sys.argv[1]
    if '--out' in sys.argv:
        idx = sys.argv.index('--out')
        if idx + 1 < len(sys.argv):
            global OUTPUT_DIR
            OUTPUT_DIR = sys.argv[idx + 1]

    try:
        # Read and parse the JSON file
        with open(input_file, 'r') as f:
            data = json.load(f)
            
        # Get URLs from the 'alive' array
        if 'alive' not in data:
            cprint("ERROR: No 'alive' array found in the JSON file", 'red')
            sys.exit(1)
            
        # Extract URLs from the 'url' field of each item in the 'alive' array
        urls = [item['url'] for item in data['alive'] if 'url' in item]
        
        if not urls:
            cprint("WARNING: No valid URLs found in the 'alive' array", 'yellow')
            sys.exit(0)
            
        cprint(f"[+] Found {len(urls)} URLs to process", 'green')
        
    except json.JSONDecodeError:
        cprint(f"ERROR: Invalid JSON file {input_file}", 'red')
        sys.exit(1)
    except IOError:
        cprint(f"ERROR: Could not read file {input_file}", 'red')
        sys.exit(1)
    except KeyError as e:
        cprint(f"ERROR: Missing required field in JSON: {str(e)}", 'red')
        sys.exit(1)

    # Process each URL
    for url in urls:
        take_screenshot(url, OUTPUT_DIR)


if __name__ == "__main__":
    main()
