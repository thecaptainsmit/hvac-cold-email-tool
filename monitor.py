#!/usr/bin/env python3
"""
HVAC Competitor Monitor MVP
Monitors Hobaica Services (Phoenix) for pricing, reviews, and job postings
Uses only standard library + requests (no BeautifulSoup)
"""

import json
import requests
import re
import html
from datetime import datetime
import os

DATA_FILE = "hobaica_data.json"
COMPETITOR = {
    "name": "Hobaica Services",
    "location": "Phoenix, AZ",
    "website": "https://www.hobaica.com",
    "careers_url": "https://www.hobaica.com/about-us/",
    "established": 1952,
    "employees": "~50",
    "services": ["HVAC", "Plumbing", "Electrical", "Drains", "Insulation"]
}

def strip_html(text):
    """Remove HTML tags from text"""
    clean = re.sub(r'<[^>]+>', ' ', text)
    return html.unescape(clean)

def load_existing_data():
    """Load existing data or return empty structure"""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {
        "competitor": COMPETITOR,
        "first_seen": datetime.now().isoformat(),
        "history": []
    }

def scrape_website():
    """Scrape Hobaica website for pricing info"""
    pricing_data = {
        "diagnostic_fee": None,
        "tune_up_price": None,
        "service_call": None,
        "other_prices": [],
        "notes": []
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    urls_to_check = [
        "https://www.hobaica.com",
        "https://www.hobaica.com/heating",
        "https://www.hobaica.com/cooling",
        "https://www.hobaica.com/service-agreements",
        "https://www.hobaica.com/pricing"
    ]
    
    all_text = ""
    pages_checked = 0
    
    for url in urls_to_check:
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            pages_checked += 1
            text = strip_html(resp.text)
            all_text += " " + text
        except Exception as e:
            pricing_data["notes"].append(f"Failed to fetch {url}: {str(e)[:50]}")
    
    pricing_data["pages_checked"] = pages_checked
    
    # Clean up text for analysis
    text = all_text.lower()
    
    # Diagnostic fee patterns
    diag_patterns = [
        r'diagnostic\s+fee[s]?[:\s]*\$?\s*(\d{2,3})',
        r'service\s+call[:\s]*\$?\s*(\d{2,3})',
        r'dispatch\s+fee[:\s]*\$?\s*(\d{2,3})',
        r'trip\s+charge[:\s]*\$?\s*(\d{2,3})',
        r'diagnostic[:\s]*\$?\s*(\d{2,3})'
    ]
    
    for pattern in diag_patterns:
        match = re.search(pattern, text)
        if match:
            pricing_data["diagnostic_fee"] = f"${match.group(1)}"
            break
    
    # Tune-up patterns
    tuneup_patterns = [
        r'tune[-\s]?up[s]?[:\s]*\$?\s*(\d{2,3})',
        r'maintenance\s+(?:visit|plan)[:\s]*\$?\s*(\d{2,3})',
        r'seasonal\s+check[:\s]*\$?\s*(\d{2,3})',
        r'precision\s+tune[-\s]?up[:\s]*\$?\s*(\d{2,3})'
    ]
    
    for pattern in tuneup_patterns:
        match = re.search(pattern, text)
        if match:
            pricing_data["tune_up_price"] = f"${match.group(1)}"
            break
    
    # General price extraction
    all_prices = re.findall(r'\$?\s*(\d{2,3})\s*(?:\.\d{2})?', all_text)
    unique_prices = list(set(all_prices))
    pricing_data["other_prices"] = [f"${p}" for p in unique_prices[:10]]
    
    # Extract key phrases that might contain pricing info
    sentences = re.split(r'[.!?]+', all_text)
    price_sentences = [s.strip() for s in sentences if '$' in s and len(s) < 200]
    pricing_data["price_contexts"] = price_sentences[:5]
    
    return pricing_data

def scrape_careers():
    """Scrape job postings from careers page"""
    jobs = {
        "hiring": False,
        "open_positions": [],
        "total_count": 0,
        "notes": []
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        resp = requests.get(COMPETITOR["careers_url"], headers=headers, timeout=10)
        text = strip_html(resp.text).lower()
        raw_html = resp.text.lower()
        
        # Hiring indicators
        hiring_indicators = [
            'now hiring', 'join our team', 'open positions', 
            'career opportunities', 'apply now', 'we\'re hiring',
            'job openings', 'current openings', 'positions available'
        ]
        
        jobs["hiring"] = any(indicator in text for indicator in hiring_indicators)
        
        # Look for job title patterns
        job_patterns = [
            r'(hvac\s+technician[s]?)',
            r'(service\s+technician[s]?)',
            r'(install\w*\s+technician[s]?)',
            r'(sales\s+\w+)',
            r'(customer\s+service\s+\w+)',
            r'(dispatch\w*)',
            r'(maintenance\s+\w+)'
        ]
        
        found_jobs = set()
        for pattern in job_patterns:
            matches = re.findall(pattern, text)
            found_jobs.update(matches)
        
        # Also look for capitalized job titles in the HTML
        title_pattern = r'(?:position|job|title)["\'>\s]*([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,4})'
        title_matches = re.findall(title_pattern, raw_html)
        for match in title_matches:
            if any(keyword in match.lower() for keyword in ['technician', 'manager', 'sales', 'service', 'hvac']):
                found_jobs.add(match)
        
        jobs["open_positions"] = sorted(list(found_jobs))[:15]
        jobs["total_count"] = len(jobs["open_positions"])
        
        if not jobs["hiring"] and jobs["total_count"] > 0:
            jobs["hiring"] = True
            
    except Exception as e:
        jobs["notes"].append(f"Error scraping careers: {str(e)[:100]}")
    
    return jobs

def get_reviews_info():
    """Return Google reviews info placeholder"""
    return {
        "review_count": "Manual check required",
        "rating": "Manual check required", 
        "recent_reviews": "Check last 30 days manually",
        "google_url": "https://www.google.com/search?q=hobaica+services+phoenix+reviews",
        "direct_link": "https://g.page/r/CZ7x1q2y3z4E/review"
    }

def run_monitor():
    """Run the full monitoring scan"""
    print("="*60)
    print("🔥 HVAC Competitor Monitor MVP")
    print(f"📍 Target: {COMPETITOR['name']} ({COMPETITOR['location']})")
    print("="*60)
    
    data = load_existing_data()
    
    print("\n🌐 Scraping website for pricing...")
    pricing = scrape_website()
    
    print("💼 Checking careers page...")
    jobs = scrape_careers()
    
    print("⭐ Preparing reviews info...")
    reviews = get_reviews_info()
    
    snapshot = {
        "timestamp": datetime.now().isoformat(),
        "pricing": pricing,
        "reviews": reviews,
        "jobs": jobs
    }
    
    data["last_updated"] = snapshot["timestamp"]
    data["current"] = snapshot
    data["history"].append(snapshot)
    
    # Keep only last 30 snapshots
    if len(data["history"]) > 30:
        data["history"] = data["history"][-30:]
    
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)
    
    # Print summary
    print("\n" + "="*60)
    print("✅ SCAN COMPLETE!")
    print("="*60)
    print(f"\n💰 Pricing Found:")
    print(f"   Diagnostic Fee: {pricing.get('diagnostic_fee') or 'Not detected'}")
    print(f"   Tune-Up Price: {pricing.get('tune_up_price') or 'Not detected'}")
    print(f"   Pages checked: {pricing.get('pages_checked', 0)}")
    
    print(f"\n💼 Hiring Status: {'🟢 HIRING!' if jobs.get('hiring') else '⚪ No/Unknown'}")
    if jobs.get('open_positions'):
        print(f"   Positions found: {len(jobs['open_positions'])}")
        for job in jobs['open_positions'][:5]:
            print(f"      • {job}")
    
    print(f"\n📁 Data saved to: {DATA_FILE}")
    print(f"🌐 Dashboard: Open dashboard.html in browser")
    
    return data

if __name__ == "__main__":
    run_monitor()
