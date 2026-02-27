# utils/email_sender.py
# =====================================================
# JOB: Send report using Brevo (FREE — 300 emails/day)
# No Gmail password needed! Just API key!
# =====================================================

import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
import os
from datetime import date
from dotenv import load_dotenv

load_dotenv()


def send_email_report(final_report, analysis):
    """
    Sends beautiful HTML email report using Brevo.
    Completely free. No Gmail passwords needed.
    """
    print("\n📧 Sending email via Brevo...")

    # Get settings from .env
    brevo_api_key = os.getenv("BREVO_API_KEY")
    owner_email   = os.getenv("OWNER_EMAIL")
    owner_name    = os.getenv("OWNER_NAME", "Shop Owner")
    sender_email  = os.getenv("SENDER_EMAIL")
    sender_name   = os.getenv("SENDER_NAME", "Shop AI Agent")

    # Check keys exist
    if not brevo_api_key:
        print("❌ BREVO_API_KEY missing in .env!")
        return False

    if not owner_email:
        print("❌ OWNER_EMAIL missing in .env!")
        return False

    today = date.today().strftime("%d %B %Y")

    # ── Configure Brevo connection
    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key["api-key"] = brevo_api_key
    api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
        sib_api_v3_sdk.ApiClient(configuration)
    )

    # ── Build beautiful HTML email
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{
            font-family: Arial, sans-serif;
            background: #f4f4f4;
            margin: 0;
            padding: 20px;
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }}
        .header {{
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 26px;
        }}
        .header p {{
            margin: 8px 0 0 0;
            opacity: 0.9;
            font-size: 14px;
        }}
        .boxes {{
            display: flex;
            padding: 20px;
            gap: 10px;
        }}
        .box {{
            flex: 1;
            padding: 15px;
            border-radius: 10px;
            text-align: center;
        }}
        .red   {{ background: #fff5f5; border: 2px solid #fc8181; }}
        .orange{{ background: #fffaf0; border: 2px solid #f6ad55; }}
        .green {{ background: #f0fff4; border: 2px solid #68d391; }}
        .num   {{ font-size: 36px; font-weight: bold; display: block; }}
        .lbl   {{ font-size: 11px; color: #666; margin-top: 4px; }}
        .section {{
            padding: 20px;
            border-top: 1px solid #eee;
        }}
        .section h2 {{
            color: #444;
            font-size: 16px;
            margin: 0 0 12px 0;
        }}
        .report-box {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            white-space: pre-line;
            font-size: 14px;
            line-height: 2;
            color: #333;
            border-left: 4px solid #667eea;
        }}
        .savings {{
            background: linear-gradient(135deg, #11998e, #38ef7d);
            color: white;
            padding: 25px;
            text-align: center;
            font-size: 22px;
            font-weight: bold;
        }}
        .footer {{
            padding: 15px;
            text-align: center;
            color: #aaa;
            font-size: 12px;
            background: #f8f9fa;
        }}
    </style>
</head>
<body>
<div class="container">

    <div class="header">
        <h1>🏪 Daily Shop Report</h1>
        <p>{today} &nbsp;|&nbsp; Good Morning, {owner_name}! ☀️</p>
    </div>

    <div class="boxes">
        <div class="box red">
            <span class="num">{analysis['critical_count']}</span>
            <span class="lbl">🚨 Critical Issues</span>
        </div>
        <div class="box orange">
            <span class="num">{analysis['high_count']}</span>
            <span class="lbl">🟠 High Priority</span>
        </div>
        <div class="box green">
            <span class="num">{analysis['total_products']}</span>
            <span class="lbl">📦 Total Products</span>
        </div>
    </div>

    <div class="section">
        <h2>📱 Today's AI Report</h2>
        <div class="report-box">{final_report}</div>
    </div>

    <div class="savings">
        💰 Act Now & Save ₹{analysis['total_potential_loss']}
    </div>

    <div class="footer">
        🤖 Sent automatically by your Shop AI Agent<br>
        Built with ❤️ for Indian shop owners
    </div>

</div>
</body>
</html>
"""

    # ── Build the email object
    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
        to=[{
            "email": owner_email,
            "name": owner_name
        }],
        sender={
            "email": sender_email,
            "name": sender_name
        },
        subject=f"🏪 Shop Report {today} — {analysis['critical_count']} Critical Issues!",
        html_content=html_content
    )

    # ── Send it!
    try:
        api_instance.send_transac_email(send_smtp_email)
        print(f"✅ Email sent to {owner_email}!")
        print(f"   Check your inbox now! 📬")
        return True

    except ApiException as e:
        print(f"❌ Brevo API Error: {e}")
        print("   Check your BREVO_API_KEY in .env file!")
        return False

    except Exception as e:
        print(f"❌ Email failed: {e}")
        return False