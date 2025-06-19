import subprocess
import json
import os

def run_nuclei(url, nuclei_output_file):
    print("[*] Running Nuclei...")
    try:
        subprocess.run(["nuclei", "-u", url, "-json-export", nuclei_output_file], check=True)
    except subprocess.CalledProcessError as e:
        print(f"[!] Error running nuclei: {e}")

def run_nikto(url, nikto_output_file):
    print("[*] Running Nikto...")
    try:
        subprocess.run(["nikto", "-url", url, "-Format", "json", ">", nikto_output_file], check=True)
    except subprocess.CalledProcessError as e:
        print(f"[!] Error running nikto: {e}")

def main():
    url = input("Enter the URL: ").strip()

    nuclei_output_file = "nuclei_result.json"
    nikto_output_file = "nikto_result.json"
    final_output_file = "combined_output.json"

    # Run both tools
    run_nuclei(url, nuclei_output_file)
    run_nikto(url, nikto_output_file)

    # Read nuclei result
    nuclei_data = []
    if os.path.exists(nuclei_output_file):
        with open(nuclei_output_file, "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        nuclei_data.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
        os.remove(nuclei_output_file)

    # Read nikto result
    nikto_data = {}
    if os.path.exists(nikto_output_file):
        with open(nikto_output_file, "r") as f:
            try:
                nikto_data = json.load(f)
            except json.JSONDecodeError:
                pass
        os.remove(nikto_output_file)

    # Merge into one JSON
    final_result = {
        "nuclei": nuclei_data,
        "nikto": nikto_data
    }

    # Save final result
    with open(final_output_file, "w") as f:
        json.dump(final_result, f, indent=4)

    print(f"[+] Combined output saved to {final_output_file}")

if __name__ == "__main__":
    main()
