# web/models.py
# =====================================================
# JOB: Define database tables
# Each class = one table in database
# =====================================================

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text
from sqlalchemy.sql import func
from web.database import Base


class DailyReport(Base):
    """
    Stores every daily report that was generated.
    One row = one day's report.
    """
    __tablename__ = "daily_reports"

    # Primary key — auto increments
    id = Column(Integer, primary_key=True, index=True)

    # When was this report made?
    report_date = Column(String, index=True)
    created_at  = Column(DateTime, default=func.now())

    # Problem counts
    critical_count = Column(Integer, default=0)
    high_count     = Column(Integer, default=0)
    medium_count   = Column(Integer, default=0)
    total_products = Column(Integer, default=0)

    # Money
    money_at_risk      = Column(Float, default=0.0)
    estimated_savings  = Column(Float, default=0.0)

    # The full AI report text
    full_report = Column(Text, default="")

    # Was delivery successful?
    email_sent     = Column(Boolean, default=False)
    whatsapp_sent  = Column(Boolean, default=False)


class InventorySnapshot(Base):
    """
    Stores inventory state for each day.
    One row = one product on one day.
    """
    __tablename__ = "inventory_snapshots"

    id           = Column(Integer, primary_key=True, index=True)
    snapshot_date = Column(String, index=True)
    created_at   = Column(DateTime, default=func.now())

    # Product details
    product_name = Column(String)
    category     = Column(String)
    stock_qty    = Column(Integer)
    expiry_date  = Column(String)
    price        = Column(Float)
    min_stock    = Column(Integer)

    # Status detected
    expiry_status = Column(String, default="SAFE")
    stock_status  = Column(String, default="NORMAL")
    days_to_expiry = Column(Integer, default=999)