#!/usr/bin/env python3
import subprocess
import json
import sys
import argparse
import random

def discover_open_ports(target, full=False):
    """Use Naabu to list open ports (top 100 by default, or full range)."""
    cmd = ["naabu", "-host", target, "-silent", "-json"]
    if full:
        cmd += ["-p", "-"]
    else:
        cmd += ["-tp", "100"]
    
    print(f"Running command: {' '.join(cmd)}")  # Debug: Print the command being run
    
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    ports = []
    
    # Read stdout and check for data
    for line in proc.stdout:
        print(f"Raw output line: {line.strip()}")  # Debug: Print raw output
        if line.strip():
            try:
                data = json.loads(line)
                port = int(data["port"])
                ports.append(port)
                print(f"Found port: {port}")  # Debug: Print each found port
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON: {e}")
            except KeyError as e:
                print(f"Missing port in data: {e}")
            except Exception as e:
                print(f"Unexpected error: {e}")

    # Check stderr for any errors
    stderr = proc.stderr.read()
    if stderr:
        print(f"Error output: {stderr}")

    proc.wait()
    
    if not ports:
        print("Warning: No ports were found!")
        
    return sorted(set(ports))

# def find_closed_ports_nmap(target, open_ports, max_closed=5):
#     """
#     Randomly sample ports from 1024–65535 (User & Ephemeral ranges) :contentReference[oaicite:1]{index=1},
#     skip any in open_ports, and test with Nmap until we gather max_closed ports.
#     """
#     # Build candidate list excluding open ports and well‑known ports (0–1023) :contentReference[oaicite:2]{index=2}
#     candidates = [p for p in range(1024, 65536) if p not in open_ports]
#     random.shuffle(candidates)
#     closed = []

#     for port in candidates:
#         cmd = ["nmap", "-Pn", "-p", str(port), target, "-oX", "-"]
#         out = subprocess.run(cmd, capture_output=True, text=True).stdout
#         if f'portid="{port}"' in out and 'state="closed"' in out:
#             closed.append(port)
#             if len(closed) >= max_closed:
#                 break

#     return closed

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Discover open ports and any 5 closed ports.")
    parser.add_argument('target', help='Domain or IP to scan')
    parser.add_argument('--full', action='store_true', help='Scan all ports (slower)')
    args = parser.parse_args()

    open_ports = discover_open_ports(args.target, full=args.full)
    
    # Create output data
    output_data = {
        "target": args.target,
        "open_ports": open_ports
    }
    
    # Write to ports.json
    with open('ports.json', 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"Scan results saved to ports.json")
