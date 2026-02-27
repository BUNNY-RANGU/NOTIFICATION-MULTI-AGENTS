# utils/whatsapp_sender.py
# =====================================================
# JOB: Send WhatsApp alert to shop owner
# Uses Twilio free sandbox
# =====================================================

import os
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()


def send_whatsapp_report(final_report, analysis):
    """
    Sends the AI report via WhatsApp.
    Keeps it under 300 words for WhatsApp.
    """
    print("\n📱 Sending WhatsApp message...")

    # Get credentials from .env
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token  = os.getenv("TWILIO_AUTH_TOKEN")
    from_number = os.getenv("TWILIO_WHATSAPP_FROM")
    to_number   = os.getenv("OWNER_WHATSAPP")

    # Check all credentials exist
    if not account_sid or not auth_token:
        print("❌ Twilio credentials missing in .env!")
        return False

    if not to_number:
        print("❌ OWNER_WHATSAPP missing in .env!")
        return False

    try:
        # Connect to Twilio
        client = Client(account_sid, auth_token)

        # Make the report shorter for WhatsApp
        # WhatsApp has character limits
        short_report = make_short_report(final_report, analysis)

        # Send the WhatsApp message
        message = client.messages.create(
            from_=from_number,
            to=to_number,
            body=short_report
        )

        print(f"✅ WhatsApp sent! Message ID: {message.sid}")
        return True

    except Exception as e:
        print(f"❌ WhatsApp failed: {e}")
        print("   Check your Twilio credentials in .env")
        return False


def make_short_report(final_report, analysis):
    """
    Makes a SHORT version of report for WhatsApp.
    Under 300 words.
    """
    from datetime import date
    today = date.today().strftime("%d %B %Y")

    # Count issues
    critical = analysis['critical_count']
    money    = analysis['total_potential_loss']
    savings  = round(money * 0.7, 2)

    # Take first 800 characters of report
    # to keep WhatsApp message short
    short = final_report[:800] if len(final_report) > 800 else final_report

    return f"""🏪 *SHOP REPORT — {today}*
━━━━━━━━━━━━━━━━━━━━━━
🚨 Critical Issues: {critical}
💰 Money at Risk: ₹{money}

{short}

💰 *Save ₹{savings} if you act NOW!*
━━━━━━━━━━━━━━━━━━━━━━
🤖 _Sent by your Shop AI Agent_"""