import random
import requests
from urllib.parse import urlparse, urlencode
import sys
import os
import json

# Add wafw00f to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

# Import wafw00f engine
from wafw00f.main import WAFW00F

# Common WAF signatures
WAF_SIGNATURES = {
    "Cloudflare": ["cf-ray", "__cfduid", "cloudflare"],
    "Akamai": ["akamai", "akamai-bot", "akamai-ghost"],
    "Sucuri": ["x-sucuri-id", "x-sucuri-block"],
    "Imperva": ["incapsula", "x-cdn"],
    "F5 BIG-IP": ["bigipserver", "f5"],
    "AWS WAF": ["aws"],
    "Barracuda": ["barracuda"],
    "DenyALL": ["denyall"],
    "Cisco ACE": ["cisco-ace"],
    "FortiWeb": ["fortiweb"],
    "360 Web Application Firewall": ["wzws-rsid"],
}

# Payloads for attack simulation
XSS_PAYLOAD = r'<script>alert("XSS");</script>'
SQLI_PAYLOAD = r'UNION SELECT ALL FROM information_schema AND " or SLEEP(5) or "'
LFI_PAYLOAD = r'../../etc/passwd'
RCE_PAYLOAD = r'/bin/cat /etc/passwd; ping 127.0.0.1; curl google.com'
XXE_PAYLOAD = r'<!ENTITY xxe SYSTEM "file:///etc/shadow">]><pwn>&hack;</pwn>'


def create_random_param_name():
    return "param" + str(random.randint(1000, 9999))


def send_request(url, headers=None, params=None, path_suffix=""):
    try:
        parsed_url = urlparse(url)
        full_path = parsed_url.path + path_suffix
        full_url = f"{parsed_url.scheme}://{parsed_url.netloc}{full_path}"
        if params:
            full_url += "?" + urlencode(params)
        return requests.get(full_url, headers=headers, timeout=10)
    except:
        return None


def basic_waf_fingerprint(response):
    waf_found = []
    for waf_name, indicators in WAF_SIGNATURES.items():
        for header_key, header_val in response.headers.items():
            lower_key = header_key.lower()
            lower_val = header_val.lower()
            for indicator in indicators:
                if indicator in lower_key or indicator in lower_val:
                    waf_found.append(waf_name)
    return set(waf_found)


def generic_detection(url):
    print("[+] Performing active WAF detection using payload comparison...")

    base_headers = {'User-Agent': 'Mozilla/5.0'}
    resp_normal = send_request(url, headers=base_headers)
    if not resp_normal:
        print("[!] Normal request failed. Target may be blocking connections.")
        return True  # Assume WAF-like behavior if base request fails

    normal_code = resp_normal.status_code
    waf_behavior = False

    checks = [
        ("XSS", {create_random_param_name(): XSS_PAYLOAD}, "", XSS_PAYLOAD),
        ("SQLi", {create_random_param_name(): SQLI_PAYLOAD}, "", SQLI_PAYLOAD),
        ("LFI", None, "/" + LFI_PAYLOAD, LFI_PAYLOAD),
        ("XXE", {create_random_param_name(): XXE_PAYLOAD}, "", XXE_PAYLOAD),
        ("RCE", {create_random_param_name(): RCE_PAYLOAD}, "", RCE_PAYLOAD),
    ]

    for attack_type, params, suffix, payload in checks:
        resp_attack = send_request(url, headers=base_headers, params=params, path_suffix=suffix)
        if resp_attack and resp_attack.status_code != normal_code:
            print(f"[!] WAF Behavior Detected on {attack_type} Payload (status code changed: {normal_code} -> {resp_attack.status_code})")
            waf_behavior = True
        elif not resp_attack:
            print(f"[!] {attack_type} request blocked or dropped entirely. Possible WAF behavior. {url} {base_headers} {params} {suffix} ")
            waf_behavior = True

    # User-Agent removal check
    headers_ua_removed = base_headers.copy()
    headers_ua_removed.pop("User-Agent")
    resp_no_ua = send_request(url, headers=headers_ua_removed)
    if resp_no_ua and resp_no_ua.status_code != normal_code:
        print("[!] WAF Behavior Detected on User-Agent removal (status code differs)")
        waf_behavior = True

    return waf_behavior

def wafw00f_detect(url):
    print("[+] Running wafw00f engine...")
    waf_engine = WAFW00F(url)
    result = waf_engine.identwaf()

    if result:
        wafs_detected, final_url = result

        if wafs_detected:
            print(f"[!] wafw00f Detected WAF(s): {', '.join(wafs_detected)}")
        else:
            print("[+] wafw00f did not detect any WAF.")
            print(f"[~] Final URL tested: {final_url}")

        return wafs_detected

def detect_waf(url):
    print(f"[+] Sending initial request to {url}")
    detection_result = {
        "url": url,
        "waf_detected": None,
        "detection_method": None,
        "waf_behavior": False
    }

    try:
        response = requests.get(url, timeout=10)
        wafs = basic_waf_fingerprint(response)
        if wafs:
            print(f"[!] Passive WAF Detection: {wafs}")
            print("[+] Skipping active detection since WAF type is identified via headers.")
            detection_result["waf_detected"] = list(wafs)
            detection_result["detection_method"] = "passive"
        else:
            print("[+] No known WAF headers detected. Proceeding with wafw00f and active detection...")

            # Run wafw00f
            wafw00f_result = wafw00f_detect(url)

            if wafw00f_result and len(wafw00f_result) > 0:
                detection_result["waf_detected"] = list(wafw00f_result)
                detection_result["detection_method"] = "wafw00f"
                print("[+] Skipping generic active detection since wafw00f identified WAF.")
            else:
                print("[+] wafw00f did not detect WAF. Running custom active detection...")
                if generic_detection(url):
                    print("[!] WAF behavior detected, but specific WAF vendor is unknown.")
                    detection_result["waf_detected"] = "unknown"
                    detection_result["detection_method"] = "generic"
                    detection_result["waf_behavior"] = True
                else:
                    print("[+] No WAF behavior observed.")
                    detection_result["waf_detected"] = "none"
                    detection_result["detection_method"] = "none"
    except requests.exceptions.RequestException as e:
        print(f"[!] Error connecting: {e}")
        detection_result["error"] = str(e)

    print("\n=== JSON Output ===")
    print(json.dumps(detection_result, indent=4))

if __name__ == "__main__":
    target_url = input("Enter target URL (with http/https): ").strip()
    detect_waf(target_url)
