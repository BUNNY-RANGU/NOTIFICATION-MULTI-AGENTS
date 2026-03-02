# main.py
# FULL PIPELINE — Sheets + AI + Email + WhatsApp + Telegram + Database
# Command: python main.py

import sys
import io
from utils.telegram_bot import send_telegram_alert_sync
from utils.sheets_reader import read_inventory
from utils.analyzer import analyze_inventory
from agents.groq_agents import agent_data_reader, agent_expiry_checker
from agents.gemini_agents import (agent_stock_analyst,
                                   agent_recommender,
                                   agent_report_writer)
from utils.email_sender import send_email_report
from utils.whatsapp_sender import send_whatsapp_report
from web.database import init_db, SessionLocal
from web.routes import save_report_to_db, save_inventory_to_db

# Force UTF-8 for Windows console
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def main():
    print("=" * 55)
    print("🏪 SHOP AI AGENT — FULL PIPELINE")
    print("=" * 55)

    # Initialize database
    init_db()

    # STEP 1: Read inventory
    print("\n📊 STEP 1: Reading inventory...")
    inventory = read_inventory()
    if not inventory:
        print("❌ No inventory data!")
        return

    # STEP 2: Analyze
    print("\n🔍 STEP 2: Detecting problems...")
    analysis = analyze_inventory(inventory)

    # STEP 3: AI Agents
    print("\n🤖 STEP 3: Running AI agents...")
    data_summary    = agent_data_reader(inventory)
    expiry_analysis = agent_expiry_checker(analysis["expiry_issues"])
    stock_analysis  = agent_stock_analyst(
                        analysis["stock_issues"], inventory)
    recommendations = agent_recommender(analysis, inventory)
    final_report    = agent_report_writer(
        data_summary, expiry_analysis,
        stock_analysis, recommendations, analysis
    )

    # STEP 4: Print report
    print("\n" + "=" * 55)
    print("📱 FINAL REPORT")
    print("=" * 55)
    print(final_report)
    print("=" * 55)

    # STEP 5: Send Alerts
    print("\n📧 Sending Email...")
    email_sent = send_email_report(final_report, analysis)

    print("\n📱 Sending WhatsApp...")
    wa_sent = send_whatsapp_report(final_report, analysis)

    print("\n📲 Sending Telegram...")
    send_telegram_alert_sync(final_report, analysis)

    # STEP 6: Save to database
    print("\n💾 Saving results to database...")
    db = SessionLocal()
    save_report_to_db(db, analysis, final_report, email_sent, wa_sent)
    save_inventory_to_db(db, inventory, analysis)
    db.close()

    print("\n" + "=" * 55)
    print("✅ ALL DONE! Alerts sent & results saved.")
    print("=" * 55)

if __name__ == "__main__":
    main()
