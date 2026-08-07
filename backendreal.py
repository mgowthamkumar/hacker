from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pathlib import Path
import os
import requests

app = FastAPI()
BASE_DIR = Path(__file__).resolve().parent

# Allow your HTML file to communicate with this Python server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

ADZUNA_APP_ID = "d1f4b68d"
ADZUNA_APP_KEY = "e5ffc11dd8e1b50c11a3b48cfa7149b7"
COUNTRY_CODE = "in"

COMPANY_CAREER_LINKS = [
    ("Google", "https://careers.google.com/"),
    ("Microsoft", "https://careers.microsoft.com/"),
    ("Amazon", "https://www.amazon.jobs/"),
    ("Apple", "https://www.apple.com/careers/"),
    ("Meta", "https://www.metacareers.com/"),
    ("Netflix", "https://jobs.netflix.com/"),
    ("NVIDIA", "https://nvidia.wd5.myworkdayjobs.com/NVIDIAExternalCareerSite"),
    ("Intel", "https://jobs.intel.com/"),
    ("IBM", "https://www.ibm.com/careers/"),
    ("Oracle", "https://www.oracle.com/careers/"),
    ("Adobe", "https://careers.adobe.com/"),
    ("Salesforce", "https://www.salesforce.com/company/careers/"),
    ("Cisco", "https://jobs.cisco.com/"),
    ("Dell Technologies", "https://jobs.dell.com/"),
    ("HP", "https://jobs.hp.com/"),
    ("Qualcomm", "https://www.qualcomm.com/company/careers"),
    ("AMD", "https://careers.amd.com/"),
    ("Broadcom", "https://www.broadcom.com/company/careers"),
    ("VMware", "https://careers.vmware.com/"),
    ("SAP", "https://www.sap.com/about/careers.html"),
    ("ServiceNow", "https://careers.servicenow.com/"),
    ("Workday", "https://www.workday.com/en-us/company/careers.html"),
    ("Atlassian", "https://www.atlassian.com/company/careers"),
    ("Shopify", "https://www.shopify.com/careers"),
    ("HubSpot", "https://www.hubspot.com/careers"),
    ("Slack", "https://slack.com/careers"),
    ("Zoom", "https://careers.zoom.us/"),
    ("Dropbox", "https://jobs.dropbox.com/"),
    ("GitHub", "https://www.github.careers/"),
    ("GitLab", "https://about.gitlab.com/handbook/hiring/"),
    ("Red Hat", "https://www.redhat.com/en/jobs"),
    ("Docker", "https://www.docker.com/careers/"),
    ("Cloudflare", "https://www.cloudflare.com/careers/"),
    ("Datadog", "https://careers.datadoghq.com/"),
    ("Snowflake", "https://careers.snowflake.com/"),
    ("Databricks", "https://www.databricks.com/company/careers"),
    ("Palantir", "https://www.palantir.com/careers/"),
    ("Stripe", "https://stripe.com/jobs"),
    ("PayPal", "https://www.paypal.com/us/brc/"),
    ("Block", "https://block.xyz/careers"),
    ("Coinbase", "https://www.coinbase.com/careers"),
    ("Uber", "https://www.uber.com/us/en/careers/"),
    ("Lyft", "https://www.lyft.com/careers"),
    ("Airbnb", "https://careers.airbnb.com/"),
    ("DoorDash", "https://careers.doordash.com/"),
    ("LinkedIn", "https://www.linkedin.com/jobs/"),
    ("Indeed", "https://www.indeed.jobs/"),
    ("X", "https://careers.x.com/"),
    ("Spotify", "https://www.lifeatspotify.com/jobs"),
    ("Discord", "https://discord.com/jobs"),
    ("Twitch", "https://www.twitch.tv/jobs/"),
    ("Electronic Arts", "https://www.ea.com/careers"),
    ("Riot Games", "https://www.riotgames.com/en/work-with-us"),
    ("Walmart Global Tech", "https://careers.walmart.com/us/en/teams/technology"),
    ("Target", "https://corporate.target.com/careers"),
    ("JPMorgan Chase", "https://www.jpmorganchase.com/careers"),
    ("Goldman Sachs", "https://www.goldmansachs.com/careers"),
    ("Morgan Stanley", "https://www.morganstanley.com/people-opportunities"),
    ("Deloitte", "https://www.deloitte.com/global/en/careers.html"),
    ("Accenture", "https://www.accenture.com/us-en/careers"),
    ("TCS", "https://www.tcs.com/careers"),
    ("Infosys", "https://www.infosys.com/careers.html"),
    ("Wipro", "https://careers.wipro.com/"),
    ("HCLTech", "https://www.hcltech.com/careers"),
    ("Flipkart", "https://www.flipkartcareers.com/"),
    ("Razorpay", "https://razorpay.com/jobs/"),
    ("Swiggy", "https://careers.swiggy.com/"),
    ("Zomato", "https://www.zomato.com/careers"),
]


def get_company_links():
    return [
        {
            "id": f"company-{index}",
            "company": company.upper(),
            "title": f"Explore {company} careers",
            "type": "companies",
            "domain": "technology",
            "isRemote": True,
            "ribbonText": "Company Link",
            "ribbonClass": "",
            "typeTag": "🏢 Company Careers",
            "domainTag": "⚙️ Technology",
            "packageTag": "🔗 Official Careers Page",
            "extraTag": "🌐 Global Opportunities",
            "location": "📍 Global / Online",
            "buttonText": "View Careers",
            "apply_link": link,
        }
        for index, (company, link) in enumerate(COMPANY_CAREER_LINKS, start=1)
    ]


@app.get("/")
def serve_homepage():
    return FileResponse(BASE_DIR / "getstarted.html")

@app.get("/api/jobs")
def get_live_jobs(prompt: str = "Software Engineer"):
    
    user_query = prompt.lower()

    if "compan" in user_query or "career page" in user_query:
        return get_company_links()
    
    # 🌟 1. SMART INTENT DETECTION
    is_hackathon = "hackathon" in user_query or "hackathons" in user_query or "contest" in user_query
    is_internship = "intern" in user_query or "internship" in user_query
    
    # 🌟 2. ROUTING FOR HACKATHONS
    if is_hackathon:
        print(f"\n--- AI AGENT ROUTING: Loading Hackathons for '{prompt}' ---")
        return [
            {
                "company": "MAJOR LEAGUE HACKING (MLH)",
                "title": f"Global Tech Hack Week",
                "type": "Hackathon",
                "domain": "Tech",
                "ribbonText": "Register Now",
                "ribbonClass": "hackathon",
                "apply_link": "https://mlh.io"
            },
            {
                "company": "DEVPOST",
                "title": f"Next-Gen Innovation Challenge",
                "type": "Hackathon",
                "domain": "Data",
                "ribbonText": "$10k Prize",
                "ribbonClass": "hackathon",
                "apply_link": "https://devpost.com"
            },
            {
                "company": "GOOGLE FOR DEVELOPERS",
                "title": "Build with AI - Global Hackathon",
                "type": "Hackathon",
                "domain": "AI",
                "ribbonText": "Live Now",
                "ribbonClass": "hackathon",
                "apply_link": "https://developers.google.com"
            }
        ]

    # 🌟 3. ROUTING FOR JOBS & INTERNSHIPS (Using Adzuna API)
    search_terms = []
    
    if "backend" in user_query:
        search_terms.append("Backend Developer")
    elif "frontend" in user_query:
        search_terms.append("Frontend Developer")
    elif "data" in user_query or "ai" in user_query or "ml" in user_query:
        search_terms.append("Data Scientist")
    elif "cyber" in user_query:
        search_terms.append("Cybersecurity")
    else:
        search_terms.append(prompt)
        
    # If the user asked for an internship, append it to the search keywords
    if is_internship:
        search_terms.append("Internship")
        
    search_query = " ".join(search_terms)

    url = f"https://api.adzuna.com/v1/api/jobs/{COUNTRY_CODE}/search/1"
    
    params = {
        "app_id": ADZUNA_APP_ID,
        "app_key": ADZUNA_APP_KEY,
        "results_per_page": 10,
        "what": search_query,
        "content-type": "application/json"
    }
    
    # If it's a standard job (and not an internship), enforce full-time
    if not is_internship:
        params["full_time"] = 1

    print(f"\n--- AI AGENT RUNNING: Searching Adzuna for '{search_query}' ---")
    
    try:
        response = requests.get(url, params=params)
        
        if response.status_code != 200:
            print(f"API Error Details: {response.text}")
            return []
            
        api_data = response.json()
        results = api_data.get("results", [])
        
        live_opportunities = []
        for item in results:
            clean_title = item.get("title", "Role").replace("<strong>", "").replace("</strong>", "")
            
            opp_type = "Internship" if is_internship else "Job"
            
            formatted_item = {
                "company": item.get("company", {}).get("display_name", "Confidential").upper(),
                "title": clean_title,
                "type": opp_type,
                "domain": "General",
                "ribbonText": "Internship" if is_internship else "Full-Time Role",
                "ribbonClass": "intern" if is_internship else "",
                "apply_link": item.get("redirect_url", "#")
            }
            live_opportunities.append(formatted_item)
            
        return live_opportunities
        
    except Exception as e:
        print(f"CRITICAL SYSTEM ERROR: {e}")
        return []


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=int(os.getenv("PORT", "5501")),
        log_level="info",
    )