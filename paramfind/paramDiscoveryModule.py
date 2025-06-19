import subprocess
import json
import re
import os

def x8_scan(url):
    command = ["x8", "-u", url, "-w", "burp-parameter-names.txt", "-O", "json", "-o", "x8_output.json"]
    
    # Use Popen to get real-time output
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,  # Line buffered
        universal_newlines=True
    )
    
    # Wait for the process to complete
    process.wait()
    
    # Read the JSON output file
    try:
        with open("x8_output.json", "r") as f:
            x8_results = json.load(f)
    except FileNotFoundError:
        print("Error: x8_output.json not found")
        x8_results = []
    except json.JSONDecodeError:
        print("Error: Invalid JSON in x8_output.json")
        x8_results = []
    
    # Delete the x8_output.json file
    try:
        os.remove("x8_output.json")
    except OSError as e:
        print(f"Error deleting x8_output.json: {e}")
    
    return x8_results

def arjun_scan(url):
    command = ["arjun", "-u", url]
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    output = result.stdout

    extracted_params = []
    detected_params = []

    match = re.search(r"Extracted \d+ parameters from response for testing: (.+)", output)
    if match:
        param_list = match.group(1)
        extracted_params = [p.strip() for p in param_list.split(",") if p.strip()]

    detected = re.findall(r"parameter detected: (\w+)", output)
    if detected:
        detected_params = detected

    return extracted_params, detected_params

def main():
    url = input("Enter the target URL: ").strip()

    x8_results = x8_scan(url)
    arjun_extracted, arjun_detected = arjun_scan(url)

    final_result = {
        "x8_results": x8_results,
        "arjun_extracted_parameters": arjun_extracted,
        "arjun_detected_parameters": arjun_detected
    }

    with open("combined_results.json", "w") as f:
        json.dump(final_result, f, indent=4)
    
    print("[+] Results saved to combined_results.json")

if __name__ == "__main__":
    main()
