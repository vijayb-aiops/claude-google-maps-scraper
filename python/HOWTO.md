# How to Use the Scraper

## What This Does

Searches Google Maps for businesses in KWC (Kitchener, Waterloo, Cambridge, Guelph).
Saves results as a CSV file with: **Business Name, Category, Address, Website, Phone, Email**.

---

## Step 1 — Build the Scraper (One Time Only)

Open terminal in `D:\workspace\google-maps-scraper` and run:

```cmd
go build -o google-maps-scraper.exe .
```

This creates `google-maps-scraper.exe`. Do this once, never again.

---

## Step 2 — Start the Dashboard

```cmd
cd D:\workspace\google-maps-scraper\python
python dashboard.py
```

Open browser: **http://localhost:5000**

---

---
# USE CASE 1 — Babitha Job Search
---

**Goal:** Get list of companies in KWC → visit each company website → find job postings → apply directly.

## Which Campaign to Use

→ **Babitha — Admin/CS/Finance Employers — KWC**

Covers 19 batches of employers who hire for:
- Admin / Reception / Office roles
- Customer Service / Call Centre / BPO / Chat Support
- Finance Admin / Accounts Payable / Billing
- Nonprofits / Community Services / Employment Services
- Medical / Dental / Pharmacy offices
- Banks / Insurance / Accounting firms
- Schools / Daycares / Libraries
- Hotels / Gyms / Property Management

## How to Run (Dashboard)

1. Open **http://localhost:5000**
2. Click **Campaigns** tab
3. Select **Babitha — Admin/CS/Finance Employers — KWC**
4. Check **Require phone** (so every result has a contact number)
5. Click **Run All Batches**
6. Wait for all jobs to finish (watch Jobs section — status turns green)
7. Click **Rebuild Master**
8. Download `master.csv`

## How to Run (Terminal)

```cmd
cd D:\workspace\google-maps-scraper\python
python scrape.py --campaign babitha_employers_kwc --require-phone
```

## What to Do With Results

Open `results/master.csv` in Excel.
For each company:
1. Go to their website (website column)
2. Look for "Careers" or "Join Us" page
3. Apply directly — this bypasses job boards (hidden job market)

If no website listed → Google the company name → find their site manually.

---

---
# USE CASE 2 — Website Sales (Selling Web Design)
---

**Goal:** Find businesses with NO website → call them → offer to build their website.

## Which Campaign to Use

→ **Blue Collar All Industries — KWC**

Covers tradespeople and contractors who typically don't have websites:
- Construction, roofing, renovation
- Plumbing, electrical, HVAC
- Auto repair, mechanics
- Landscaping, snow removal
- Cleaning, painting, flooring
- Moving, trucking, logistics
- Pest control, security, waste removal

## How to Run (Dashboard)

1. Open **http://localhost:5000**
2. Click **Campaigns** tab
3. Select **Blue Collar All Industries — KWC**
4. Check **NO website (pitch web design)**
5. Check **Require phone** (so you can call them)
6. Click **Run All Batches**
7. Wait → Rebuild Master → Download

## How to Run (Terminal)

```cmd
cd D:\workspace\google-maps-scraper\python
python scrape.py --campaign blue_collar_kwc --no-website --require-phone
```

## What to Do With Results

Open `results/master.csv` in Excel.
Every result = business with a phone number and NO website.
Call them: *"Hi, I noticed your business isn't online. I build websites for local trades businesses starting at $X…"*

---

---
# GENERAL REFERENCE
---

## Understanding Batches

Each campaign is split into batches. Each batch = group of related searches.

Example Babitha campaign:
- Batch 1 = Medical clinics
- Batch 2 = Banks, insurance, accounting
- Batch 3 = Law firms, real estate
- ... up to Batch 19 = BPO / call centres

Each batch takes **5–15 minutes**. Full campaign = few hours.
Run batch 1 first to test, then run all.

```cmd
# Test with batch 1 first
python scrape.py --campaign babitha_employers_kwc --batch 1

# Then run all
python scrape.py --campaign babitha_employers_kwc --require-phone
```

## Where Are My Results

All files saved in: `D:\workspace\google-maps-scraper\python\results\`

- `master.csv` — final combined clean file **(use this one)**
- `batch01_*.csv` — individual batch files (ignore)

## CSV Columns Explained

| Column | Meaning |
|---|---|
| title | Business name |
| category | Type of business |
| address | Street address |
| website | Their website — **blank = no website** |
| phone | Phone number |
| emails | Email if found |

## All Available Campaigns

| Campaign ID | What It Scrapes |
|---|---|
| `babitha_employers_kwc` | Admin/CS/finance/BPO employers — job search |
| `blue_collar_kwc` | Trades/contractors — website sales |
| `all_businesses_kwc` | All business types — general |
| `construction_kwc` | Construction detailed — website sales |

List all campaigns in terminal:
```cmd
python scrape.py --list-campaigns
```

## Common Problems

**"The system cannot find the file"**
→ Binary not built. Go back to Step 1.

**0 results / empty CSV**
→ Binary path wrong. Check `google-maps-scraper.exe` exists in `D:\workspace\google-maps-scraper\`

**Scraping is slow**
→ Normal. Each query opens real browser, scrolls Google Maps. 2–5 min per query.

**Google blocking / suddenly 0 results**
→ Wait a few hours or restart your router to get a new IP. Run overnight.
