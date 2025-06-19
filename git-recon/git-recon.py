#!/usr/bin/env python3

import subprocess
import json
import sys
from datetime import datetime

def run_trufflehog(repo_url):
    try:
        # Run trufflehog command
        command = f"sudo trufflehog github --repo {repo_url} --json"
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Error running trufflehog: {result.stderr}")
            return None
        
        # Parse the output as JSON
        output = result.stdout.strip()
        if not output:
            print("No results found")
            return None
            
        # Generate output filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"trufflehog_results_{timestamp}.json"
        
        # Write to JSON file
        with open(output_file, 'w') as f:
            f.write(output)
            
        print(f"Results saved to {output_file}")
        return output_file
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return None

def main():
    if len(sys.argv) > 1:
        repo_url = sys.argv[1]
    else:
        repo_url = input("Enter GitHub repository URL: ")
    
    if not repo_url:
        print("Repository URL cannot be empty")
        sys.exit(1)
    
    run_trufflehog(repo_url)

if __name__ == "__main__":
    main() 