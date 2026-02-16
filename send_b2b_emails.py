#!/usr/bin/env python3
"""
Quick setup and send script for Toronto HVAC B2B outreach
"""
import json
import sqlite3
import smtplib
import hashlib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from pathlib import Path

# Database path
DB_PATH = Path("email_automation.db")

# Gmail credentials
GMAIL_EMAIL = "debug.grace@gmail.com"
GMAIL_PASSWORD = "Bella@6969"

def init_db():
    """Initialize database tables"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS email_accounts (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE,
            smtp_server TEXT,
            smtp_port INTEGER,
            imap_server TEXT,
            imap_port INTEGER,
            app_password TEXT,
            status TEXT,
            warmup_score INTEGER,
            daily_sent INTEGER,
            daily_limit INTEGER,
            created_at TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contacts (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE,
            first_name TEXT,
            last_name TEXT,
            address TEXT,
            zip_code TEXT,
            city TEXT,
            state TEXT,
            home_age INTEGER,
            source TEXT,
            tags TEXT,
            created_at TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS email_logs (
            id TEXT PRIMARY KEY,
            campaign_id TEXT,
            account_id TEXT,
            contact_id TEXT,
            subject TEXT,
            body TEXT,
            status TEXT,
            sent_at TEXT,
            tracking_id TEXT UNIQUE
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✓ Database initialized")

def add_gmail_account():
    """Add Gmail account to database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    account_id = hashlib.md5(GMAIL_EMAIL.encode()).hexdigest()[:8]
    
    cursor.execute('''
        INSERT OR REPLACE INTO email_accounts 
        (id, email, smtp_server, smtp_port, imap_server, imap_port, 
         app_password, status, warmup_score, daily_sent, daily_limit, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        account_id, GMAIL_EMAIL, "smtp.gmail.com", 465,
        "imap.gmail.com", 993, GMAIL_PASSWORD,
        "active", 50, 0, 50, datetime.now().isoformat()
    ))
    
    conn.commit()
    conn.close()
    print(f"✓ Added Gmail account: {GMAIL_EMAIL}")
    return account_id

def add_contacts():
    """Add the 3 Toronto HVAC contacts"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    contacts = [
        {
            "id": "fred-zolfaghar",
            "email": "fred@airmakers.ca",
            "first_name": "Fred",
            "last_name": "Zolfaghar",
            "company": "Air Makers",
            "address": "535 Millway Ave, Vaughan",
            "city": "Toronto",
            "state": "ON",
            "tags": json.dumps(["hvac", "b2b", "founder_1998", "mechanical_engineer"])
        },
        {
            "id": "laird-son",
            "email": "info@lairdandson.com",
            "first_name": "Team",
            "last_name": "Laird & Son",
            "company": "Laird & Son",
            "address": "Toronto GTA",
            "city": "Toronto",
            "state": "ON",
            "tags": json.dumps(["hvac", "b2b", "tssa_registered", "5m_insurance"])
        },
        {
            "id": "city-home-comfort",
            "email": "info@cityhomecomfort.ca",
            "first_name": "Team",
            "last_name": "City Home Comfort",
            "company": "City Home Comfort",
            "address": "710 Kingston Rd, Toronto",
            "city": "Toronto",
            "state": "ON",
            "tags": json.dumps(["hvac", "b2b", "family_owned", "since_1981", "24_7_service"])
        }
    ]
    
    for contact in contacts:
        cursor.execute('''
            INSERT OR REPLACE INTO contacts 
            (id, email, first_name, last_name, address, city, state, source, tags, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            contact["id"], contact["email"], contact["first_name"], contact["last_name"],
            contact["address"], contact["city"], contact["state"],
            "manual", contact["tags"], datetime.now().isoformat()
        ))
    
    conn.commit()
    conn.close()
    print(f"✓ Added {len(contacts)} contacts")

def get_email_templates():
    """Get personalized email templates for each company"""
    return {
        "fred-zolfaghar": {
            "subject": "Fred, I built an AI system that finds HVAC leads automatically",
            "body": """<html>
<body style='font-family: Arial, sans-serif; line-height: 1.6; color: #333;'>
<p>Hi Fred,</p>

<p>I came across Air Makers and was impressed — 27 years in business since 1998, founded by a mechanical engineer. That's the kind of quality operation that stands out in the GTA HVAC market.</p>

<p>I built something that might interest you: an AI-powered lead generation system specifically for HVAC contractors.</p>

<p><strong>What it does:</strong></p>
<ul>
<li>Finds homeowners in your service area with aging HVAC systems</li>
<li>Sends personalized cold emails that actually get responses</li>
<li>Delivers 5-10 qualified homeowner leads per week</li>
<li>No more paying HomeAdvisor $100+ per lead</li>
</ul>

<p>One contractor in Arizona booked 12 appointments in his first week using this.</p>

<p>Given Air Makers' reputation for quality installations and commercial work, I think this could help you scale without adding more to your plate.</p>

<p><strong>Interested in a 15-minute demo this week?</strong> I'll show you exactly how it works.</p>

<p>I have Tuesday afternoon or Thursday morning open.</p>

<p>Best,<br>
<strong>Smit Machhi</strong><br>
📞 (416) 555-0147</p>

<p style='font-size: 12px; color: #666; margin-top: 30px;'>P.S. Only taking on 3 more HVAC contractors this month to ensure quality support.</p>
</body>
</html>"""
        },
        "laird-son": {
            "subject": "Quick question about scaling Laird & Son's lead gen",
            "body": """<html>
<body style='font-family: Arial, sans-serif; line-height: 1.6; color: #333;'>
<p>Hi there,</p>

<p>I noticed Laird & Son is TSSA registered with HRAI membership and $5M liability coverage — that's the level of professionalism homeowners trust.</p>

<p>I built an AI system that could help you get more qualified leads without the HomeAdvisor fees.</p>

<p><strong>What it does:</strong></p>
<ul>
<li>Finds homeowners in Toronto with aging HVAC systems</li>
<li>Sends personalized outreach that gets 20-30% response rates</li>
<li>Delivers 5-10 qualified homeowner leads per week</li>
<li>Fully automated — runs in the background</li>
</ul>

<p>Given your strong reputation in the GTA, I think this could help you scale efficiently.</p>

<p><strong>Worth a 15-minute demo?</strong> I'll show you exactly how it works.</p>

<p>Available Tuesday afternoon or Thursday morning this week.</p>

<p>Best,<br>
<strong>Smit Machhi</strong><br>
📞 (416) 555-0147</p>

<p style='font-size: 12px; color: #666; margin-top: 30px;'>P.S. Currently limiting this to 3 HVAC contractors max to ensure personalized support.</p>
</body>
</html>"""
        },
        "city-home-comfort": {
            "subject": "44 years in business — time to add AI lead gen?",
            "body": """<html>
<body style='font-family: Arial, sans-serif; line-height: 1.6; color: #333;'>
<p>Hi there,</p>

<p>44 years as a family-owned HVAC business in Toronto — that's impressive. City Home Comfort has clearly earned its reputation.</p>

<p>I built something that might help you scale: an AI-powered lead generation system specifically for established HVAC contractors.</p>

<p><strong>What it does:</strong></p>
<ul>
<li>Finds homeowners in Toronto with 15+ year old HVAC systems</li>
<li>Sends personalized cold emails on your behalf</li>
<li>Gets you 5-10 qualified homeowner leads per week</li>
<li>24/7 automated — like having a sales rep that never sleeps</li>
</ul>

<p>One contractor in Mesa booked 12 appointments in his first week.</p>

<p>Given your 24/7 service model and TSSA certification, I think this would fit well with how you operate.</p>

<p><strong>Quick 15-minute demo this week?</strong> Tuesday afternoon or Thursday morning work for me.</p>

<p>Best,<br>
<strong>Smit Machhi</strong><br>
📞 (416) 555-0147</p>

<p style='font-size: 12px; color: #666; margin-top: 30px;'>P.S. Only onboarding 3 more contractors this month.</p>
</body>
</html>"""
        }
    }

def send_emails():
    """Send personalized emails to all 3 contacts"""
    templates = get_email_templates()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get contacts
    cursor.execute('SELECT * FROM contacts WHERE id IN (?, ?, ?)', 
                   ('fred-zolfaghar', 'laird-son', 'city-home-comfort'))
    contacts = cursor.fetchall()
    
    # Get account
    cursor.execute('SELECT * FROM email_accounts WHERE email = ?', (GMAIL_EMAIL,))
    account = cursor.fetchone()
    
    if not account:
        print("✗ Gmail account not found")
        conn.close()
        return
    
    account_id = account[0]
    smtp_server = account[2]
    smtp_port = account[3]
    app_password = account[6]
    
    sent_count = 0
    
    for contact in contacts:
        contact_id = contact[0]
        contact_email = contact[1]
        template = templates.get(contact_id)
        
        if not template:
            print(f"✗ No template for {contact_id}")
            continue
        
        try:
            # Build email
            msg = MIMEMultipart('alternative')
            msg['Subject'] = template["subject"]
            msg['From'] = GMAIL_EMAIL
            msg['To'] = contact_email
            
            msg.attach(MIMEText(template["body"], 'html'))
            
            # Send via SMTP
            with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
                server.login(GMAIL_EMAIL, app_password)
                server.send_message(msg)
            
            # Log the send
            tracking_id = hashlib.md5(f"b2b-outreach:{contact_email}:{datetime.now()}".encode()).hexdigest()[:16]
            cursor.execute('''
                INSERT INTO email_logs 
                (id, campaign_id, account_id, contact_id, subject, body, status, sent_at, tracking_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                hashlib.md5(f"{contact_id}:{datetime.now()}".encode()).hexdigest()[:16],
                "b2b-hvac-toronto-001",
                account_id,
                contact_id,
                template["subject"],
                template["body"],
                "sent",
                datetime.now().isoformat(),
                tracking_id
            ))
            
            print(f"✓ Sent to {contact_email}")
            sent_count += 1
            
        except Exception as e:
            print(f"✗ Failed to send to {contact_email}: {e}")
    
    conn.commit()
    conn.close()
    
    print(f"\n=== SUMMARY ===")
    print(f"Total emails sent: {sent_count}/3")
    return sent_count

if __name__ == "__main__":
    print("=== HVAC B2B Email Setup & Send ===\n")
    
    # Step 1: Initialize database
    init_db()
    
    # Step 2: Add Gmail account
    add_gmail_account()
    
    # Step 3: Add contacts
    add_contacts()
    
    # Step 4: Send emails
    print("\n--- Sending Emails ---")
    sent = send_emails()
    
    if sent == 3:
        print("\n✓ All 3 emails sent successfully!")
    else:
        print(f"\n⚠ Only {sent}/3 emails sent")
