#!/usr/bin/env python3
"""
Email Account Warmup System
Simulates natural email conversations to build sender reputation
"""

import random
import time
import smtplib
import imaplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import List, Dict
import json
import sqlite3
from email_automation import Database, EmailAccount


class WarmupEngine:
    """
    Warms up email accounts by sending emails between them.
    Simulates real conversations to build sender reputation with Gmail.
    """
    
    WARMUP_SUBJECTS = [
        "Quick question about your service",
        "Thanks for the info",
        "Following up",
        "Quick update",
        "Re: Our conversation",
        "Checking in",
        "Great talking to you",
        "Quick favor",
    ]
    
    WARMUP_BODIES = [
        """Hi there,

Just wanted to follow up on our conversation. Thanks for getting back to me!

Best regards""",
        
        """Hey,

Quick question - do you have availability next week? Let me know what works.

Thanks!""",
        
        """Hi,

Thanks for sending that over. I'll review and get back to you soon.

Talk soon,""",
        
        """Hello,

Appreciate the quick response. That sounds good to me.

Best,""",
        
        """Hi,

Just checking in to see if you had a chance to look at my previous email?

Thanks,""",
    ]
    
    REPLY_BODIES = [
        """Hey,

Yes, that works perfectly. Thanks for confirming!

Best""",
        
        """Hi,

No problem at all. I'll be in touch soon.

Regards,""",
        
        """Thanks for the update! Much appreciated.

Talk soon,""",
    ]
    
    def __init__(self, db: Database):
        self.db = db
        self.warmup_pairs = []  # Pairs of accounts that send to each other
    
    def create_warmup_pairs(self):
        """Create pairs of accounts to send warmup emails between them"""
        accounts = self.db.get_accounts(status="warming")
        
        # Shuffle and pair up accounts
        random.shuffle(accounts)
        pairs = []
        
        for i in range(0, len(accounts) - 1, 2):
            pairs.append((accounts[i], accounts[i + 1]))
        
        self.warmup_pairs = pairs
        print(f"Created {len(pairs)} warmup pairs from {len(accounts)} accounts")
        return pairs
    
    def send_warmup_email(self, from_account: EmailAccount, 
                          to_account: EmailAccount, 
                          is_reply: bool = False) -> bool:
        """Send a warmup email from one account to another"""
        try:
            # Build email
            msg = MIMEMultipart('alternative')
            msg['Subject'] = random.choice(self.WARMUP_SUBJECTS)
            msg['From'] = from_account.email
            msg['To'] = to_account.email
            
            # Select body
            if is_reply:
                body = random.choice(self.REPLY_BODIES)
            else:
                body = random.choice(self.WARMUP_BODIES)
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send
            with smtplib.SMTP_SSL(from_account.smtp_server, from_account.smtp_port) as server:
                server.login(from_account.email, from_account.app_password)
                server.send_message(msg)
            
            print(f"✓ Warmup: {from_account.email} → {to_account.email}")
            return True
            
        except Exception as e:
            print(f"✗ Warmup failed: {e}")
            return False
    
    def check_and_reply(self, account: EmailAccount, pair_account: EmailAccount):
        """Check for warmup emails and reply to them"""
        try:
            mail = imaplib.IMAP4_SSL(account.imap_server, account.imap_port)
            mail.login(account.email, account.app_password)
            mail.select('inbox')
            
            # Search for emails from warmup partner
            _, messages = mail.search(None, f'FROM "{pair_account.email}"')
            
            reply_count = 0
            for msg_num in messages[0].split()[:3]:  # Max 3 replies per check
                # Mark as seen and reply
                _, msg_data = mail.fetch(msg_num, '(RFC822)')
                raw_email = msg_data[0][1]
                msg = email.message_from_bytes(raw_email)
                
                subject = msg['Subject']
                
                # Send reply
                if not subject.startswith("Re:"):
                    self.send_warmup_email(account, pair_account, is_reply=True)
                    reply_count += 1
            
            mail.logout()
            return reply_count
            
        except Exception as e:
            print(f"Failed to check replies for {account.email}: {e}")
            return 0
    
    def warmup_cycle(self):
        """Run one warmup cycle - send emails and check replies"""
        print(f"\n=== Warmup Cycle {datetime.now().strftime('%Y-%m-%d %H:%M')} ===")
        
        if not self.warmup_pairs:
            self.create_warmup_pairs()
        
        total_sent = 0
        
        for account_a, account_b in self.warmup_pairs:
            # A sends to B (random chance)
            if random.random() > 0.3:  # 70% chance to send
                if self.send_warmup_email(account_a, account_b):
                    total_sent += 1
                    
                    # Update warmup score
                    account_a.warmup_score = min(100, account_a.warmup_score + 1)
                    self.db.save_account(account_a)
                
                # Random delay
                time.sleep(random.randint(30, 120))
            
            # B checks inbox and replies
            replies = self.check_and_reply(account_b, account_a)
            total_sent += replies
            
            # Random delay
            time.sleep(random.randint(30, 120))
            
            # B sends to A (random chance, lower)
            if random.random() > 0.5:  # 50% chance
                if self.send_warmup_email(account_b, account_a):
                    total_sent += 1
                    account_b.warmup_score = min(100, account_b.warmup_score + 1)
                    self.db.save_account(account_b)
                
                time.sleep(random.randint(30, 120))
            
            # A checks inbox and replies
            replies = self.check_and_reply(account_a, account_b)
            total_sent += replies
        
        print(f"Warmup cycle complete: {total_sent} emails exchanged")
        return total_sent
    
    def run_continuous(self, cycles: int = None):
        """Run warmup continuously with delays between cycles"""
        cycle_count = 0
        
        while True:
            self.warmup_cycle()
            cycle_count += 1
            
            if cycles and cycle_count >= cycles:
                print(f"Completed {cycles} warmup cycles")
                break
            
            # Wait 2-4 hours between cycles
            wait_hours = random.uniform(2, 4)
            print(f"Waiting {wait_hours:.1f} hours until next cycle...")
            time.sleep(wait_hours * 3600)
    
    def promote_accounts(self, min_score: int = 50):
        """Promote accounts from 'warming' to 'active' if warmup score is high enough"""
        accounts = self.db.get_accounts(status="warming")
        promoted = 0
        
        for account in accounts:
            if account.warmup_score >= min_score:
                account.status = "active"
                self.db.save_account(account)
                promoted += 1
                print(f"Promoted {account.email} to active (score: {account.warmup_score})")
        
        print(f"Promoted {promoted} accounts to active status")
        return promoted


def generate_warmup_schedule(days: int = 14) -> List[Dict]:
    """Generate a warmup schedule for new accounts"""
    schedule = []
    
    daily_limits = [
        5, 8, 12, 15, 18,  # Week 1
        22, 25, 28, 32, 35,  # Week 2
        38, 42, 45, 50  # Final ramp
    ]
    
    for day in range(min(days, len(daily_limits))):
        schedule.append({
            "day": day + 1,
            "max_emails": daily_limits[day],
            "warmup_emails": min(5, daily_limits[day] // 3),
            "actions": ["send_warmup", "check_replies", "send_warmup"]
        })
    
    return schedule


# CLI Interface
if __name__ == "__main__":
    import sys
    
    db = Database()
    engine = WarmupEngine(db)
    
    if len(sys.argv) < 2:
        print("Email Warmup System")
        print("\nUsage:")
        print("  python warmup_system.py pairs          - Create warmup pairs")
        print("  python warmup_system.py cycle          - Run one warmup cycle")
        print("  python warmup_system.py run [cycles]   - Run continuous warmup")
        print("  python warmup_system.py promote        - Promote ready accounts")
        print("  python warmup_system.py schedule       - Show warmup schedule")
        sys.exit(0)
    
    cmd = sys.argv[1]
    
    if cmd == "pairs":
        engine.create_warmup_pairs()
    
    elif cmd == "cycle":
        engine.warmup_cycle()
    
    elif cmd == "run":
        cycles = int(sys.argv[2]) if len(sys.argv) > 2 else None
        engine.run_continuous(cycles)
    
    elif cmd == "promote":
        engine.promote_accounts()
    
    elif cmd == "schedule":
        schedule = generate_warmup_schedule()
        print("\n=== 14-Day Warmup Schedule ===")
        for day in schedule:
            print(f"Day {day['day']:2d}: Max {day['max_emails']:2d} emails, "
                  f"{day['warmup_emails']} warmup exchanges")
    
    else:
        print(f"Unknown command: {cmd}")
