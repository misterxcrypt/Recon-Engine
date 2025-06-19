import subprocess
import json
import sys

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <ports.json>")
        sys.exit(1)
    data = json.load(open(sys.argv[1]))
    target = data["target"]
    http_ports = data.get("open_ports", [])

    if not http_ports:
        output_data = {"target": target, "http": {}}
        with open('httpx_tech.json', 'w') as f:
            json.dump(output_data, f, indent=2)
        print("No HTTP ports found. Empty results saved to httpx_tech.json")
        sys.exit(0)

    port_list = ",".join(map(str, http_ports))
    cmd = [
        "httpx", "-u", target,
        "-p", port_list,
        "-title", "-status-code", "-server", "-tech-detect", "-follow-redirects", "-json", "-no-fallback"
    ]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    http_info = {}
    for line in proc.stdout:
        try:
            rec = json.loads(line)
            p = int(rec["port"])
            title = rec.get("title")
            if title == "Loading":
                title = None
            http_info[p] = {
                "status_code": rec.get("status_code"),
                "title": title,
                "server": rec.get("server"),
                "tech": rec.get("tech", [])
            }
        except:
            continue
    proc.wait()

    # Create output data
    output_data = {
        "target": target,
        "http": http_info
    }

    # Write to httpx_tech.json
    with open('httpx_tech.json', 'w') as f:
        json.dump(output_data, f, indent=2)

    print(f"HTTP technology scan results saved to httpx_tech.json")