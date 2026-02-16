# HVAC Cold Email Tool - Setup Report

## Date: February 16, 2026

---

## ✅ COMPLETED

### 1. Gmail Account Configuration
- **Email**: debug.grace@gmail.com
- **Password**: Bella@6969 (stored in email_automation.db)
- **SMTP Server**: smtp.gmail.com:465
- **IMAP Server**: imap.gmail.com:993
- **Status**: Configured in database

### 2. Contact Database Setup
Added 3 Toronto HVAC contractors with personalized research:

| Company | Contact | Research Notes |
|---------|---------|----------------|
| **Air Makers** | fred@airmakers.ca | Founded 1998 by Fred Zolfaghar (mechanical engineer), 27 years in business, residential & commercial |
| **Laird & Son** | info@lairdandson.com | TSSA registered, HRAI membership, $5M liability insurance, Toronto's #1 rated |
| **City Home Comfort** | info@cityhomecomfort.ca | Family-owned since 1981 (44 years), 24/7 service, TSSA-certified, East Toronto |

### 3. Email Templates Created
Personalized B2B outreach emails for each company:

**Email Angle**: "I built an AI system that finds HVAC leads automatically. Gets 5-10 qualified homeowner leads per week."

**Personalization per company**:
- **Air Makers**: References 27-year history, mechanical engineer founder, GTA reputation
- **Laird & Son**: Mentions TSSA registration, HRAI membership, professional standards
- **City Home Comfort**: Highlights 44 years family-owned, 24/7 service model

### 4. GitHub Repo Preparation
- **Local repo**: Initialized and committed
- **Files committed**:
  - email_automation.py (core engine)
  - send_b2b_emails.py (B2B outreach script)
  - template_library.json (email templates)
  - warmup_system.py (account warmup)
  - monitor.py (inbox monitoring)
  - README_HVAC_EMAIL.md (documentation)

---

## ⚠️ NEEDS MANUAL COMPLETION

### 1. Gmail SMTP Configuration
**Issue**: Gmail requires an App Password when 2FA is enabled

**Steps to fix**:
1. Go to https://myaccount.google.com/security
2. Enable 2-Step Verification if not already on
3. Go to "App passwords" section
4. Generate a new app password for "Mail"
5. Replace the password in the script or use:
   ```bash
   python3 email_automation.py add-account debug.grace@gmail.com [APP_PASSWORD]
   ```

### 2. Send the Emails
Once Gmail App Password is configured:

```bash
cd /root/.openclaw/workspace
python3 send_b2b_emails.py
```

This will:
- Send personalized emails to all 3 contacts
- Log sends to email_automation.db
- Create tracking IDs for monitoring opens/replies

### 3. Create GitHub Repository
**GitHub no longer supports password auth**. You need a Personal Access Token:

1. Go to https://github.com/settings/tokens
2. Generate new token (classic) with "repo" scope
3. Create the repo:
   ```bash
   curl -X POST -H "Authorization: token YOUR_TOKEN" \
     -H "Accept: application/vnd.github.v3+json" \
     https://api.github.com/user/repos \
     -d '{"name":"hvac-cold-email-tool","description":"AI-powered cold email automation for HVAC contractors","private":false}'
   ```
4. Push code:
   ```bash
   cd /root/.openclaw/workspace
   git remote set-url origin https://thecaptainsmit:YOUR_TOKEN@github.com/thecaptainsmit/hvac-cold-email-tool.git
   git push -u origin master
   ```

---

## 📊 CURRENT STATUS

| Task | Status |
|------|--------|
| Gmail configured in DB | ✅ Done |
| 3 Contacts researched & added | ✅ Done |
| Personalized templates created | ✅ Done |
| Code committed to local git | ✅ Done |
| Emails sent | ⏳ Blocked (need Gmail App Password) |
| GitHub repo created | ⏳ Blocked (need Personal Access Token) |

---

## 📧 EMAIL PREVIEW

### Air Makers (Fred Zolfaghar)
```
Subject: Fred, I built an AI system that finds HVAC leads automatically

Hi Fred,

I came across Air Makers and was impressed — 27 years in business since 1998, 
founded by a mechanical engineer. That's the kind of quality operation that 
stands out in the GTA HVAC market.

I built something that might interest you: an AI-powered lead generation system 
specifically for HVAC contractors.

What it does:
• Finds homeowners in your service area with aging HVAC systems
• Sends personalized cold emails that actually get responses
• Delivers 5-10 qualified homeowner leads per week
• No more paying HomeAdvisor $100+ per lead

...
```

### Laird & Son
```
Subject: Quick question about scaling Laird & Son's lead gen

Hi there,

I noticed Laird & Son is TSSA registered with HRAI membership and $5M liability 
coverage — that's the level of professionalism homeowners trust.

...
```

### City Home Comfort
```
Subject: 44 years in business — time to add AI lead gen?

Hi there,

44 years as a family-owned HVAC business in Toronto — that's impressive. 
City Home Comfort has clearly earned its reputation.

...
```

---

## 🔍 MONITORING REPLIES

After emails are sent, check for replies:

```bash
# Check database for sent emails
sqlite3 email_automation.db "SELECT * FROM email_logs;"

# Monitor inbox for replies (once IMAP is working)
python3 email_automation.py check-replies
```

---

## 📝 FILES CREATED

- `/root/.openclaw/workspace/send_b2b_emails.py` - B2B outreach automation
- `/root/.openclaw/workspace/email_automation.db` - SQLite database with contacts & logs

---

## NEXT STEPS

1. **Immediate**: Generate Gmail App Password and re-run `send_b2b_emails.py`
2. **Create GitHub repo** with Personal Access Token
3. **Monitor replies** in inbox over next 24-48 hours
4. **Follow up** with any responders

---

*Report generated: February 16, 2026*
