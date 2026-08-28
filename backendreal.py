from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi import Request
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

# Previously deployed backend URL (Vercel) — used as an external service endpoint
EXTERNAL_BACKEND_URL = "https://hacker-2t6h3vhn1-aihack.vercel.app"

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


@app.post("/api/track_apply")
async def track_apply(request: Request):
    """Receive application tracking events from the frontend and persist them to applications.json"""
    try:
        payload = await request.json()
    except Exception:
        return {"status": "error", "message": "invalid json"}

    out_file = BASE_DIR / "applications.json"
    try:
        existing = []
        if out_file.exists():
            import json
            existing = json.loads(out_file.read_text(encoding="utf-8") or "[]")

        import json
        entry = {
            "company": payload.get("company"),
            "title": payload.get("title"),
            "apply_link": payload.get("apply_link"),
            "timestamp": __import__("time").time(),
        }
        existing.append(entry)
        out_file.write_text(json.dumps(existing, indent=2), encoding="utf-8")
        return {"status": "ok", "entry": entry}
    except Exception as e:
        return {"status": "error", "message": str(e)}


COMPANY_SIGNIN_PORTALS = {
    "GOOGLE": "https://careers.google.com/",
    "MICROSOFT": "https://careers.microsoft.com/",
    "AMAZON": "https://www.amazon.jobs/",
    "APPLE": "https://www.apple.com/careers/",
    "META": "https://www.metacareers.com/",
    "NETFLIX": "https://jobs.netflix.com/",
    "NVIDIA": "https://nvidia.wd5.myworkdayjobs.com/NVIDIAExternalCareerSite",
    "OPENAI": "https://openai.com/careers/",
    "IBM": "https://www.ibm.com/careers/",
    "ORACLE": "https://www.oracle.com/careers/",
    "ADOBE": "https://careers.adobe.com/",
    "SALESFORCE": "https://www.salesforce.com/company/careers/",
    "SPOTIFY": "https://lifeatspotify.com/jobs",
    "UBER": "https://www.uber.com/us/en/careers/",
    "AIRBNB": "https://careers.airbnb.com/",
    "LINKEDIN": "https://www.linkedin.com/jobs/",
    "INDEED": "https://www.indeed.com/",
    "MLH": "https://mlh.io/users/sign_in",
    "DEVPOST": "https://devpost.com/login"
}

def resolve_signin_link(company_name: str, redirect_url: str = "") -> str:
    upper = (company_name or "").upper()
    for name, portal in COMPANY_SIGNIN_PORTALS.items():
        if name in upper:
            return portal
    if redirect_url and redirect_url != "#":
        return redirect_url
    return f"https://www.google.com/search?q={requests.utils.quote(company_name + ' career sign in portal')}"


@app.get("/")
def serve_homepage():
    return FileResponse(BASE_DIR / "getstarted.html")


@app.get("/api/jobs")
def get_live_jobs(prompt: str = "Software Engineer"):
    user_query = prompt.lower().strip()

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
                "title": "Global Tech Hackathon 2026",
                "type": "Hackathon",
                "domain": "Software & AI",
                "location": "Online / Worldwide",
                "salary": "Prizes worth $25,000",
                "description": "Build innovative web & AI applications alongside developers worldwide.",
                "ribbonText": "Live Hackathon",
                "ribbonClass": "hackathon",
                "apply_link": "https://mlh.io",
                "signin_link": "https://mlh.io/users/sign_in"
            },
            {
                "company": "DEVPOST",
                "title": "Next-Gen AI & Cloud Challenge",
                "type": "Hackathon",
                "domain": "Artificial Intelligence",
                "location": "Remote",
                "salary": "Prizes worth $50,000",
                "description": "Create novel machine learning models and serverless cloud solutions.",
                "ribbonText": "$50k Prize Pool",
                "ribbonClass": "hackathon",
                "apply_link": "https://devpost.com",
                "signin_link": "https://devpost.com/login"
            },
            {
                "company": "GOOGLE FOR DEVELOPERS",
                "title": "Build with AI - Global Developer Hackathon",
                "type": "Hackathon",
                "domain": "AI / ML",
                "location": "Global / Online",
                "salary": "Google Cloud Credits & Swag",
                "description": "Collaborate with Google engineers and turn creative tech ideas into reality.",
                "ribbonText": "Google Event",
                "ribbonClass": "hackathon",
                "apply_link": "https://developers.google.com",
                "signin_link": "https://accounts.google.com"
            },
            {
                "company": "META",
                "title": "Meta Hacker Cup 2026",
                "type": "Hackathon",
                "domain": "Algorithms & Systems",
                "location": "Global / Online",
                "salary": "$100,000 Total Prize Purse",
                "description": "Meta's flagship global algorithmic programming competition.",
                "ribbonText": "Meta Official",
                "ribbonClass": "hackathon",
                "apply_link": "https://www.facebook.com/codingcompetitions/hacker-cup/",
                "signin_link": "https://www.facebook.com/login/"
            },
            {
                "company": "ETHGLOBAL",
                "title": "ETHGlobal Web3 & Smart Contracts Hackathon",
                "type": "Hackathon",
                "domain": "Web3 & Blockchain",
                "location": "Remote / Global",
                "salary": "$125,000 Bounties",
                "description": "Build decentralized protocols, smart contracts, and dApps with global crypto leaders.",
                "ribbonText": "Web3 Event",
                "ribbonClass": "hackathon",
                "apply_link": "https://ethglobal.com/",
                "signin_link": "https://ethglobal.com/login"
            },
            {
                "company": "MICROSOFT",
                "title": "Imagine Cup World Championship",
                "type": "Hackathon",
                "domain": "AI & Cloud Tech",
                "location": "Global / Online",
                "salary": "$100,000 + Azure Mentorship",
                "description": "Student developer competition to launch startup prototypes powered by Azure AI.",
                "ribbonText": "World Championship",
                "ribbonClass": "hackathon",
                "apply_link": "https://imaginecup.microsoft.com/",
                "signin_link": "https://imaginecup.microsoft.com/"
            },
            {
                "company": "KAGGLE",
                "title": "Kaggle Grand Prix Machine Learning Hackathon",
                "type": "Hackathon",
                "domain": "Data Science & ML",
                "location": "Remote / Kaggle Platform",
                "salary": "$30,000 Prize Pool",
                "description": "Train deep learning models on real-world datasets to predict complex outcomes.",
                "ribbonText": "Kaggle Live",
                "ribbonClass": "hackathon",
                "apply_link": "https://www.kaggle.com/competitions",
                "signin_link": "https://www.kaggle.com/account/login"
            },
            {
                "company": "MIT HACKERS",
                "title": "HackMIT Flagship Student Hackathon",
                "type": "Hackathon",
                "domain": "Software & Hardware",
                "location": "Cambridge, MA / Hybrid",
                "salary": "Tech Swag & Mentorship",
                "description": "1,000+ student developers gather to hack, build, and pitch disruptive prototypes in 36 hours.",
                "ribbonText": "MIT Flagship",
                "ribbonClass": "hackathon",
                "apply_link": "https://hackmit.org/",
                "signin_link": "https://hackmit.org/"
            }
        ]

    # 🌟 3. ROUTING FOR JOBS & INTERNSHIPS (Using Adzuna API)
    search_terms = []
    
    if "backend" in user_query:
        search_terms.append("Backend Developer")
    elif "frontend" in user_query:
        search_terms.append("Frontend Developer")
    elif "fullstack" in user_query or "full stack" in user_query:
        search_terms.append("Full Stack Engineer")
    elif "data" in user_query or "ai" in user_query or "ml" in user_query:
        search_terms.append("Data Scientist")
    elif "cyber" in user_query or "security" in user_query:
        search_terms.append("Cybersecurity Specialist")
    elif "teacher" in user_query or "teaching" in user_query or "education" in user_query:
        search_terms.append("Teacher Education")
    elif "product" in user_query or "manager" in user_query:
        search_terms.append("Product Manager")
    else:
        search_terms.append(prompt)
        
    if is_internship:
        search_terms.append("Internship")
        
    search_query = " ".join(search_terms)
    url = f"https://api.adzuna.com/v1/api/jobs/{COUNTRY_CODE}/search/1"
    
    params = {
        "app_id": ADZUNA_APP_ID,
        "app_key": ADZUNA_APP_KEY,
        "results_per_page": 25,
        "what": search_query,
        "content-type": "application/json"
    }
    
    if not is_internship:
        params["full_time"] = 1

    print(f"\n--- AI AGENT RUNNING: Searching Adzuna for '{search_query}' ---")
    
    try:
        response = requests.get(url, params=params, timeout=4)
        
        if response.status_code == 200:
            api_data = response.json()
            results = api_data.get("results", [])
            
            if results:
                live_opportunities = []
                for item in results:
                    raw_company = item.get("company", {}).get("display_name", "Tech Company").upper()
                    clean_title = item.get("title", "Role").replace("<strong>", "").replace("</strong>", "")
                    redirect_url = item.get("redirect_url", "#")
                    signin_url = resolve_signin_link(raw_company, redirect_url)
                    opp_type = "Internship" if is_internship or "intern" in clean_title.lower() else "Job"
                    
                    loc_name = item.get("location", {}).get("display_name", "India / Remote")
                    min_sal = item.get("salary_min")
                    max_sal = item.get("salary_max", min_sal * 1.3 if min_sal else None)
                    sal_str = f"₹{int(min_sal):,} - ₹{int(max_sal):,} / yr" if min_sal else "Competitive Compensation"
                    desc_snippet = item.get("description", "Opportunity to join a dynamic development team.").replace("<strong>", "").replace("</strong>", "")[:180] + "..."

                    formatted_item = {
                        "company": raw_company,
                        "title": clean_title,
                        "type": opp_type,
                        "domain": item.get("category", {}).get("label", "Technology"),
                        "location": loc_name,
                        "salary": sal_str,
                        "description": desc_snippet,
                        "ribbonText": "Internship" if opp_type == "Internship" else "Full-Time Role",
                        "ribbonClass": "intern" if opp_type == "Internship" else "",
                        "apply_link": redirect_url,
                        "signin_link": signin_url
                    }
                    live_opportunities.append(formatted_item)
                    
                return live_opportunities
    except Exception as e:
        print(f"ADZUNA FETCH EXCEPTION: {e}")

    # Fallback opportunities if API limit reached or network offline
    is_teacher = "teacher" in user_query or "teaching" in user_query
    if is_teacher:
        return [
            {
                "company": "K-12 ACADEMY & LOCAL SCHOOLS",
                "title": "Computer Science Educator",
                "type": "Job",
                "domain": "Education",
                "location": "Bangalore / Remote",
                "salary": "₹6,00,000 - ₹12,00,000 / yr",
                "description": "Teach coding, computer science fundamentals, and web development to enthusiastic students.",
                "ribbonText": "Urgent Opening",
                "ribbonClass": "",
                "apply_link": "https://www.indeed.com/q-teacher-jobs.html",
                "signin_link": "https://www.indeed.com/account/login"
            },
            {
                "company": "COURSERA & EDTECH PARTNERS",
                "title": "Online AI & Technical Curriculum Instructor",
                "type": "Job",
                "domain": "EdTech",
                "location": "Remote",
                "salary": "₹8,00,000 - ₹15,00,000 / yr",
                "description": "Design interactive coding assessments, video lessons, and developer tutorials.",
                "ribbonText": "100% Remote",
                "ribbonClass": "",
                "apply_link": "https://www.coursera.org/about/careers",
                "signin_link": "https://www.coursera.org/?authMode=login"
            }
        ]

    return [
        {
            "company": "GOOGLE",
            "title": "Software Engineering Intern" if is_internship else "Software Engineer - AI & Cloud",
            "type": "Internship" if is_internship else "Job",
            "domain": "Technology",
            "location": "Bangalore / Hyderabad, India",
            "salary": "₹18,00,000 - ₹32,00,000 / yr",
            "description": "Architect scalable web applications, modern APIs, and machine learning backend services.",
            "ribbonText": "Featured",
            "ribbonClass": "intern" if is_internship else "",
            "apply_link": "https://careers.google.com/",
            "signin_link": "https://careers.google.com/"
        },
        {
            "company": "MICROSOFT",
            "title": "Product Engineer Intern" if is_internship else "Senior Software Engineer",
            "type": "Internship" if is_internship else "Job",
            "domain": "Product & Cloud",
            "location": "Hyderabad, India / Remote",
            "salary": "₹16,00,000 - ₹28,00,000 / yr",
            "description": "Build high-availability cloud solutions, Azure integrations, and developer platforms.",
            "ribbonText": "Internship" if is_internship else "High Demand",
            "ribbonClass": "intern" if is_internship else "",
            "apply_link": "https://careers.microsoft.com/",
            "signin_link": "https://careers.microsoft.com/"
        },
        {
            "company": "OPENAI",
            "title": "Research & AI Systems Engineer",
            "type": "Job",
            "domain": "Generative AI",
            "location": "Remote / Global",
            "salary": "₹28,00,000+ / yr",
            "description": "Develop high-throughput inference engines and state-of-the-art transformer models.",
            "ribbonText": "Hot Role",
            "ribbonClass": "",
            "apply_link": "https://openai.com/careers/",
            "signin_link": "https://openai.com/careers/"
        },
        {
            "company": "AMAZON",
            "title": "Frontend & Fullstack Developer",
            "type": "Job",
            "domain": "E-Commerce",
            "location": "Chennai / Bangalore, India",
            "salary": "₹15,00,000 - ₹24,00,000 / yr",
            "description": "Create responsive, accessible user interfaces with React and AWS serverless backend infrastructure.",
            "ribbonText": "Actively Hiring",
            "ribbonClass": "",
            "apply_link": "https://www.amazon.jobs/",
            "signin_link": "https://www.amazon.jobs/"
        },
        {
            "company": "META",
            "title": "Production Engineering Intern" if is_internship else "Software Engineer - Infrastructure",
            "type": "Internship" if is_internship else "Job",
            "domain": "Social Infrastructure",
            "location": "Gurgaon, India / Remote",
            "salary": "₹19,00,000 - ₹34,00,000 / yr",
            "description": "Scale global networking infrastructure, data center automation, and distributed web services.",
            "ribbonText": "High Growth",
            "ribbonClass": "intern" if is_internship else "",
            "apply_link": "https://www.metacareers.com/",
            "signin_link": "https://www.metacareers.com/"
        },
        {
            "company": "APPLE",
            "title": "iOS & Swift Application Developer",
            "type": "Job",
            "domain": "Mobile Systems",
            "location": "Hyderabad / Bangalore, India",
            "salary": "₹17,00,000 - ₹30,00,000 / yr",
            "description": "Build high-performance client applications and frameworks for millions of Apple devices.",
            "ribbonText": "Apple Team",
            "ribbonClass": "",
            "apply_link": "https://www.apple.com/careers/",
            "signin_link": "https://www.apple.com/careers/"
        },
        {
            "company": "NVIDIA",
            "title": "CUDA & Deep Learning SDK Engineer",
            "type": "Job",
            "domain": "AI Hardware & Compute",
            "location": "Pune / Bangalore, India",
            "salary": "₹22,00,000 - ₹38,00,000 / yr",
            "description": "Accelerate neural network training pipelines using CUDA C++, PyTorch, and TensorRT.",
            "ribbonText": "AI Leader",
            "ribbonClass": "",
            "apply_link": "https://nvidia.wd5.myworkdayjobs.com/NVIDIAExternalCareerSite",
            "signin_link": "https://nvidia.wd5.myworkdayjobs.com/NVIDIAExternalCareerSite"
        },
        {
            "company": "NETFLIX",
            "title": "Cloud Operations & Streaming Backend Engineer",
            "type": "Job",
            "domain": "Media & Cloud",
            "location": "Remote / Mumbai",
            "salary": "₹25,00,000 - ₹40,00,000 / yr",
            "description": "Optimize real-time video streaming delivery algorithms and microservices backend micro-architectures.",
            "ribbonText": "Top Compensation",
            "ribbonClass": "",
            "apply_link": "https://jobs.netflix.com/",
            "signin_link": "https://jobs.netflix.com/"
        },
        {
            "company": "UBER",
            "title": "Backend Engineering Intern" if is_internship else "Systems & Logistics Engineer",
            "type": "Internship" if is_internship else "Job",
            "domain": "Transportation & Tech",
            "location": "Bangalore, India",
            "salary": "₹16,50,000 - ₹27,00,000 / yr",
            "description": "Engineer low-latency dispatch algorithms, Geospatial routing, and real-time transaction processing.",
            "ribbonText": "Actively Hiring",
            "ribbonClass": "intern" if is_internship else "",
            "apply_link": "https://www.uber.com/us/en/careers/",
            "signin_link": "https://www.uber.com/us/en/careers/"
        },
        {
            "company": "AIRBNB",
            "title": "Fullstack Platform Engineer",
            "type": "Job",
            "domain": "Hospitality Tech",
            "location": "Remote / Global",
            "salary": "₹20,00,000 - ₹35,00,000 / yr",
            "description": "Build universal web components, payment integrations, and search recommendation workflows.",
            "ribbonText": "100% Remote",
            "ribbonClass": "",
            "apply_link": "https://careers.airbnb.com/",
            "signin_link": "https://careers.airbnb.com/"
        },
        {
            "company": "SPOTIFY",
            "title": "Audio Recommendation Systems Developer",
            "type": "Job",
            "domain": "Music Tech",
            "location": "Remote / Global",
            "salary": "₹18,00,000 - ₹32,00,000 / yr",
            "description": "Implement machine learning recommendation models and personal audio discovery features.",
            "ribbonText": "Global Remote",
            "ribbonClass": "",
            "apply_link": "https://lifeatspotify.com/jobs",
            "signin_link": "https://lifeatspotify.com/jobs"
        },
        {
            "company": "DELOITTE DIGITAL",
            "title": "Cloud Solutions & DevOps Specialist",
            "type": "Job",
            "domain": "Consulting Tech",
            "location": "Hyderabad / Pune, India",
            "salary": "₹10,00,000 - ₹18,00,000 / yr",
            "description": "Architect enterprise cloud migrations, CI/CD automated deployment pipelines, and Kubernetes clusters.",
            "ribbonText": "Enterprise",
            "ribbonClass": "",
            "apply_link": "https://www.deloitte.com/global/en/careers.html",
            "signin_link": "https://www.deloitte.com/global/en/careers.html"
        },
        {
            "company": "TCS DIGITAL",
            "title": "Graduate Systems Engineer Trainee",
            "type": "Job",
            "domain": "IT Services",
            "location": "Chennai / Mumbai / Kolkata",
            "salary": "₹7,00,000 - ₹11,00,000 / yr",
            "description": "Entry-level software engineering program covering Java, Cloud, Data Engineering, and Web Development.",
            "ribbonText": "Fresher Friendly",
            "ribbonClass": "",
            "apply_link": "https://www.tcs.com/careers",
            "signin_link": "https://www.naukri.com/nlogin/login"
        },
        {
            "company": "INFOSYS",
            "title": "Specialist Programmer - Web & Cloud",
            "type": "Job",
            "domain": "Software Services",
            "location": "Bangalore / Mysore",
            "salary": "₹8,00,000 - ₹13,00,000 / yr",
            "description": "Develop fullstack microservices and cloud-native solutions for Fortune 500 enterprise clients.",
            "ribbonText": "Mass Hiring",
            "ribbonClass": "",
            "apply_link": "https://www.infosys.com/careers.html",
            "signin_link": "https://www.naukri.com/nlogin/login"
        },
        {
            "company": "RAZORPAY",
            "title": "Backend Engineering Intern" if is_internship else "Fintech Software Engineer",
            "type": "Internship" if is_internship else "Job",
            "domain": "Fintech",
            "location": "Bangalore, India",
            "salary": "₹14,00,000 - ₹24,00,000 / yr",
            "description": "Build high-reliability payment gateway APIs handling millions of online digital transactions.",
            "ribbonText": "Fintech Leader",
            "ribbonClass": "intern" if is_internship else "",
            "apply_link": "https://razorpay.com/jobs/",
            "signin_link": "https://razorpay.com/jobs/"
        },
        {
            "company": "SWIGGY",
            "title": "Fullstack Software Engineer",
            "type": "Job",
            "domain": "E-Commerce Logistics",
            "location": "Bangalore, India",
            "salary": "₹15,00,000 - ₹26,00,000 / yr",
            "description": "Work on quick-commerce order routing, dynamic pricing algorithms, and mobile web clients.",
            "ribbonText": "Fast Paced",
            "ribbonClass": "",
            "apply_link": "https://careers.swiggy.com/",
            "signin_link": "https://careers.swiggy.com/"
        },
        {
            "company": "ZOMATO",
            "title": "Data Analyst & Business Intelligence",
            "type": "Job",
            "domain": "Analytics & Tech",
            "location": "Gurgaon, India",
            "salary": "₹12,00,000 - ₹20,00,000 / yr",
            "description": "Analyze user metrics, delivery efficiency data, and construct executive dashboards using SQL & Python.",
            "ribbonText": "Data Role",
            "ribbonClass": "",
            "apply_link": "https://www.zomato.com/careers",
            "signin_link": "https://www.zomato.com/careers"
        }
    ]



if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", "5501")),
        log_level="info",
    )