PLANNED MODULES:
Whois
Subdomain Enumeration-Active & Passive
Alive URL check
Technology Identification
DNS
WAF
Port Scan
URL Discovery
Param Discovery
JS Discovery
Directory Discovery
CMS
OSINT
Github
Cloud Assets
Screenshot
Vulnerability Scan

OUR MODULES:
1. subdomain-recon (INPUT: DOMAIN) (OUTPUT: ALIVE-SUBDOMAINS)
2. tech-stack (INPUT: ALIVE-SUBDOMAINS) (OUTPUT: TECHSTACK)
3. screenshot-mod (INPUT: ALIVE-SUBDOMAINS) (OUTPUT: SCREENSHOTS)
4. Discovery (INPUT: DOMAIN) (OUTPUT: URLS & SECRETS)
    -> urldiscovery (INPUT: DOMAIN) (OUTPUT: URLS)
    -> jsrecon (INPUT: DOMAIN) (OUTPUT: URLS & SECRETS)
    -> directory-discovery (INPUT: DOMAIN) (OUTPUT: URLS)
5. portscan (INPUT: DOMAIN) (OUTPUT: OPEN-PORTS)
6. cloud-recon (INPUT: DOMAIN) (OUTPUT: CLOUD-ASSET)
7. git-recon (INPUT: GIT-REPO) (OUTPUT: GIT-SECRETS)
8. waf-detector (INPUT: DOMAIN) (OUTPUT: WAF)
9. cms-recon (INPUT: DOMAIN) (OUTPUT: Vulnerability report)
10. vulnscan (INPUT: DOMAIN) (OUTPUT: Vulnerabiltiy report)

Current workflow:
1. Get Domain Input from the user.
2. Run Subdomain Enumeration (subdomain-recon module) 
3. After getting Subdomains, Run alive check on them and get alive subdomains (subdomain-recon module)
4. Input the Alive subdomains into tech stack module and find tech stack for each subdomains (subdomain-recon module)
5. Input the Alive Subdomains into screenshot module (screenshot-mod module)
5. Parallely, after step 1, Run The below modules.
6. Run URL Discovery to collect all endpoints from the actual domain (urldiscovery module)
7. Run JS Discovery to collect JS files and any secrets in JS files. (jsrecon module)
8. Run Directory Discovery to collect all directories from the actual domain (directory-discovery module)
9. Run Cloud Assets on domain (cloud-recon module)
11. Run Port Scan for the domain (portscan module)
12. Run CMS Recon for the domain (cms-recon module)
13. Run Vulnerabiltiy Scanning using nikto and nuclei for the domain (vulnscan module)
14. Get Github Repo from the user.
15. Run Git Recon on the input repo (git-recon module)
16. Now The assets we collected
    - Subdomains
    - Tech stack of each subdomains
    - Screenshots of each subdomains
    - URL Endpoints - directories, JS, json, css, ts, html, php endpoints
    - Cloud assets - input domain
    - git asset - input git repo
    - Waf detector - input domain
    - Open ports - input domain
    - Vulnerability report - input domain

FILTERING OPTIONS:
1. Have grep functions to find URLs of similar kind like finding admin panels, login pages.

FUTURE PLAN:
1	portscan INPUT: ALIVE-SUBDOMAINS - Subdomains may resolve to different IPs and ports.
2	jsrecon	INPUT: DOMAIN + ALIVE-SUBDOMAINS - JS files may be hosted per-subdomain.
3	directory-discovery	INPUT: ALIVE-SUBDOMAINS	- Each subdomain might have different directories.
4	waf-detector INPUT: ALIVE-SUBDOMAINS - WAFs can be subdomain-specific.