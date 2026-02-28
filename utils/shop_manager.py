# utils/shop_manager.py
# =====================================================
# JOB: Manage multiple shops
# Add shops, run reports for all shops, etc.
# =====================================================

import os
from datetime import date
from web.database import SessionLocal, init_db
from web.models import Shop, DailyReport, InventorySnapshot


def add_shop(shop_name, owner_name, owner_email,
             owner_phone, sheet_name, whatsapp_number):
    """
    Adds a new shop to the system.
    Call this when a new owner signs up.
    """
    db = SessionLocal()
    try:
        # Check if shop already exists
        existing = db.query(Shop).filter(
            Shop.owner_email == owner_email
        ).first()

        if existing:
            print(f"⚠️  Shop already exists: {owner_email}")
            return existing

        # Create new shop
        new_shop = Shop(
            shop_name       = shop_name,
            owner_name      = owner_name,
            owner_email     = owner_email,
            owner_phone     = owner_phone,
            sheet_name      = sheet_name,
            whatsapp_number = whatsapp_number,
            is_active       = True,
            plan            = "free"
        )

        db.add(new_shop)
        db.commit()
        db.refresh(new_shop)

        print(f"✅ Shop added: {shop_name} (ID: {new_shop.id})")
        return new_shop

    except Exception as e:
        print(f"❌ Error adding shop: {e}")
        db.rollback()
        return None
    finally:
        db.close()


def get_all_active_shops():
    """Returns all active shops from database."""
    db = SessionLocal()
    try:
        shops = db.query(Shop).filter(
            Shop.is_active == True
        ).all()
        return shops
    finally:
        db.close()


def run_report_for_shop(shop):
    """
    Runs the FULL pipeline for ONE shop.
    Reads THEIR sheet, sends to THEIR phone/email.
    """
    print(f"\n{'='*55}")
    print(f"🏪 Running report for: {shop.shop_name}")
    print(f"   Owner: {shop.owner_name}")
    print(f"   Email: {shop.owner_email}")
    print(f"{'='*55}")

    try:
        # ── Override env variables for this shop
        os.environ["GOOGLE_SHEET_NAME"] = shop.sheet_name
        os.environ["OWNER_EMAIL"]       = shop.owner_email
        os.environ["OWNER_NAME"]        = shop.owner_name
        os.environ["OWNER_WHATSAPP"]    = f"whatsapp:{shop.whatsapp_number}"

        # ── Run the pipeline
        from utils.sheets_reader import read_inventory
        from utils.analyzer import analyze_inventory
        from agents.groq_agents import (agent_data_reader,
                                         agent_expiry_checker)
        from agents.gemini_agents import (agent_stock_analyst,
                                           agent_recommender,
                                           agent_report_writer)
        from utils.email_sender import send_email_report
        from utils.whatsapp_sender import send_whatsapp_report

        inventory = read_inventory()
        if not inventory:
            print(f"❌ No inventory for {shop.shop_name}")
            return False

        analysis = analyze_inventory(inventory)

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

        # Send to THIS shop's owner
        email_sent = send_email_report(final_report, analysis)
        wa_sent    = send_whatsapp_report(final_report, analysis)

        # Save to database with shop_id
        save_shop_report(shop.id, analysis,
                         final_report, email_sent, wa_sent)
        save_shop_inventory(shop.id, inventory, analysis)

        print(f"✅ Done for {shop.shop_name}!")
        return True

    except Exception as e:
        print(f"❌ Error for {shop.shop_name}: {e}")
        return False


def run_all_shops():
    """
    Runs reports for ALL active shops.
    Call this from scheduler every morning!
    """
    print("\n🚀 RUNNING REPORTS FOR ALL SHOPS...")
    shops = get_all_active_shops()

    if not shops:
        print("⚠️  No active shops found!")
        print("   Add shops using add_shop() function")
        return

    print(f"📊 Found {len(shops)} active shops")

    results = []
    for shop in shops:
        success = run_report_for_shop(shop)
        results.append({
            "shop": shop.shop_name,
            "success": success
        })

    # Print summary
    print(f"\n{'='*55}")
    print("📊 ALL SHOPS SUMMARY")
    print(f"{'='*55}")
    for r in results:
        status = "✅" if r["success"] else "❌"
        print(f"   {status} {r['shop']}")
    print(f"{'='*55}")


def save_shop_report(shop_id, analysis, report_text,
                      email_sent, whatsapp_sent):
    """Saves report to database for specific shop."""
    db = SessionLocal()
    try:
        today   = date.today().strftime("%Y-%m-%d")
        savings = round(analysis["total_potential_loss"] * 0.7, 2)

        # Check if report exists for today
        existing = db.query(DailyReport).filter(
            DailyReport.shop_id     == shop_id,
            DailyReport.report_date == today
        ).first()

        if existing:
            existing.critical_count    = analysis["critical_count"]
            existing.high_count        = analysis["high_count"]
            existing.money_at_risk     = analysis["total_potential_loss"]
            existing.estimated_savings = savings
            existing.full_report       = report_text
            existing.email_sent        = email_sent
            existing.whatsapp_sent     = whatsapp_sent
        else:
            report = DailyReport(
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
            db.add(report)

        db.commit()
        print(f"💾 Report saved for shop {shop_id}!")

    except Exception as e:
        print(f"❌ Error saving report: {e}")
        db.rollback()
    finally:
        db.close()


def save_shop_inventory(shop_id, inventory, analysis):
    """Saves inventory snapshot for specific shop."""
    db = SessionLocal()
    try:
        today = date.today().strftime("%Y-%m-%d")

        expiry_lookup = {
            r["product_name"]: r
            for r in analysis["expiry_results"]
        }
        stock_lookup = {
            r["product_name"]: r
            for r in analysis["stock_results"]
        }

        for item in inventory:
            name         = item["product_name"]
            expiry_info  = expiry_lookup.get(name, {})
            stock_info   = stock_lookup.get(name, {})

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
        print(f"💾 Inventory saved for shop {shop_id}!")

    except Exception as e:
        print(f"❌ Error saving inventory: {e}")
        db.rollback()
    finally:
        db.close()