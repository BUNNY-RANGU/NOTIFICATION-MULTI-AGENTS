# web/routes.py
# =====================================================
# JOB: All API endpoints (URLs) for the dashboard
# =====================================================

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import datetime, date
import json
import os

from web.database import get_db
from web.models import DailyReport, InventorySnapshot

# Create router
router = APIRouter()

# Templates folder
templates = Jinja2Templates(directory="web/templates")


# =====================================================
# PAGE ROUTES (returns HTML pages)
# =====================================================

@router.get("/", response_class=HTMLResponse)
async def landing(request: Request):
    """Landing page with pricing."""
    return templates.TemplateResponse(
        "landing.html",
        {"request": request}
    )


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    """
    Main dashboard page.
    Shows today's report and stats.
    """
    # Get today's report
    today = date.today().strftime("%Y-%m-%d")
    today_report = db.query(DailyReport).filter(
        DailyReport.report_date == today
    ).first()

    # Get last 7 days reports
    recent_reports = db.query(DailyReport).order_by(
        DailyReport.created_at.desc()
    ).limit(7).all()

    # Get today's inventory
    today_inventory = db.query(InventorySnapshot).filter(
        InventorySnapshot.snapshot_date == today
    ).all()

    # If no data yet, use defaults
    stats = {
        "critical": today_report.critical_count if today_report else 0,
        "high": today_report.high_count if today_report else 0,
        "products": today_report.total_products if today_report else 0,
        "money_at_risk": today_report.money_at_risk if today_report else 0,
        "savings": today_report.estimated_savings if today_report else 0,
        "report_text": today_report.full_report if today_report else "No report yet today. Run main.py to generate!",
        "email_sent": today_report.email_sent if today_report else False,
        "whatsapp_sent": today_report.whatsapp_sent if today_report else False,
    }

    return templates.TemplateResponse("index.html", {
        "request": request,
        "stats": stats,
        "recent_reports": recent_reports,
        "inventory": today_inventory,
        "today": date.today().strftime("%d %B %Y")
    })


# =====================================================
# API ROUTES (returns JSON data)
# =====================================================

@router.get("/api/stats")
async def get_stats(db: Session = Depends(get_db)):
    """Returns today's stats as JSON."""
    today = date.today().strftime("%Y-%m-%d")
    report = db.query(DailyReport).filter(
        DailyReport.report_date == today
    ).first()

    if not report:
        return {
            "critical": 0, "high": 0,
            "products": 0, "money_at_risk": 0
        }

    return {
        "critical": report.critical_count,
        "high": report.high_count,
        "products": report.total_products,
        "money_at_risk": report.money_at_risk,
        "savings": report.estimated_savings
    }


@router.get("/api/reports")
async def get_reports(db: Session = Depends(get_db)):
    """Returns last 30 days of reports."""
    reports = db.query(DailyReport).order_by(
        DailyReport.created_at.desc()
    ).limit(30).all()

    return [{
        "date": r.report_date,
        "critical": r.critical_count,
        "high": r.high_count,
        "money_at_risk": r.money_at_risk,
        "email_sent": r.email_sent,
        "whatsapp_sent": r.whatsapp_sent
    } for r in reports]


@router.get("/api/inventory")
async def get_inventory(db: Session = Depends(get_db)):
    """Returns today's inventory snapshot."""
    today = date.today().strftime("%Y-%m-%d")
    items = db.query(InventorySnapshot).filter(
        InventorySnapshot.snapshot_date == today
    ).all()

    return [{
        "name": i.product_name,
        "category": i.category,
        "stock": i.stock_qty,
        "expiry": i.expiry_date,
        "price": i.price,
        "expiry_status": i.expiry_status,
        "stock_status": i.stock_status,
        "days_to_expiry": i.days_to_expiry
    } for i in items]


@router.post("/api/run-report")
async def run_report_now(db: Session = Depends(get_db)):
    """
    Manually trigger a report right now.
    Called when owner clicks 'Run Report Now' button.
    """
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
        if not inventory:
            return {"success": False, "message": "No inventory found!"}

        analysis = analyze_inventory(inventory)

        data_summary    = agent_data_reader(inventory)
        expiry_analysis = agent_expiry_checker(analysis["expiry_issues"])
        stock_analysis  = agent_stock_analyst(
                            analysis["stock_issues"], inventory)
        recommendations = agent_recommender(analysis, inventory)
        final_report    = agent_report_writer(
            data_summary, expiry_analysis,
            stock_analysis, recommendations, analysis
        )

        email_sent = send_email_report(final_report, analysis)
        wa_sent    = send_whatsapp_report(final_report, analysis)

        # Save to database
        save_report_to_db(db, analysis, final_report,
                          email_sent, wa_sent)
        save_inventory_to_db(db, inventory, analysis)

        return {
            "success": True,
            "message": "Report generated and sent!",
            "email_sent": email_sent,
            "whatsapp_sent": wa_sent
        }

    except Exception as e:
        return {"success": False, "message": str(e)}


# =====================================================
# HELPER FUNCTIONS
# =====================================================

def save_report_to_db(db, analysis, report_text,
                       email_sent, whatsapp_sent, shop_id=None):
    """Saves daily report to database."""
    from web.models import Shop
    
    # If no shop_id, use the first one (for demo/default)
    if not shop_id:
        shop = db.query(Shop).first()
        if not shop:
            # Create a default shop if none exists
            shop = Shop(shop_name="Default Shop", owner_email="admin@example.com")
            db.add(shop)
            db.commit()
            db.refresh(shop)
        shop_id = shop.id

    today = date.today().strftime("%Y-%m-%d")
    savings = round(analysis["total_potential_loss"] * 0.7, 2)

    # Check if report for today already exists
    existing = db.query(DailyReport).filter(
        DailyReport.report_date == today,
        DailyReport.shop_id == shop_id
    ).first()

    if existing:
        # Update existing
        existing.critical_count   = analysis["critical_count"]
        existing.high_count       = analysis["high_count"]
        existing.medium_count     = analysis["medium_count"]
        existing.total_products   = analysis["total_products"]
        existing.money_at_risk    = analysis["total_potential_loss"]
        existing.estimated_savings = savings
        existing.full_report      = report_text
        existing.email_sent       = email_sent
        existing.whatsapp_sent    = whatsapp_sent
    else:
        # Create new
        new_report = DailyReport(
            shop_id           = shop_id,
            report_date       = today,
            critical_count    = analysis["critical_count"],
            high_count        = analysis["high_count"],
            medium_count      = analysis["medium_count"],
            total_products    = analysis["total_products"],
            money_at_risk     = analysis["total_potential_loss"],
            estimated_savings = savings,
            full_report       = report_text,
            email_sent        = email_sent,
            whatsapp_sent     = whatsapp_sent
        )
        db.add(new_report)

    db.commit()
    print(f"✅ Report saved to database for shop {shop_id}!")


def save_inventory_to_db(db, inventory, analysis, shop_id=None):
    """Saves inventory snapshot to database."""
    from web.models import Shop
    
    if not shop_id:
        shop = db.query(Shop).first()
        shop_id = shop.id if shop else 1

    today = date.today().strftime("%Y-%m-%d")

    # Build lookup dicts for statuses
    expiry_lookup = {
        r["product_name"]: r
        for r in analysis["expiry_results"]
    }
    stock_lookup = {
        r["product_name"]: r
        for r in analysis["stock_results"]
    }

    # Remove old snapshots for today/shop to avoid duplicates
    db.query(InventorySnapshot).filter(
        InventorySnapshot.snapshot_date == today,
        InventorySnapshot.shop_id == shop_id
    ).delete()

    for item in inventory:
        name = item["product_name"]
        expiry_info = expiry_lookup.get(name, {})
        stock_info  = stock_lookup.get(name, {})

        snapshot = InventorySnapshot(
            shop_id        = shop_id,
            snapshot_date  = today,
            product_name   = name,
            category       = item["category"],
            stock_qty      = item["stock_qty"],
            expiry_date    = item["expiry_date"],
            price          = item["price"],
            min_stock      = item["min_stock"],
            expiry_status  = expiry_info.get("status", "UNKNOWN"),
            stock_status   = stock_info.get("status", "UNKNOWN"),
            days_to_expiry = expiry_info.get("days_left", 999) or 999
        )
        db.add(snapshot)

    db.commit()
    print(f"✅ Inventory saved to database for shop {shop_id}!")


# =====================================================
# PAYMENT & REGISTRATION ROUTES
# =====================================================

@router.post("/api/register-shop")
async def register_shop(
    shop_data: dict,
    db: Session = Depends(get_db)
):
    """Registers a new shop owner."""
    try:
        from web.models import Shop

        # Check if already exists
        existing = db.query(Shop).filter(
            Shop.owner_email == shop_data.get("owner_email")
        ).first()

        if existing:
            return {
                "success": True,
                "message": "Shop already registered!"
            }

        # Create new shop
        new_shop = Shop(
            shop_name       = shop_data.get("shop_name"),
            owner_name      = shop_data.get("owner_name"),
            owner_email     = shop_data.get("owner_email"),
            owner_phone     = shop_data.get("owner_phone"),
            sheet_name      = shop_data.get("sheet_name",
                                            "ShopInventory"),
            whatsapp_number = shop_data.get("owner_phone"),
            is_active       = False,
            plan            = "trial"
        )
        db.add(new_shop)
        db.commit()

        return {
            "success": True,
            "message": "Shop registered!"
        }

    except Exception as e:
        return {"success": False, "message": str(e)}


@router.post("/api/create-order")
async def create_payment_order(payment_data: dict):
    """Creates Razorpay payment order."""
    from utils.payments import create_order

    result = create_order(
        amount_rupees = 499,
        shop_name     = payment_data.get("shop_name", ""),
        owner_email   = payment_data.get("email", "")
    )
    return result


@router.post("/api/verify-payment")
async def verify_payment_route(
    payment_data: dict,
    db: Session = Depends(get_db)
):
    """
    Verifies Razorpay payment signature and activates subscription.
    On success → sends WhatsApp to BOTH owner and admin instantly!
    """
    from utils.payments import (verify_payment,
                                 activate_shop_subscription,
                                 send_payment_notifications)
    from web.models import Shop

    # ── Step 1: Cryptographically verify the payment signature
    is_valid = verify_payment(
        order_id   = payment_data.get("order_id"),
        payment_id = payment_data.get("payment_id"),
        signature  = payment_data.get("signature")
    )

    if is_valid:
        email      = payment_data.get("email")
        payment_id = payment_data.get("payment_id")

        # ── Step 2: Activate subscription in database
        activate_shop_subscription(
            owner_email = email,
            payment_id  = payment_id
        )

        # ── Step 3: Get owner details from database
        shop = db.query(Shop).filter(
            Shop.owner_email == email
        ).first()

        # ── Step 4: Fire WhatsApp to BOTH owner and admin!
        if shop:
            wa_sent = send_payment_notifications(
                owner_name  = shop.owner_name  or "Shop Owner",
                owner_email = shop.owner_email or email,
                owner_phone = shop.owner_phone or "",
                payment_id  = payment_id
            )
            print(f"{'✅' if wa_sent else '⚠️'} WhatsApp notifications: "
                  f"{'sent' if wa_sent else 'failed (check Twilio)'}")
        else:
            print(f"⚠️  Shop not found for {email} — skipping WhatsApp")

        return {"success": True}

    else:
        return {
            "success": False,
            "message": "Payment verification failed!"
        }


# =====================================================
# UPI PAYMENT CONFIRMATION — Sends alerts to user + admin
# =====================================================

@router.post("/api/confirm-upi-payment")
async def confirm_upi_payment(payment_data: dict):
    """
    Called when a user confirms their UPI payment.
    Sends instant WhatsApp + Telegram + Email notifications to:
      1. The USER  — confirming their payment was received
      2. The ADMIN — alerting them that new payment came in
    """
    import os
    from datetime import datetime

    name      = payment_data.get("name", "Customer")
    email     = payment_data.get("email", "")
    phone     = payment_data.get("phone", "")
    txn_id    = payment_data.get("txn_id", "N/A")
    shop_name = payment_data.get("shop_name", "Not provided")
    amount    = payment_data.get("amount", "₹499")
    now       = datetime.now().strftime("%d %B %Y, %I:%M %p")

    results = []

    # ── Message Templates ──────────────────────────────────

    user_whatsapp_msg = f"""✅ *Payment Received — Shop AI Agent*

Hello *{name}*! 🎉

Your payment of *{amount}* has been confirmed!

📋 *Details:*
• Transaction ID : `{txn_id}`
• Shop Name      : {shop_name}
• Date & Time    : {now}
• Plan           : Pro — ₹499/month

⚡ *What happens next?*
Your account is being activated. You'll receive your FIRST AI inventory report at *8AM tomorrow* on this WhatsApp number!

Thank you for choosing *Shop AI Agent* 🏪
Questions? Reply to this message anytime!"""

    admin_whatsapp_msg = f"""🔔 *NEW PAYMENT RECEIVED!*

💰 *{amount}* — Pro Plan

👤 *Customer Details:*
• Name        : {name}
• Email       : {email}
• WhatsApp    : {phone}
• Shop Name   : {shop_name}
• Txn ID      : {txn_id}
• Time        : {now}

⚡ Action needed: Verify the payment in your UPI app and activate the account!"""

    user_email_subject = f"✅ Payment Confirmed — Shop AI Agent ({txn_id})"
    user_email_body = f"""<h2>✅ Payment Confirmed!</h2>
<p>Hello <strong>{name}</strong>,</p>
<p>Your payment of <strong>{amount}</strong> for <strong>Shop AI Agent Pro Plan</strong> has been received successfully!</p>
<table style="border-collapse:collapse;margin:16px 0">
  <tr><td style="padding:6px 16px 6px 0;color:#888">Transaction ID</td><td style="font-family:monospace;font-weight:bold">{txn_id}</td></tr>
  <tr><td style="padding:6px 16px 6px 0;color:#888">Shop Name</td><td>{shop_name}</td></tr>
  <tr><td style="padding:6px 16px 6px 0;color:#888">Amount</td><td><strong>{amount}/month</strong></td></tr>
  <tr><td style="padding:6px 16px 6px 0;color:#888">Date</td><td>{now}</td></tr>
</table>
<p>Your account is being set up. You'll receive your <strong>first AI inventory report at 8AM tomorrow</strong> on WhatsApp and Email!</p>
<p>Thank you for choosing Shop AI Agent 🏪</p>
<hr>
<p style="color:#888;font-size:12px">Shop AI Agent — Built for Indian shop owners. Powered by AI.</p>"""

    # ── 1. Send WhatsApp to USER ────────────────────────────
    try:
        from twilio.rest import Client
        account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        auth_token  = os.getenv("TWILIO_AUTH_TOKEN")
        from_number = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")

        if account_sid and auth_token:
            client = Client(account_sid, auth_token)
            # Normalize user phone to WhatsApp format
            user_phone = phone.strip()
            if not user_phone.startswith("whatsapp:"):
                if not user_phone.startswith("+"):
                    user_phone = "+91" + user_phone.lstrip("0")
                user_phone = "whatsapp:" + user_phone

            client.messages.create(
                body = user_whatsapp_msg,
                from_ = from_number,
                to    = user_phone
            )
            print(f"✅ User WhatsApp sent to {user_phone}")
            results.append("user_whatsapp: sent")
        else:
            results.append("user_whatsapp: skipped (no Twilio creds)")
    except Exception as e:
        print(f"❌ User WhatsApp error: {e}")
        results.append(f"user_whatsapp: failed ({e})")

    # ── 2. Send WhatsApp to ADMIN ───────────────────────────
    try:
        from twilio.rest import Client
        account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        auth_token  = os.getenv("TWILIO_AUTH_TOKEN")
        from_number = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")
        admin_phone = os.getenv("OWNER_WHATSAPP", "whatsapp:+919985784511")

        if account_sid and auth_token:
            client = Client(account_sid, auth_token)
            client.messages.create(
                body  = admin_whatsapp_msg,
                from_ = from_number,
                to    = admin_phone
            )
            print(f"✅ Admin WhatsApp sent to {admin_phone}")
            results.append("admin_whatsapp: sent")
        else:
            results.append("admin_whatsapp: skipped (no Twilio creds)")
    except Exception as e:
        print(f"❌ Admin WhatsApp error: {e}")
        results.append(f"admin_whatsapp: failed ({e})")

    # ── 3. Send Telegram to ADMIN ───────────────────────────
    try:
        import httpx
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        chat_id   = os.getenv("TELEGRAM_CHAT_ID")

        if bot_token and chat_id:
            tg_msg = f"""🔔 *NEW PAYMENT RECEIVED!*

💰 *{amount}* — Pro Plan

👤 *Customer:* {name}
📱 *Phone:* {phone}
📧 *Email:* {email}
🏪 *Shop:* {shop_name}
🧾 *Txn ID:* `{txn_id}`
🕐 *Time:* {now}

⚡ Verify in UPI app & activate account!"""

            url  = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            resp = httpx.post(url, json={
                "chat_id": chat_id,
                "text": tg_msg,
                "parse_mode": "Markdown"
            }, timeout=10)
            if resp.status_code == 200:
                print("✅ Admin Telegram sent!")
                results.append("admin_telegram: sent")
            else:
                results.append(f"admin_telegram: failed ({resp.text})")
        else:
            results.append("admin_telegram: skipped (no Telegram creds)")
    except Exception as e:
        print(f"❌ Telegram error: {e}")
        results.append(f"admin_telegram: failed ({e})")

    # ── 4. Send Email to USER via Brevo ─────────────────────
    try:
        import httpx
        brevo_key = os.getenv("BREVO_API_KEY")

        if brevo_key and email:
            url  = "https://api.brevo.com/v3/smtp/email"
            payload = {
                "sender":      {"name": "Shop AI Agent",  "email": os.getenv("SENDER_EMAIL", "bunnyrangu29@gmail.com")},
                "to":          [{"email": email, "name": name}],
                "subject":     user_email_subject,
                "htmlContent": user_email_body
            }
            resp = httpx.post(url, json=payload, headers={
                "api-key": brevo_key,
                "Content-Type": "application/json"
            }, timeout=10)
            if resp.status_code in (200, 201):
                print(f"✅ Confirmation email sent to {email}")
                results.append("user_email: sent")
            else:
                results.append(f"user_email: failed ({resp.text})")
        else:
            results.append("user_email: skipped (no Brevo key or email)")
    except Exception as e:
        print(f"❌ Email error: {e}")
        results.append(f"user_email: failed ({e})")

    print(f"\n📋 Payment confirmation results: {results}")


# =====================================================
# AI CHAT ENDPOINT — Powered by Groq LLaMA 3.3 70B
# =====================================================

@router.post("/api/ai-chat")
async def ai_chat(payload: dict, db: Session = Depends(get_db)):
    """
    Chat with the AI expert about your inventory.
    Uses today's live inventory from DB as context.
    Powered by Groq LLaMA 3.3 70B.
    """
    question = payload.get("question", "").strip()
    if not question:
        return {"answer": "Please ask a question!"}

    try:
        from agents.groq_agents import call_groq

        # Get today's live inventory as context
        today = date.today().strftime("%Y-%m-%d")
        items = db.query(InventorySnapshot).filter(
            InventorySnapshot.snapshot_date == today
        ).all()

        # Build inventory context text for the AI
        if items:
            inventory_context = "\n".join([
                f"- {i.product_name}: Stock={i.stock_qty}, "
                f"Expiry={i.expiry_date}, Price=Rs.{i.price}, "
                f"Status={i.expiry_status}/{i.stock_status}"
                for i in items
            ])
        else:
            inventory_context = "No inventory data for today yet. Run a report first from the dashboard."

        system_prompt = (
            "You are a smart, friendly AI expert for a small Indian shop owner.\n"
            "You have access to the shop's live inventory data shown below.\n"
            "Answer questions clearly and directly. Use Rs. for prices.\n"
            "Give specific, actionable advice. Be concise (max 6-8 lines).\n"
            "Use bullet points where helpful. Be warm and supportive.\n\n"
            f"TODAY'S LIVE INVENTORY:\n{inventory_context}"
        )

        answer = call_groq(system_prompt, question)

        if not answer:
            return {"answer": "AI is unavailable right now. Please check your GROQ_API_KEY in .env file."}

        return {"answer": answer}

    except Exception as e:
        print(f"AI chat error: {e}")
        return {"answer": f"Error: {str(e)}"}
