"""
Industry campaign templates.
Each campaign = list of query variations + recommended grid settings.
Split into batches so each batch = one dashboard job (~200-300 results).
Combine all batches in master CSV for 1000+ total.
"""

# KWC bounding box (covers Kitchener + Waterloo + Cambridge)
KWC_BBOX = {"min_lat": "43.33", "min_lon": "-80.60", "max_lat": "43.50", "max_lon": "-80.35"}

# Greater KWC (wider net, includes Guelph fringe)
GKWC_BBOX = {"min_lat": "43.28", "min_lon": "-80.65", "max_lat": "43.55", "max_lon": "-80.30"}

CAMPAIGNS = {
    "babitha_employers_kwc": {
        "label": "Babitha — Admin/CS/Finance Employers — KWC",
        "goal": "hidden_job_market",
        "bbox": GKWC_BBOX,
        "cell": "1",
        "batches": [
            # Batch 1 — Medical & dental (receptionist, MOA, clinic admin)
            ["medical clinics Kitchener Ontario", "dental offices Kitchener Ontario",
             "doctor offices Waterloo Ontario", "pharmacy Kitchener Ontario",
             "physiotherapy clinics Kitchener", "optometry Kitchener Ontario"],
            # Batch 2 — Finance & banking (AP clerk, billing, bank CSR)
            ["banks Kitchener Ontario", "credit unions Kitchener Ontario",
             "insurance companies Kitchener Ontario", "accounting firms Waterloo Ontario",
             "financial advisors Kitchener Ontario", "mortgage brokers Kitchener"],
            # Batch 3 — Law & professional offices (admin, receptionist)
            ["law firms Kitchener Ontario", "legal offices Waterloo Ontario",
             "real estate offices Kitchener", "notary public Kitchener Ontario",
             "consulting firms Kitchener Ontario"],
            # Batch 4 — Retail (supervisor, assistant manager, sales associate)
            ["retail stores Kitchener Ontario", "shopping centres Kitchener",
             "grocery stores Kitchener Ontario", "clothing stores Waterloo Ontario",
             "department stores Kitchener Ontario", "home improvement stores Kitchener"],
            # Batch 5 — Nonprofits & community services (program assistant, intake)
            ["nonprofit organizations Kitchener Ontario", "community centres Kitchener",
             "social services Kitchener Ontario", "charities Waterloo Ontario",
             "employment services Kitchener Ontario", "settlement services Kitchener"],
            # Batch 6 — Schools & libraries (school office, library assistant)
            ["schools Kitchener Ontario", "elementary schools Waterloo Ontario",
             "colleges Kitchener Ontario", "libraries Kitchener Ontario",
             "daycares Kitchener Ontario", "tutoring centres Waterloo"],
            # Batch 7 — Property & facilities (leasing admin, property management)
            ["property management companies Kitchener", "real estate property management Waterloo",
             "apartment buildings Kitchener Ontario", "condominium management Kitchener",
             "building management Cambridge Ontario"],
            # Batch 8 — Hotels & hospitality (front desk, customer service)
            ["hotels Kitchener Ontario", "motels Waterloo Ontario",
             "bed and breakfast Kitchener", "event venues Kitchener Ontario",
             "conference centres Waterloo Ontario"],
            # Batch 9 — Gyms & fitness (front desk, member services)
            ["gyms Kitchener Ontario", "fitness centres Waterloo Ontario",
             "yoga studios Kitchener", "recreation centres Kitchener Ontario",
             "sports clubs Waterloo Ontario"],
            # Batch 10 — Call centres & BPO (call centre rep, chat support, data entry)
            ["call centres Kitchener Ontario", "call center Waterloo Ontario",
             "BPO companies Kitchener Ontario", "outsourcing companies Waterloo",
             "customer service centres Kitchener", "contact centres Cambridge Ontario",
             "telemarketing companies Kitchener", "business process outsourcing Kitchener"],
            # Batch 11 — Logistics & warehouse admin (admin clerk, inventory, dispatch)
            ["logistics companies Kitchener Ontario", "warehouses Kitchener Ontario",
             "distribution centres Cambridge Ontario", "shipping companies Kitchener",
             "courier companies Waterloo Ontario"],
            # Batch 12 — HR & staffing (HR assistant, recruitment coordinator)
            ["staffing agencies Kitchener Ontario", "HR consulting Waterloo Ontario",
             "recruitment agencies Kitchener", "employment agencies Cambridge Ontario",
             "human resources firms Kitchener"],
            # Batch 13 — Clinics missing from before
            ["chiropractic clinics Kitchener ON", "chiropractic clinics Waterloo ON",
             "veterinary clinics Kitchener ON", "veterinary clinics Waterloo ON",
             "chiropractic clinics Cambridge ON", "veterinary clinics Guelph ON"],
            # Batch 14 — Finance admin missing (bookkeeping, payroll, tax)
            ["bookkeeping services Kitchener ON", "bookkeeping services Waterloo ON",
             "payroll services Kitchener ON", "tax preparation Kitchener ON",
             "tax preparation Waterloo ON", "bookkeeping services Cambridge ON"],
            # Batch 15 — Customer service missing (rental, storage, travel)
            ["car rental companies Kitchener ON", "equipment rental Kitchener ON",
             "storage facilities Kitchener ON", "storage facilities Waterloo ON",
             "travel agencies Kitchener ON", "travel agencies Waterloo ON"],
            # Batch 16 — Nonprofit missing (women, youth, family services)
            ["women services Kitchener ON", "youth services Kitchener ON",
             "family services Kitchener ON", "women services Waterloo ON",
             "youth services Cambridge ON", "family services Guelph ON"],
            # Batch 17 — Training & education missing
            ["training centres Kitchener ON", "training centres Waterloo ON",
             "private schools Kitchener ON", "private schools Waterloo ON",
             "training centres Cambridge ON", "colleges Guelph ON"],
            # Batch 18 — Guelph expansion (all high-value categories)
            ["medical clinics Guelph ON", "dental clinics Guelph ON",
             "accounting firms Guelph ON", "property management Guelph ON",
             "nonprofit organizations Guelph ON", "gyms Guelph ON",
             "car dealerships Guelph ON", "daycare centres Guelph ON",
             "employment agencies Guelph ON", "staffing agencies Guelph ON"],
            # Batch 19 — BPO & contact centres (Wipro chat experience fits perfectly)
            ["BPO companies Kitchener ON", "call centers Kitchener ON",
             "contact centers Kitchener ON", "customer service outsourcing Kitchener ON",
             "business process outsourcing Waterloo ON", "call centers Waterloo ON",
             "contact centers Cambridge ON", "customer support companies Kitchener ON",
             "answering services Kitchener ON", "telemarketing companies Kitchener ON",
             "market research call centre Kitchener ON", "virtual receptionist services Kitchener ON"],
        ],
    },

    "all_businesses_kwc": {
        "label": "All Businesses — KWC",
        "goal": "hidden_job_market",
        "bbox": KWC_BBOX,
        "cell": "1",
        "batches": [
            ["businesses in Kitchener Ontario", "companies in Kitchener Ontario", "offices in Kitchener Ontario"],
            ["businesses in Waterloo Ontario", "companies in Waterloo Ontario", "offices in Waterloo Ontario"],
            ["businesses in Cambridge Ontario", "companies in Cambridge Ontario", "offices in Cambridge Ontario"],
            ["manufacturing Kitchener Ontario", "warehouse Kitchener Ontario", "factory Kitchener Ontario"],
            ["retail stores Kitchener Ontario", "shops Kitchener Ontario", "stores Waterloo Ontario"],
            ["restaurants Kitchener Ontario", "hotels Kitchener Ontario", "hospitality Kitchener Ontario"],
            ["construction Kitchener Ontario", "contractors Kitchener Ontario", "trades Kitchener Ontario"],
            ["healthcare Kitchener Ontario", "clinics Kitchener Ontario", "medical Waterloo Ontario"],
            ["finance Kitchener Ontario", "insurance Kitchener Ontario", "accounting Kitchener Ontario"],
            ["technology companies Waterloo Ontario", "IT firms Kitchener Ontario", "software Waterloo Ontario"],
        ],
    },

    "blue_collar_kwc": {
        "label": "Blue Collar All Industries — KWC",
        "goal": "hidden_job_market",
        "bbox": GKWC_BBOX,
        "cell": "1",
        "batches": [
            # Batch 1 — Construction & trades
            ["general contractors Kitchener", "construction companies Kitchener", "renovation contractors Waterloo",
             "roofing companies Kitchener", "siding contractors Cambridge"],
            # Batch 2 — Mechanical trades
            ["plumbers Kitchener Ontario", "electricians Kitchener Ontario", "HVAC contractors Kitchener",
             "pipefitters Kitchener", "gasfitters Waterloo Ontario"],
            # Batch 3 — Automotive
            ["auto repair shops Kitchener", "mechanics Kitchener Ontario", "auto body shops Waterloo",
             "tire shops Kitchener", "towing companies Kitchener", "car dealerships Kitchener"],
            # Batch 4 — Manufacturing & industrial
            ["manufacturing companies Kitchener", "factories Kitchener Ontario", "metal fabrication Kitchener",
             "welding shops Waterloo", "machine shops Cambridge Ontario"],
            # Batch 5 — Warehousing & logistics
            ["warehouses Kitchener Ontario", "logistics companies Kitchener", "trucking companies Kitchener",
             "moving companies Kitchener", "courier companies Waterloo"],
            # Batch 6 — Landscaping & outdoor
            ["landscaping companies Kitchener", "lawn care Kitchener Ontario", "tree service Kitchener",
             "snow removal Kitchener", "excavation companies Waterloo"],
            # Batch 7 — Cleaning & maintenance
            ["cleaning companies Kitchener", "janitorial services Waterloo", "commercial cleaning Cambridge",
             "window cleaning Kitchener", "pressure washing Kitchener"],
            # Batch 8 — Skilled trades finish work
            ["painters Kitchener Ontario", "drywall contractors Kitchener", "flooring companies Kitchener",
             "tile contractors Waterloo", "insulation contractors Kitchener", "carpentry Kitchener"],
            # Batch 9 — Specialty
            ["concrete companies Kitchener", "masonry contractors Waterloo", "demolition contractors Kitchener",
             "septic services Kitchener", "pest control Kitchener", "pool services Waterloo"],
            # Batch 10 — Food & hospitality (blue collar adjacent)
            ["food processing Kitchener", "bakeries Kitchener Ontario", "restaurants Kitchener Ontario",
             "catering companies Kitchener", "grocery stores Waterloo"],
            # Batch 11 — Security & property
            ["security companies Kitchener", "security guards Waterloo", "property management Kitchener",
             "building maintenance Kitchener", "facilities management Waterloo"],
            # Batch 12 — Waste & utilities
            ["waste management Kitchener", "recycling companies Waterloo", "scrap metal Kitchener",
             "junk removal Kitchener", "drain cleaning Waterloo"],
        ],
    },

    "construction_kwc": {
        "label": "Construction Companies — KWC",
        "goal": "website_sales",  # target: no-website businesses
        "bbox": KWC_BBOX,
        "cell": "1",
        "batches": [
            # Batch 1 — general
            [
                "construction companies in Kitchener Ontario",
                "construction companies in Waterloo Ontario",
                "construction companies in Cambridge Ontario",
                "general contractors in Kitchener Ontario",
                "general contractors in Waterloo Ontario",
            ],
            # Batch 2 — specialty trades
            [
                "roofing contractors in Kitchener Ontario",
                "roofing contractors in Waterloo Ontario",
                "roofing companies in Cambridge Ontario",
                "siding contractors in Kitchener Ontario",
                "exterior renovation Kitchener Ontario",
            ],
            # Batch 3 — renovation
            [
                "home renovation contractors Kitchener",
                "basement renovation Kitchener Ontario",
                "kitchen renovation Kitchener Ontario",
                "bathroom renovation Kitchener Ontario",
                "house renovation Cambridge Ontario",
            ],
            # Batch 4 — trades
            [
                "plumbers in Kitchener Ontario",
                "electricians in Kitchener Ontario",
                "HVAC contractors Kitchener Ontario",
                "drywall contractors Kitchener Ontario",
                "flooring contractors Kitchener Ontario",
            ],
            # Batch 5 — commercial / industrial
            [
                "commercial construction Kitchener Ontario",
                "industrial contractors Waterloo Ontario",
                "concrete contractors Kitchener Ontario",
                "framing contractors Kitchener Ontario",
                "masonry contractors Kitchener Ontario",
            ],
        ],
    },

    "staffing_leads_kwc": {
        "label": "Hidden Job Market — KWC (Staffing Leads)",
        "goal": "hidden_job_market",  # target: businesses with phone, no online jobs
        "bbox": KWC_BBOX,
        "cell": "1",
        "batches": [
            [
                "manufacturing companies Kitchener Ontario",
                "manufacturing companies Waterloo Ontario",
                "manufacturing companies Cambridge Ontario",
                "factories in Kitchener Ontario",
                "warehouses in Kitchener Ontario",
            ],
            [
                "logistics companies Kitchener Ontario",
                "distribution centers Cambridge Ontario",
                "food processing Kitchener Ontario",
                "packaging companies Waterloo Ontario",
                "automotive parts Kitchener Ontario",
            ],
            [
                "small businesses Kitchener Ontario",
                "retail stores Kitchener Ontario",
                "restaurants Kitchener Ontario",
                "hotels Kitchener Ontario",
                "cleaning companies Kitchener Ontario",
            ],
            [
                "IT companies Waterloo Ontario",
                "tech companies Kitchener Ontario",
                "call centers Kitchener Ontario",
                "accounting firms Kitchener Ontario",
                "insurance companies Waterloo Ontario",
            ],
        ],
    },

    "restaurants_kwc": {
        "label": "Restaurants — KWC",
        "goal": "website_sales",
        "bbox": KWC_BBOX,
        "cell": "0.5",
        "batches": [
            ["restaurants in Kitchener Ontario", "restaurants in Waterloo Ontario", "restaurants in Cambridge Ontario"],
            ["cafes in Kitchener Ontario", "coffee shops Waterloo Ontario", "bakeries Kitchener Ontario"],
            ["pizza Kitchener Ontario", "sushi Kitchener Ontario", "indian restaurant Kitchener Ontario"],
            ["takeout Kitchener Ontario", "fast food Kitchener Ontario", "food delivery Kitchener Ontario"],
        ],
    },

    "custom": {
        "label": "Custom Campaign",
        "goal": "custom",
        "bbox": KWC_BBOX,
        "cell": "1",
        "batches": [],
    },
}


def get_campaign_names():
    return [{"id": k, "label": v["label"], "goal": v["goal"], "batch_count": len(v["batches"])}
            for k, v in CAMPAIGNS.items()]


def get_campaign(campaign_id):
    return CAMPAIGNS.get(campaign_id)
