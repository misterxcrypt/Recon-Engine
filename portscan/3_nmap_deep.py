#!/usr/bin/env python3
import json
import sys
import os
import nmap

# Ensure python‑nmap is installed
try:
    import nmap
except ImportError:
    print("Missing dependency: Install python‑nmap in your venv:\n"
          "  source venv/bin/activate && pip install python‑nmap")
    sys.exit(1)

# Require root for OS detection and raw packet probes
if os.geteuid() != 0:
    print("Error: This script requires root privileges for OS detection", file=sys.stderr)
    sys.exit(1)

if len(sys.argv) != 3:
    print(f"Usage: {sys.argv[0]} <ports.json> <evasion.json>")
    sys.exit(1)

# Load inputs
ports_data  = json.load(open(sys.argv[1]))
evasion     = json.load(open(sys.argv[2]))
target      = ports_data["target"]
open_ports  = ports_data.get("open_ports", [])
# closed_port = ports_data.get("closed_port")

# Build port list (open + one closed for fingerprinting)
scan_ports = list(open_ports)
# if closed_port:
#     scan_ports.append(closed_port)
port_str = ",".join(map(str, scan_ports))

# Compose Nmap arguments:
# - TCP+UDP handshake, version & OS detection
# - --version-all for thorough probes :contentReference[oaicite:3]{index=3}
# - Run SSL/HTTP NSE scripts for extra banner info :contentReference[oaicite:4]{index=4}
# - --resolve-all to scan every IP for multi‑A records :contentReference[oaicite:5]{index=5}
base_args = [
    "-Pn", "-sSU", "-sV", "--version-all",
    "--version-intensity", "2", "--osscan-guess", "-O",
    "--script", "ssl-cert,http-headers,http-title",
    "--resolve-all"
]
args = evasion.get("evasion_args", []) + base_args

scanner = nmap.PortScanner()
# FIX: use 'hosts=' parameter (IP) 
scanner.scan(hosts=target, ports=port_str, arguments=" ".join(args))

# Retrieve the actual host IP used in scan
hosts = scanner.all_hosts()
if not hosts:
    print(f"No hosts found for {target}", file=sys.stderr)
    sys.exit(1)
host = hosts[0]  # first IP

# Collect service/version info
services = []
for p in open_ports:
    info = scanner[host]["tcp"].get(p, {})
    services.append({
        "port":      p,
        "service":   info.get("name"),      # e.g., http, ssh
        "product":   info.get("product"),   # e.g., Apache, OpenSSH
        "version":   info.get("version"),   # e.g., 2.4.46
        "extrainfo": info.get("extrainfo")  # additional details
    })

# Collect OS fingerprint
os_info = {}
matches = scanner[host].get("osmatch", [])
if matches:
    best = matches[0]
    os_info = {
        "name":     best.get("name"),      # e.g., Linux 3.X
        "accuracy": best.get("accuracy")   # e.g., 98%
    }

# Output JSON report
output_data = {
    "target":   target,
    "services": services,
    "os":       os_info
}

# Write to deepnmap.json
with open('deepnmap.json', 'w') as f:
    json.dump(output_data, f, indent=2)

print(f"Deep scan results saved to deepnmap.json")
