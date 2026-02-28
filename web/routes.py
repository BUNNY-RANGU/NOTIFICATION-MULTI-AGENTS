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
                       email_sent, whatsapp_sent):
    """Saves daily report to database."""
    today = date.today().strftime("%Y-%m-%d")
    savings = round(analysis["total_potential_loss"] * 0.7, 2)

    # Check if report for today already exists
    existing = db.query(DailyReport).filter(
        DailyReport.report_date == today
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
    print("✅ Report saved to database!")


def save_inventory_to_db(db, inventory, analysis):
    """Saves inventory snapshot to database."""
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

    for item in inventory:
        name = item["product_name"]
        expiry_info = expiry_lookup.get(name, {})
        stock_info  = stock_lookup.get(name, {})

        snapshot = InventorySnapshot(
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
    print("✅ Inventory saved to database!")