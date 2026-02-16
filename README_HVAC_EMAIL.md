# HVAC Cold Email Automation Tool

A multi-account cold email system for HVAC contractors, modeled after Instantly.ai. Built for managing 10-50 email accounts, warming them up, sending campaigns, and tracking results.

## Files Created

| File | Description | Lines |
|------|-------------|-------|
| `email_automation.py` | Core engine - accounts, campaigns, sending, tracking | ~550 |
| `warmup_system.py` | Account warming - simulates conversations between accounts | ~250 |
| `template_library.json` | 10 HVAC-specific email templates | ~350 |
| `dashboard.html` | Simple stats dashboard (open in browser) | ~650 |

## Quick Start

### 1. Install Dependencies
```bash
pip install sqlite3  # Usually built-in
```

### 2. Add Email Accounts (Gmail/Google Workspace)
```bash
# Generate Gmail App Password at: https://myaccount.google.com/apppasswords
python email_automation.py add-account your-email@gmail.com "your-app-password"
```

### 3. Add Contacts
```bash
python email_automation.py add-contact homeowner@email.com John Doe "90210"
```

### 4. Run Warmup (First 1-2 Weeks)
```bash
# Create warmup pairs
python warmup_system.py pairs

# Run continuous warmup
python warmup_system.py run  # Runs indefinitely, Ctrl+C to stop

# After 50+ warmup score, promote to active
python warmup_system.py promote
```

### 5. Create & Run Campaign
```bash
# Create campaign
python email_automation.py create-campaign "Summer AC Tune-Up" hvac_seasonal_tuneup

# Run campaign (sends in batches)
python email_automation.py run-campaign CAMPAIGN_ID
```

### 6. View Dashboard
Open `dashboard.html` in your browser for stats view.

### 7. Check Stats
```bash
python email_automation.py stats
```

## Templates Available

| Template ID | Use Case |
|-------------|----------|
| `hvac_seasonal_tuneup` | Free AC inspection offer |
| `hvac_system_replacement` | Old system → new system pitch |
| `hvac_emergency_repair` | Same-day repair service |
| `hvac_maintenance_plan` | VIP membership program |
| `hvac_air_quality` | Indoor air quality testing |
| `hvac_follow_up` | Follow up after quote |
| `hvac_testimonial_request` | Ask for reviews |
| `hvac_winter_heating_check` | Pre-winter furnace check |
| `hvac_duct_cleaning` | Duct cleaning service |
| `hvac_referral_request` | Customer referral program |

## Database Schema

- `email_accounts` - All connected email accounts with warmup scores
- `contacts` - Homeowner leads with zip codes
- `campaigns` - Email campaigns with stats
- `email_logs` - Every email sent with tracking IDs
- `replies` - Unified inbox for all replies

## Warmup System Explained

New accounts start at "warming" status. The warmup system:
1. Pairs accounts together
2. Sends realistic emails between them
3. Checks/replies to build conversation threads
4. Increases warmup score over time
5. Auto-promotes to "active" at score 50+

This builds sender reputation with Gmail so cold emails land in inbox, not spam.

## Campaign Sending Logic

- Rotates through active accounts
- Respects daily limits per account
- Adds 2-5 minute random delays between sends
- Tracks opens, clicks, replies via tracking pixel

## Production Notes (MVP Limitations)

- Tracking pixel needs hosting (use ngrok or server)
- No built-in contact scraping (buy lists or use external tools)
- CLI only - dashboard is static HTML (needs API backend for live data)
- SQLite for MVP (migrate to PostgreSQL for scale)

## Next Steps for Full Production

1. Add Flask/FastAPI backend for live dashboard
2. Implement real tracking pixel endpoint
3. Add contact import from CSV
4. Add unsubscribe handling
5. Add bounce detection
6. Add A/B testing for templates
7. Add automated reply handling/AI responses
