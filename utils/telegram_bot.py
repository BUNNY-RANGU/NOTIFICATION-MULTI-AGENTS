# utils/telegram_bot.py
# =====================================================
# JOB: Telegram bot that answers owner's questions
# Owner can ask anything about their shop!
# =====================================================

import os
import asyncio
from datetime import date
from dotenv import load_dotenv
from telegram import Update, Bot
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)

load_dotenv()

# Bot credentials
TOKEN   = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


# =====================================================
# COMMAND HANDLERS
# Each function handles one command
# =====================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles /start command.
    First message owner sees.
    """
    welcome = """🏪 *Welcome to Shop AI Agent Bot!*

I'm your personal shop assistant. Ask me anything!

📋 *Available Commands:*
/report  → Get today's full report
/stock   → Check stock levels
/expiry  → Check expiring items
/summary → Quick stats summary
/help    → Show all commands

Or just *type any question* and I'll answer!

Examples:
- "What's expired today?"
- "Which items need reorder?"
- "How much money am I losing?"
"""
    await update.message.reply_text(
        welcome,
        parse_mode="Markdown"
    )


async def help_command(update: Update,
                        context: ContextTypes.DEFAULT_TYPE):
    """Handles /help command."""
    help_text = """📚 *Shop AI Bot Commands*

/start   → Welcome message
/report  → Full AI report for today
/stock   → All stock levels
/expiry  → Expiring products
/summary → Quick numbers
/run     → Generate new report now
/help    → This message

💬 *Or just ask me anything:*
"What should I order today?"
"Show me critical issues"
"How much stock of Rice do I have?"
"""
    await update.message.reply_text(
        help_text,
        parse_mode="Markdown"
    )


async def report_command(update: Update,
                          context: ContextTypes.DEFAULT_TYPE):
    """
    Handles /report command.
    Sends today's full AI report.
    """
    await update.message.reply_text(
        "⏳ Fetching today's report..."
    )

    try:
        # Get latest report from database
        from web.database import SessionLocal
        from web.models import DailyReport

        db = SessionLocal()
        today = date.today().strftime("%Y-%m-%d")
        report = db.query(DailyReport).filter(
            DailyReport.report_date == today
        ).order_by(DailyReport.id.desc()).first()
        db.close()

        if report:
            msg = f"""📊 *TODAY'S REPORT — {today}*
━━━━━━━━━━━━━━━━━━━━━━

{report.full_report}

━━━━━━━━━━━━━━━━━━━━━━
💾 _From database — generated today_"""
        else:
            msg = """⚠️ No report found for today!

Use /run to generate a new report now!"""

        await update.message.reply_text(
            msg,
            parse_mode="Markdown"
        )

    except Exception as e:
        await update.message.reply_text(
            f"❌ Error getting report: {e}"
        )


async def stock_command(update: Update,
                         context: ContextTypes.DEFAULT_TYPE):
    """
    Handles /stock command.
    Shows current stock levels.
    """
    await update.message.reply_text("📦 Checking stock levels...")

    try:
        from utils.sheets_reader import read_inventory
        from utils.analyzer import analyze_inventory

        inventory = read_inventory()
        if not inventory:
            await update.message.reply_text(
                "❌ Could not read inventory!"
            )
            return

        analysis = analyze_inventory(inventory)
        msg = "📦 *CURRENT STOCK LEVELS*\n━━━━━━━━━━━━━━━━━━━━━━\n\n"

        for result in analysis["stock_results"]:
            name   = result["product_name"]
            status = result["status"]
            stock  = result["stock_qty"]
            mini   = result["min_stock"]

            # Pick emoji based on status
            if status == "OUT_OF_STOCK":
                emoji = "🚨"
            elif status == "LOW_STOCK":
                emoji = "🟠"
            elif status == "OVERSTOCKED":
                emoji = "🟡"
            else:
                emoji = "✅"

            msg += f"{emoji} *{name}*\n"
            msg += f"   Stock: {stock} units "
            msg += f"(min: {mini})\n"
            msg += f"   Status: {status}\n\n"

        msg += "━━━━━━━━━━━━━━━━━━━━━━"

        await update.message.reply_text(
            msg,
            parse_mode="Markdown"
        )

    except Exception as e:
        await update.message.reply_text(
            f"❌ Error: {e}"
        )


async def expiry_command(update: Update,
                          context: ContextTypes.DEFAULT_TYPE):
    """
    Handles /expiry command.
    Shows expiring products.
    """
    await update.message.reply_text(
        "🗓️ Checking expiry dates..."
    )

    try:
        from utils.sheets_reader import read_inventory
        from utils.analyzer import analyze_inventory

        inventory = read_inventory()
        analysis  = analyze_inventory(inventory)
        issues    = analysis["expiry_issues"]

        if not issues:
            await update.message.reply_text(
                "✅ Great news! No expiry issues today!"
            )
            return

        msg = "⏰ *EXPIRY ALERTS*\n━━━━━━━━━━━━━━━━━━━━━━\n\n"

        for issue in issues:
            name      = issue["product_name"]
            status    = issue["status"]
            days      = issue["days_left"]
            action    = issue["action"]
            loss      = issue["potential_loss"]
            discount  = issue["discount"]

            if status == "EXPIRED":
                emoji = "🚨"
            elif status == "EXPIRING_CRITICAL":
                emoji = "🔴"
            elif status == "EXPIRING_HIGH":
                emoji = "🟠"
            else:
                emoji = "🟡"

            msg += f"{emoji} *{name}*\n"
            msg += f"   Days left: {days}\n"
            msg += f"   Discount : {discount}% OFF\n"
            msg += f"   Action   : {action}\n"
            msg += f"   At risk  : ₹{loss}\n\n"

        msg += f"━━━━━━━━━━━━━━━━━━━━━━\n"
        msg += f"💰 Total at risk: "
        msg += f"₹{analysis['total_potential_loss']}"

        await update.message.reply_text(
            msg,
            parse_mode="Markdown"
        )

    except Exception as e:
        await update.message.reply_text(
            f"❌ Error: {e}"
        )


async def summary_command(update: Update,
                           context: ContextTypes.DEFAULT_TYPE):
    """
    Handles /summary command.
    Shows quick stats.
    """
    try:
        from utils.sheets_reader import read_inventory
        from utils.analyzer import analyze_inventory

        inventory = read_inventory()
        analysis  = analyze_inventory(inventory)
        today     = date.today().strftime("%d %B %Y")

        msg = f"""📊 *QUICK SUMMARY — {today}*
━━━━━━━━━━━━━━━━━━━━━━

🚨 Critical Issues : {analysis['critical_count']}
🟠 High Priority   : {analysis['high_count']}
🟡 Medium Issues   : {analysis['medium_count']}
📦 Total Products  : {analysis['total_products']}
💰 Money at Risk   : ₹{analysis['total_potential_loss']}

━━━━━━━━━━━━━━━━━━━━━━
Use /expiry for expiry details
Use /stock for stock details
Use /report for full AI report"""

        await update.message.reply_text(
            msg,
            parse_mode="Markdown"
        )

    except Exception as e:
        await update.message.reply_text(
            f"❌ Error: {e}"
        )


async def run_command(update: Update,
                       context: ContextTypes.DEFAULT_TYPE):
    """
    Handles /run command.
    Generates fresh report and sends it.
    """
    await update.message.reply_text(
        "🤖 Running full AI report now...\n"
        "This takes about 30 seconds..."
    )

    try:
        from utils.sheets_reader import read_inventory
        from utils.analyzer import analyze_inventory
        from agents.groq_agents import (agent_data_reader,
                                         agent_expiry_checker)
        from agents.gemini_agents import (agent_stock_analyst,
                                           agent_recommender,
                                           agent_report_writer)
        from utils.email_sender import send_email_report
        from utils.whatsapp_sender import send_whatsapp_report

        # Run full pipeline
        inventory = read_inventory()
        analysis  = analyze_inventory(inventory)

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

        # Send email + WhatsApp
        email_sent = send_email_report(final_report, analysis)
        wa_sent    = send_whatsapp_report(final_report, analysis)

        # Send to Telegram
        await update.message.reply_text(
            f"✅ *Report Generated!*\n\n{final_report}\n\n"
            f"📧 Email: {'Sent ✅' if email_sent else 'Failed ❌'}\n"
            f"📱 WhatsApp: {'Sent ✅' if wa_sent else 'Failed ❌'}",
            parse_mode="Markdown"
        )

    except Exception as e:
        await update.message.reply_text(
            f"❌ Error running report: {e}"
        )


async def handle_message(update: Update,
                          context: ContextTypes.DEFAULT_TYPE):
    """
    Handles ANY text message.
    Uses Groq AI to answer questions about the shop!
    """
    user_question = update.message.text
    await update.message.reply_text(
        "🤔 Thinking..."
    )

    try:
        # Get current inventory context
        from utils.sheets_reader import read_inventory
        from utils.analyzer import analyze_inventory
        from agents.groq_agents import call_groq

        inventory = read_inventory()
        analysis  = analyze_inventory(inventory)

        # Build context for AI
        context_text = f"""
Shop Inventory Summary:
- Total products: {analysis['total_products']}
- Critical issues: {analysis['critical_count']}
- Money at risk: ₹{analysis['total_potential_loss']}

Expiry Issues:
{chr(10).join([f"- {i['product_name']}: {i['status']} ({i['days_left']} days)" for i in analysis['expiry_issues']])}

Stock Issues:
{chr(10).join([f"- {i['product_name']}: {i['status']}" for i in analysis['stock_issues']])}
"""

        system = """You are a helpful shop assistant AI.
Answer the owner's question about their shop inventory.
Be SHORT and DIRECT. Max 5 lines.
Use emojis. Indian context.
Always end with one action they should take."""

        answer = call_groq(
            system,
            f"Shop data:\n{context_text}\n\nOwner asks: {user_question}"
        )

        if answer:
            await update.message.reply_text(
                f"🤖 {answer}"
            )
        else:
            await update.message.reply_text(
                "❌ Could not get AI answer. Try /report instead!"
            )

    except Exception as e:
        await update.message.reply_text(
            f"❌ Error: {e}"
        )


# =====================================================
# SEND ALERT FUNCTION
# Called from scheduler to push morning alert
# =====================================================

async def send_telegram_alert(report_text, analysis):
    """
    Sends morning report to owner's Telegram.
    Called automatically at 8AM from scheduler.
    """
    if not TOKEN or not CHAT_ID:
        print("❌ Telegram credentials missing!")
        return False

    try:
        bot = Bot(token=TOKEN)
        today = date.today().strftime("%d %B %Y")

        msg = f"""🌅 *GOOD MORNING! Daily Report Ready*
━━━━━━━━━━━━━━━━━━━━━━

{report_text}

━━━━━━━━━━━━━━━━━━━━━━
💬 _Ask me anything about your shop!_"""

        await bot.send_message(
            chat_id    = CHAT_ID,
            text       = msg,
            parse_mode = "Markdown"
        )

        print("✅ Telegram alert sent!")
        return True

    except Exception as e:
        print(f"❌ Telegram error: {e}")
        return False


def send_telegram_alert_sync(report_text, analysis):
    """
    Synchronous wrapper for send_telegram_alert.
    Call this from non-async code like scheduler.
    """
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            send_telegram_alert(report_text, analysis)
        )
        loop.close()
        return result
    except Exception as e:
        print(f"❌ Telegram sync error: {e}")
        return False


# =====================================================
# START THE BOT
# =====================================================

def run_bot():
    """Starts the Telegram bot. Runs forever."""
    if not TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN missing in .env!")
        return

    print("🤖 Starting Telegram bot...")
    print("   Open Telegram and message your bot!")

    # Build application
    app = Application.builder().token(TOKEN).build()

    # Add command handlers
    app.add_handler(CommandHandler("start",   start))
    app.add_handler(CommandHandler("help",    help_command))
    app.add_handler(CommandHandler("report",  report_command))
    app.add_handler(CommandHandler("stock",   stock_command))
    app.add_handler(CommandHandler("expiry",  expiry_command))
    app.add_handler(CommandHandler("summary", summary_command))
    app.add_handler(CommandHandler("run",     run_command))

    # Handle any text message with AI
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_message
    ))

    print("✅ Bot is running! Press Ctrl+C to stop.")

    # Start polling for messages
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    run_bot()