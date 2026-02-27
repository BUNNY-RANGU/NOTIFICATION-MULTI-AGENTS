# scheduler.py
# =====================================================
# JOB: Run the full pipeline at 8AM every day
# Command to start: python scheduler.py
# Runs forever in background!
# =====================================================

import schedule
import time
import os
import traceback
from datetime import datetime

# Import all our modules
from utils.sheets_reader import read_inventory
from utils.analyzer import analyze_inventory
from agents.groq_agents import agent_data_reader, agent_expiry_checker
from agents.gemini_agents import (agent_stock_analyst,
                                   agent_recommender,
                                   agent_report_writer)
from utils.email_sender import send_email_report
from utils.whatsapp_sender import send_whatsapp_report


def run_daily_report():
    """
    This function runs every day at 8AM.
    It does EVERYTHING automatically:
    1. Reads sheet
    2. Detects problems
    3. Runs AI agents
    4. Sends email
    5. Sends WhatsApp
    """
    print("\n" + "=" * 55)
    print(f"⏰ AUTO REPORT STARTING!")
    print(f"   Time: {datetime.now().strftime('%d %B %Y — %I:%M %p')}")
    print("=" * 55)

    try:
        # ── STEP 1: Read inventory
        print("\n📊 Reading inventory...")
        inventory = read_inventory()

        if not inventory:
            print("❌ No inventory! Sending alert...")
            send_empty_alert()
            return

        # ── STEP 2: Analyze problems
        print("\n🔍 Analyzing problems...")
        analysis = analyze_inventory(inventory)

        # ── STEP 3: Run all AI agents
        print("\n🤖 Running AI agents...")
        data_summary    = agent_data_reader(inventory)
        expiry_analysis = agent_expiry_checker(analysis["expiry_issues"])
        stock_analysis  = agent_stock_analyst(analysis["stock_issues"], inventory)
        recommendations = agent_recommender(analysis, inventory)
        final_report    = agent_report_writer(
            data_summary,
            expiry_analysis,
            stock_analysis,
            recommendations,
            analysis
        )

        # ── STEP 4: Send Email
        print("\n📧 Sending email...")
        email_sent = send_email_report(final_report, analysis)

        # ── STEP 5: Send WhatsApp
        print("\n📱 Sending WhatsApp...")
        wa_sent = send_whatsapp_report(final_report, analysis)

        # ── STEP 6: Log the result
        log_result(email_sent, wa_sent, analysis)

        print("\n" + "=" * 55)
        print("✅ DAILY REPORT COMPLETE!")
        print(f"   📧 Email   : {'Sent ✅' if email_sent else 'Failed ❌'}")
        print(f"   📱 WhatsApp: {'Sent ✅' if wa_sent else 'Failed ❌'}")
        print("=" * 55)

    except Exception as e:
        # CRITICAL: Even if everything crashes
        # we log the error and keep running tomorrow
        print(f"\n❌ ERROR in daily report: {e}")
        print(traceback.format_exc())
        log_error(str(e))
        print("⚠️  System will try again tomorrow at 8AM")


def send_empty_alert():
    """
    Sends alert when inventory sheet is empty or unreachable.
    """
    from utils.email_sender import send_email_report
    empty_analysis = {
        "critical_count": 0,
        "high_count": 0,
        "total_products": 0,
        "total_potential_loss": 0
    }
    empty_report = """⚠️ ALERT: Could not read inventory today!

Please check:
1. Your Google Sheet is accessible
2. Internet connection is working
3. Credentials are valid

Your Shop AI Agent could not generate today's report.
Please check your inventory manually today."""

    send_email_report(empty_report, empty_analysis)


def log_result(email_sent, wa_sent, analysis):
    """
    Saves a log of each report sent.
    So you can check history later.
    """
    try:
        os.makedirs("logs", exist_ok=True)
        log_file = "logs/report_log.txt"

        with open(log_file, "a") as f:
            f.write(f"\n{'='*40}\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Products: {analysis['total_products']}\n")
            f.write(f"Critical: {analysis['critical_count']}\n")
            f.write(f"Money at Risk: Rs.{analysis['total_potential_loss']}\n")
            f.write(f"Email Sent: {email_sent}\n")
            f.write(f"WhatsApp Sent: {wa_sent}\n")

    except Exception as e:
        print(f"⚠️  Could not save log: {e}")


def log_error(error_msg):
    """
    Saves errors to log file for debugging.
    """
    try:
        os.makedirs("logs", exist_ok=True)
        with open("logs/errors.txt", "a") as f:
            f.write(f"\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: {error_msg}\n")
    except:
        pass


# =====================================================
# MAIN SCHEDULER SETUP
# =====================================================

if __name__ == "__main__":
    print("=" * 55)
    print("🤖 SHOP AI AGENT — SCHEDULER STARTED!")
    print("=" * 55)
    print("⏰ Daily report will run at 8:00 AM every day")
    print("🛑 Press Ctrl+C to stop")
    print("=" * 55)

    # Schedule the job at 8AM every day
    schedule.every().day.at("08:00").do(run_daily_report)

    # Also run immediately RIGHT NOW for testing!
    print("\n🧪 Running once RIGHT NOW for testing...")
    run_daily_report()

    print("\n⏳ Scheduler is now waiting for 8AM...")
    print("   Keep this terminal open!")

    # Keep running forever
    # Checks every 60 seconds if it's time to run
    while True:
        schedule.run_pending()
        time.sleep(60)