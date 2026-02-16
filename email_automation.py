#!/usr/bin/env python3
"""
HVAC Cold Email Automation - Core Engine
Manages multiple email accounts, sends campaigns, tracks metrics
"""

import json
import sqlite3
import smtplib
import imaplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import random
import hashlib
import os
from dataclasses import dataclass, asdict
from pathlib import Path

# Database setup
DB_PATH = Path("email_automation.db")

@dataclass
class EmailAccount:
    id: str
    email: str
    smtp_server: str
    smtp_port: int
    imap_server: str
    imap_port: int
    app_password: str  # Gmail App Password
    status: str = "active"  # active, warming, paused, blocked
    warmup_score: int = 0  # 0-100 warmup reputation
    daily_sent: int = 0
    daily_limit: int = 50
    created_at: str = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()

@dataclass
class Contact:
    id: str
    email: str
    first_name: str
    last_name: str
    address: str
    zip_code: str
    city: str
    state: str
    home_age: Optional[int] = None
    source: str = "manual"
    tags: List[str] = None
    created_at: str = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()

@dataclass
class Campaign:
    id: str
    name: str
    template_id: str
    status: str = "draft"  # draft, active, paused, completed
    target_zips: List[str] = None
    sent_count: int = 0
    open_count: int = 0
    click_count: int = 0
    reply_count: int = 0
    created_at: str = None
    started_at: str = None
    
    def __post_init__(self):
        if self.target_zips is None:
            self.target_zips = []
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()

@dataclass
class EmailLog:
    id: str
    campaign_id: str
    account_id: str
    contact_id: str
    subject: str
    body: str
    status: str = "pending"  # pending, sent, delivered, opened, clicked, replied, bounced
    sent_at: str = None
    opened_at: str = None
    clicked_at: str = None
    replied_at: str = None
    tracking_id: str = None
    
    def __post_init__(self):
        if self.sent_at is None:
            self.sent_at = datetime.now().isoformat()
        if self.tracking_id is None:
            self.tracking_id = hashlib.md5(f"{self.campaign_id}:{self.contact_id}:{datetime.now()}".encode()).hexdigest()[:16]


class Database:
    def __init__(self, db_path: str = None):
        self.db_path = db_path or DB_PATH
        self.init_db()
    
    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Email accounts table
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
        
        # Contacts table
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
        
        # Campaigns table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS campaigns (
                id TEXT PRIMARY KEY,
                name TEXT,
                template_id TEXT,
                status TEXT,
                target_zips TEXT,
                sent_count INTEGER,
                open_count INTEGER,
                click_count INTEGER,
                reply_count INTEGER,
                created_at TEXT,
                started_at TEXT
            )
        ''')
        
        # Email logs table (tracks every email sent)
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
                opened_at TEXT,
                clicked_at TEXT,
                replied_at TEXT,
                tracking_id TEXT UNIQUE
            )
        ''')
        
        # Replies table (unified inbox)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS replies (
                id TEXT PRIMARY KEY,
                account_id TEXT,
                contact_email TEXT,
                subject TEXT,
                body TEXT,
                received_at TEXT,
                is_read INTEGER DEFAULT 0,
                campaign_id TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_account(self, account: EmailAccount):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO email_accounts 
            (id, email, smtp_server, smtp_port, imap_server, imap_port, 
             app_password, status, warmup_score, daily_sent, daily_limit, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            account.id, account.email, account.smtp_server, account.smtp_port,
            account.imap_server, account.imap_port, account.app_password,
            account.status, account.warmup_score, account.daily_sent, 
            account.daily_limit, account.created_at
        ))
        conn.commit()
        conn.close()
    
    def get_accounts(self, status: str = None) -> List[EmailAccount]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if status:
            cursor.execute('SELECT * FROM email_accounts WHERE status = ?', (status,))
        else:
            cursor.execute('SELECT * FROM email_accounts')
        
        rows = cursor.fetchall()
        conn.close()
        
        accounts = []
        for row in rows:
            accounts.append(EmailAccount(
                id=row[0], email=row[1], smtp_server=row[2], smtp_port=row[3],
                imap_server=row[4], imap_port=row[5], app_password=row[6],
                status=row[7], warmup_score=row[8], daily_sent=row[9],
                daily_limit=row[10], created_at=row[11]
            ))
        return accounts
    
    def save_contact(self, contact: Contact):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO contacts 
            (id, email, first_name, last_name, address, zip_code, city, state,
             home_age, source, tags, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            contact.id, contact.email, contact.first_name, contact.last_name,
            contact.address, contact.zip_code, contact.city, contact.state,
            contact.home_age, contact.source, json.dumps(contact.tags), contact.created_at
        ))
        conn.commit()
        conn.close()
    
    def get_contacts_by_zip(self, zip_codes: List[str]) -> List[Contact]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        placeholders = ','.join('?' * len(zip_codes))
        cursor.execute(f'SELECT * FROM contacts WHERE zip_code IN ({placeholders})', zip_codes)
        
        rows = cursor.fetchall()
        conn.close()
        
        contacts = []
        for row in rows:
            contacts.append(Contact(
                id=row[0], email=row[1], first_name=row[2], last_name=row[3],
                address=row[4], zip_code=row[5], city=row[6], state=row[7],
                home_age=row[8], source=row[9], 
                tags=json.loads(row[10]) if row[10] else [],
                created_at=row[11]
            ))
        return contacts
    
    def save_campaign(self, campaign: Campaign):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO campaigns 
            (id, name, template_id, status, target_zips, sent_count, open_count,
             click_count, reply_count, created_at, started_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            campaign.id, campaign.name, campaign.template_id, campaign.status,
            json.dumps(campaign.target_zips), campaign.sent_count, campaign.open_count,
            campaign.click_count, campaign.reply_count, campaign.created_at,
            campaign.started_at
        ))
        conn.commit()
        conn.close()
    
    def get_campaign(self, campaign_id: str) -> Optional[Campaign]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM campaigns WHERE id = ?', (campaign_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return Campaign(
            id=row[0], name=row[1], template_id=row[2], status=row[3],
            target_zips=json.loads(row[4]) if row[4] else [],
            sent_count=row[5], open_count=row[6], click_count=row[7],
            reply_count=row[8], created_at=row[9], started_at=row[10]
        )
    
    def log_email(self, log: EmailLog):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO email_logs 
            (id, campaign_id, account_id, contact_id, subject, body, status,
             sent_at, opened_at, clicked_at, replied_at, tracking_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            log.id, log.campaign_id, log.account_id, log.contact_id,
            log.subject, log.body, log.status, log.sent_at, log.opened_at,
            log.clicked_at, log.replied_at, log.tracking_id
        ))
        conn.commit()
        conn.close()
    
    def get_stats(self) -> Dict:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Account stats
        cursor.execute('SELECT COUNT(*), SUM(daily_sent) FROM email_accounts WHERE status = "active"')
        account_row = cursor.fetchone()
        
        # Campaign stats
        cursor.execute('''
            SELECT SUM(sent_count), SUM(open_count), SUM(click_count), SUM(reply_count)
            FROM campaigns
        ''')
        campaign_row = cursor.fetchone()
        
        # Reply count
        cursor.execute('SELECT COUNT(*) FROM replies WHERE is_read = 0')
        unread_replies = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "active_accounts": account_row[0] or 0,
            "emails_sent_today": account_row[1] or 0,
            "total_sent": campaign_row[0] or 0,
            "total_opens": campaign_row[1] or 0,
            "total_clicks": campaign_row[2] or 0,
            "total_replies": campaign_row[3] or 0,
            "unread_replies": unread_replies
        }


class TemplateEngine:
    def __init__(self, templates_path: str = "template_library.json"):
        self.templates_path = templates_path
        self.templates = self.load_templates()
    
    def load_templates(self) -> Dict:
        if not os.path.exists(self.templates_path):
            return {}
        with open(self.templates_path, 'r') as f:
            return json.load(f)
    
    def render(self, template_id: str, contact: Contact, **kwargs) -> tuple:
        template = self.templates.get(template_id, {})
        subject = template.get('subject', '')
        body = template.get('body', '')
        
        # Replace variables
        variables = {
            '{{first_name}}': contact.first_name,
            '{{last_name}}': contact.last_name,
            '{{city}}': contact.city,
            '{{zip_code}}': contact.zip_code,
            '{{address}}': contact.address,
            '{{home_age}}': str(contact.home_age) if contact.home_age else 'your home',
        }
        variables.update(kwargs)
        
        for var, value in variables.items():
            subject = subject.replace(var, value)
            body = body.replace(var, value)
        
        return subject, body


class EmailSender:
    def __init__(self, db: Database):
        self.db = db
        self.template_engine = TemplateEngine()
    
    def send_email(self, account: EmailAccount, contact: Contact, 
                   campaign_id: str, template_id: str) -> bool:
        try:
            # Check daily limit
            if account.daily_sent >= account.daily_limit:
                print(f"Account {account.email} hit daily limit")
                return False
            
            # Render template
            subject, body = self.template_engine.render(template_id, contact)
            
            # Add tracking pixel
            tracking_id = hashlib.md5(f"{campaign_id}:{contact.email}:{datetime.now()}".encode()).hexdigest()[:16]
            tracking_pixel = f'<img src="http://yourdomain.com/track/{tracking_id}" width="1" height="1" />'
            body += f"\n\n{tracking_pixel}"
            
            # Build email
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = account.email
            msg['To'] = contact.email
            
            msg.attach(MIMEText(body, 'html'))
            
            # Send via SMTP
            with smtplib.SMTP_SSL(account.smtp_server, account.smtp_port) as server:
                server.login(account.email, account.app_password)
                server.send_message(msg)
            
            # Log the send
            email_log = EmailLog(
                id=tracking_id,
                campaign_id=campaign_id,
                account_id=account.id,
                contact_id=contact.id,
                subject=subject,
                body=body,
                status="sent",
                tracking_id=tracking_id
            )
            self.db.log_email(email_log)
            
            # Update account daily sent
            account.daily_sent += 1
            self.db.save_account(account)
            
            print(f"✓ Sent to {contact.email} from {account.email}")
            return True
            
        except Exception as e:
            print(f"✗ Failed to send to {contact.email}: {e}")
            return False
    
    def run_campaign(self, campaign_id: str, batch_size: int = 10):
        campaign = self.db.get_campaign(campaign_id)
        if not campaign:
            print(f"Campaign {campaign_id} not found")
            return
        
        # Get active accounts
        accounts = self.db.get_accounts(status="active")
        if not accounts:
            print("No active accounts available")
            return
        
        # Get contacts for target zips
        contacts = self.db.get_contacts_by_zip(campaign.target_zips)
        print(f"Found {len(contacts)} contacts in target zip codes")
        
        # Rotate through accounts
        account_idx = 0
        sent_count = 0
        
        for contact in contacts[:batch_size]:
            account = accounts[account_idx % len(accounts)]
            
            if self.send_email(account, contact, campaign_id, campaign.template_id):
                sent_count += 1
                
                # Rotate account
                account_idx += 1
                
                # Add delay between sends (2-5 minutes)
                import time
                delay = random.randint(120, 300)
                time.sleep(delay)
        
        # Update campaign stats
        campaign.sent_count += sent_count
        campaign.status = "active"
        self.db.save_campaign(campaign)
        
        print(f"Campaign batch complete: {sent_count} emails sent")


class InboxMonitor:
    def __init__(self, db: Database):
        self.db = db
    
    def check_replies(self, account: EmailAccount):
        try:
            mail = imaplib.IMAP4_SSL(account.imap_server, account.imap_port)
            mail.login(account.email, account.app_password)
            mail.select('inbox')
            
            # Search for unread emails
            _, messages = mail.search(None, 'UNSEEN')
            
            for msg_num in messages[0].split():
                _, msg_data = mail.fetch(msg_num, '(RFC822)')
                raw_email = msg_data[0][1]
                msg = email.message_from_bytes(raw_email)
                
                # Parse email
                subject = msg['Subject']
                from_email = msg['From']
                date = msg['Date']
                
                # Get body
                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            body = part.get_payload(decode=True).decode()
                            break
                else:
                    body = msg.get_payload(decode=True).decode()
                
                # Save reply
                reply_id = hashlib.md5(f"{account.id}:{from_email}:{date}".encode()).hexdigest()[:16]
                conn = sqlite3.connect(self.db.db_path)
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR IGNORE INTO replies 
                    (id, account_id, contact_email, subject, body, received_at, is_read)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (reply_id, account.id, from_email, subject, body, 
                      datetime.now().isoformat(), 0))
                conn.commit()
                conn.close()
                
                print(f"Reply from {from_email}: {subject[:50]}...")
            
            mail.logout()
            
        except Exception as e:
            print(f"Failed to check {account.email}: {e}")


# CLI Interface
if __name__ == "__main__":
    import sys
    import uuid
    
    db = Database()
    
    if len(sys.argv) < 2:
        print("HVAC Email Automation Tool")
        print("\nUsage:")
        print("  python email_automation.py add-account <email> <app_password>")
        print("  python email_automation.py add-contact <email> <first_name> <last_name> <zip>")
        print("  python email_automation.py create-campaign <name> <template_id>")
        print("  python email_automation.py run-campaign <campaign_id>")
        print("  python email_automation.py stats")
        sys.exit(0)
    
    cmd = sys.argv[1]
    
    if cmd == "add-account":
        if len(sys.argv) < 4:
            print("Usage: add-account <email> <app_password>")
            sys.exit(1)
        
        email_addr = sys.argv[2]
        app_password = sys.argv[3]
        
        account = EmailAccount(
            id=str(uuid.uuid4())[:8],
            email=email_addr,
            smtp_server="smtp.gmail.com",
            smtp_port=465,
            imap_server="imap.gmail.com",
            imap_port=993,
            app_password=app_password,
            status="warming",  # Start in warmup
            daily_limit=random.randint(40, 60)  # Randomize to look natural
        )
        db.save_account(account)
        print(f"Added account: {email_addr} (ID: {account.id})")
    
    elif cmd == "add-contact":
        if len(sys.argv) < 6:
            print("Usage: add-contact <email> <first_name> <last_name> <zip>")
            sys.exit(1)
        
        contact = Contact(
            id=str(uuid.uuid4())[:8],
            email=sys.argv[2],
            first_name=sys.argv[3],
            last_name=sys.argv[4],
            zip_code=sys.argv[5],
            address="",
            city="",
            state=""
        )
        db.save_contact(contact)
        print(f"Added contact: {contact.email}")
    
    elif cmd == "create-campaign":
        if len(sys.argv) < 4:
            print("Usage: create-campaign <name> <template_id>")
            sys.exit(1)
        
        campaign = Campaign(
            id=str(uuid.uuid4())[:8],
            name=sys.argv[2],
            template_id=sys.argv[3],
            target_zips=["90210"]  # Default, customize as needed
        )
        db.save_campaign(campaign)
        print(f"Created campaign: {campaign.name} (ID: {campaign.id})")
    
    elif cmd == "run-campaign":
        if len(sys.argv) < 3:
            print("Usage: run-campaign <campaign_id>")
            sys.exit(1)
        
        sender = EmailSender(db)
        sender.run_campaign(sys.argv[2])
    
    elif cmd == "stats":
        stats = db.get_stats()
        print("\n=== HVAC Email Automation Stats ===")
        print(f"Active Accounts: {stats['active_accounts']}")
        print(f"Emails Sent Today: {stats['emails_sent_today']}")
        print(f"Total Sent: {stats['total_sent']}")
        print(f"Total Opens: {stats['total_opens']}")
        print(f"Total Clicks: {stats['total_clicks']}")
        print(f"Total Replies: {stats['total_replies']}")
        print(f"Unread Replies: {stats['unread_replies']}")
    
    else:
        print(f"Unknown command: {cmd}")
