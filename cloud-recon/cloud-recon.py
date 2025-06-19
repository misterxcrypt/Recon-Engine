#!/usr/bin/env python3

import subprocess
import sys
import json
import os
import re

def run_cloudbrute(domain, wordlist, keyword):
    try:
        # Construct the command
        command = [
            "cloudbrute",
            "-d", domain,
            "-w", wordlist,
            "-k", keyword,
            "-o", "output.txt"
        ]
        
        # Run the command and capture output
        result = subprocess.run(command, 
                              capture_output=True, 
                              text=True,
                              check=True)
        
        # Print the output
        print(result.stdout)
        if result.stderr:
            print("Errors:", result.stderr)
            
    except subprocess.CalledProcessError as e:
        print(f"Error running cloudbrute: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("Error: cloudbrute command not found. Please make sure it's installed and in your PATH.")
        sys.exit(1)

def process_output():
    try:
        # Check if output.txt exists
        if not os.path.exists("output.txt"):
            print("output.txt not found, creating empty result")
            with open("cloud-recon.json", "w") as f:
                json.dump({"message": "no output"}, f, indent=4)
            return

        # Read the output file
        with open("output.txt", "r") as f:
            lines = f.readlines()
        
        print("Processing output.txt...")
        print(f"Found {len(lines)} lines in output.txt")
        
        # Process each line and create JSON entries
        results = []
        for line in lines:
            # Skip empty lines
            if not line.strip():
                continue
                
            print(f"Processing line: {line.strip()}")
            
            # Try to extract code, status, and cloud using different patterns
            patterns = [
                r'(\d+):\s+(\w+)\s+-\s+(.+)',  # Pattern for "400: Protected - cloudname"
                r'(\d+)\s+(\w+)\s+-\s+(.+)',   # Pattern for "400 Protected - cloudname"
                r'WRN\s+(\d+):\s+(\w+)\s+-\s+(.+)',  # Pattern for "WRN 400: Protected - cloudname"
                r'INF\s+(\d+):\s+(\w+)\s+-\s+(.+)'   # Pattern for "INF 400: Protected - cloudname"
            ]
            
            for pattern in patterns:
                match = re.search(pattern, line)
                if match:
                    code = match.group(1)
                    status = match.group(2)
                    cloud = match.group(3)
                    
                    results.append({
                        "code": int(code),
                        "status": status,
                        "cloud": cloud
                    })
                    print(f"Found match: code={code}, status={status}, cloud={cloud}")
                    break
        
        if not results:
            print("Warning: No matches found in the output file")
            print("Raw output content:")
            with open("output.txt", "r") as f:
                print(f.read())
            # Create empty result
            with open("cloud-recon.json", "w") as f:
                json.dump({"message": "no output"}, f, indent=4)
            return
        
        # Write to JSON file
        with open("cloud-recon.json", "w") as f:
            json.dump(results, f, indent=4)
            
        print(f"Found {len(results)} valid entries")
        print("Results have been saved to cloud-recon.json")
        
        # Delete output.txt
        os.remove("output.txt")
        
    except Exception as e:
        print(f"Error processing output: {e}")
        # Create error result
        with open("cloud-recon.json", "w") as f:
            json.dump({"message": "no output"}, f, indent=4)
        sys.exit(1)

if __name__ == "__main__":
    # Default values
    domain = "flipkart.com"
    wordlist = "data/storage_small.txt"
    keyword = "flipkart"
    
    # Run cloudbrute
    run_cloudbrute(domain, wordlist, keyword)
    
    # Process the output
    process_output()
