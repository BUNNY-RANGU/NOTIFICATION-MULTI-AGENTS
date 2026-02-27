# scheduler.py
# =====================================================
# BULLETPROOF SCHEDULER
# Runs at 8AM daily. Never stops. Never crashes.
# Command: python scheduler.py
# =====================================================

import schedule
import time
import os
import traceback
from datetime import datetime

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
    Runs the full pipeline.
    If ANYTHING fails → logs error → keeps running tomorrow.
    """
    start_time = datetime.now()

    print("\n" + "=" * 55)
    print(f"⏰ DAILY REPORT STARTING!")
    print(f"   {start_time.strftime('%d %B %Y — %I:%M %p')}")
    print("=" * 55)

    # Track what worked and what failed
    results = {
        "inventory": False,
        "analysis": False,
        "agents": False,
        "email": False,
        "whatsapp": False
    }

    try:
        # ── STEP 1: Read inventory
        inventory = read_inventory()

        if not inventory:
            print("❌ No inventory! Sending emergency alert...")
            send_emergency_alert()
            log_run(results, "No inventory found")
            return

        results["inventory"] = True

        # ── STEP 2: Analyze
        analysis = analyze_inventory(inventory)
        results["analysis"] = True

        # ── STEP 3: Run agents (each in its own try block)
        try:
            data_summary    = agent_data_reader(inventory)
            expiry_analysis = agent_expiry_checker(
                                analysis["expiry_issues"])
            stock_analysis  = agent_stock_analyst(
                                analysis["stock_issues"], inventory)
            recommendations = agent_recommender(analysis, inventory)
            final_report    = agent_report_writer(
                data_summary, expiry_analysis,
                stock_analysis, recommendations, analysis
            )
            results["agents"] = True

        except Exception as e:
            print(f"❌ Agent error: {e}")
            # Use basic fallback report if agents fail
            final_report = build_fallback_report(analysis)

        # ── STEP 4: Send Email
        try:
            email_sent = send_email_report(final_report, analysis)
            results["email"] = email_sent
        except Exception as e:
            print(f"❌ Email error: {e}")

        # ── STEP 5: Send WhatsApp
        try:
            wa_sent = send_whatsapp_report(final_report, analysis)
            results["whatsapp"] = wa_sent
        except Exception as e:
            print(f"❌ WhatsApp error: {e}")

        # ── Log the run
        end_time = datetime.now()
        duration = (end_time - start_time).seconds

        print("\n" + "=" * 55)
        print("📊 RUN SUMMARY")
        print("=" * 55)
        print(f"   ✅ Inventory : {'OK' if results['inventory'] else 'FAILED'}")
        print(f"   ✅ Analysis  : {'OK' if results['analysis'] else 'FAILED'}")
        print(f"   ✅ Agents    : {'OK' if results['agents'] else 'FAILED'}")
        print(f"   📧 Email     : {'Sent' if results['email'] else 'Failed'}")
        print(f"   📱 WhatsApp  : {'Sent' if results['whatsapp'] else 'Failed'}")
        print(f"   ⏱️  Duration  : {duration} seconds")
        print("=" * 55)

        log_run(results, "Success")

    except Exception as e:
        # NUCLEAR FALLBACK
        # Even if everything explodes → we log and survive
        error_msg = traceback.format_exc()
        print(f"\n💥 CRITICAL ERROR: {e}")
        print(error_msg)
        log_error(error_msg)
        print("⚠️  Will try again tomorrow at 8AM")


def build_fallback_report(analysis):
    """
    If AI agents fail → use this basic report.
    System still sends SOMETHING to owner.
    """
    from datetime import date
    today = date.today().strftime("%d %B %Y")

    return f"""📊 DAILY SHOP REPORT — {today}
━━━━━━━━━━━━━━━━━━━━━━
⚠️ AI analysis unavailable today.
Here are the raw numbers:

🚨 Critical Issues: {analysis['critical_count']}
🟠 High Priority  : {analysis['high_count']}
📦 Total Products : {analysis['total_products']}
💰 Money at Risk  : ₹{analysis['total_potential_loss']}

Please check your inventory manually today!
━━━━━━━━━━━━━━━━━━━━━━"""


def send_emergency_alert():
    """
    Sends alert when inventory is unreachable.
    """
    from datetime import date
    today = date.today().strftime("%d %B %Y")

    emergency_analysis = {
        "critical_count": 0,
        "high_count": 0,
        "total_products": 0,
        "total_potential_loss": 0
    }

    emergency_report = f"""⚠️ EMERGENCY ALERT — {today}

Could not read your inventory today!

Please check:
1. Internet connection
2. Google Sheet is accessible
3. System is running properly

Check inventory manually today!
Your Shop AI Agent"""

    try:
        send_email_report(emergency_report, emergency_analysis)
        send_whatsapp_report(emergency_report, emergency_analysis)
    except Exception as e:
        print(f"❌ Emergency alert also failed: {e}")


def log_run(results, status):
    """Saves run history to logs folder."""
    try:
        os.makedirs("logs", exist_ok=True)
        with open("logs/run_history.txt", "a") as f:
            f.write(f"\n{'='*40}\n")
            f.write(f"Time    : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Status  : {status}\n")
            f.write(f"Email   : {results.get('email', False)}\n")
            f.write(f"WhatsApp: {results.get('whatsapp', False)}\n")
    except:
        pass


def log_error(error_msg):
    """Saves errors to log file."""
    try:
        os.makedirs("logs", exist_ok=True)
        with open("logs/errors.txt", "a") as f:
            f.write(f"\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"{error_msg}\n")
    except:
        pass


# =====================================================
# START SCHEDULER
# =====================================================

if __name__ == "__main__":
    print("=" * 55)
    print("🤖 SHOP AI AGENT — BULLETPROOF SCHEDULER")
    print("=" * 55)
    print("⏰ Scheduled: 8:00 AM every day")
    print("🛑 Stop: Press Ctrl+C")
    print("=" * 55)

    # Schedule 8AM daily
    schedule.every().day.at("08:00").do(run_daily_report)

    # Run immediately for testing
    print("\n🧪 Running test now...")
    run_daily_report()

    print("\n" + "=" * 55)
    print("⏳ Scheduler running! Waiting for 8AM...")
    print("   Keep this terminal open!")
    print("=" * 55)

    # Run forever
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)
        except KeyboardInterrupt:
            print("\n🛑 Scheduler stopped by user!")
            break
        except Exception as e:
            print(f"⚠️  Scheduler error: {e}")
            print("   Restarting in 60 seconds...")
            time.sleep(60)