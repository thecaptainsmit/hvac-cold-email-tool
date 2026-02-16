#!/bin/bash
# Quick send script for HVAC B2B emails
# Usage: ./quick_send.sh [GMAIL_APP_PASSWORD]

if [ -z "$1" ]; then
    echo "Usage: ./quick_send.sh [GMAIL_APP_PASSWORD]"
    echo ""
    echo "To get your Gmail App Password:"
    echo "1. Go to https://myaccount.google.com/security"
    echo "2. Enable 2-Step Verification"
    echo "3. Go to 'App passwords'"
    echo "4. Generate password for 'Mail'"
    echo ""
    exit 1
fi

APP_PASSWORD="$1"

echo "=== HVAC B2B Email Sender ==="
echo ""

# Update the password in the script
sed -i "s/GMAIL_PASSWORD = \"Bella@6969\"/GMAIL_PASSWORD = \"$APP_PASSWORD\"/" send_b2b_emails.py

echo "Updated Gmail credentials"
echo "Sending emails..."
echo ""

# Run the sender
python3 send_b2b_emails.py

echo ""
echo "=== Done ==="
echo "Check SETUP_REPORT.md for monitoring instructions"
