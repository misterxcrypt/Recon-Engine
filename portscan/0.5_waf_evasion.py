import json
import sys

# Evasion flags template for Nmap
evasion_template = {
    "decoys": ["RND:5"],      # random decoys
    "fragment": True,           # packet fragmentation
    "data_length": 25,          # pad packets
    "source_port": 53           # use DNS source port
}

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <domain-or-ip>")
        sys.exit(1)
    target = sys.argv[1]

    args = []
    if evasion_template.get("decoys"):
        args += ["-D"] + evasion_template["decoys"]
    if evasion_template.get("fragment"):
        args.append("-f")
    if evasion_template.get("data_length"):
        args += ["--data-length", str(evasion_template["data_length"])]
    if evasion_template.get("source_port"):
        args += ["--source-port", str(evasion_template["source_port"])]

    # Create output data
    output_data = {
        "target": target,
        "evasion_args": args
    }

    # Write to evasion.json
    with open('evasion.json', 'w') as f:
        json.dump(output_data, f, indent=2)

    print(f"WAF evasion configuration saved to evasion.json")