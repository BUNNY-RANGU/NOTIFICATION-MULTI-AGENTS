# web/models.py
# =====================================================
# Updated models supporting multiple shops!
# =====================================================

from sqlalchemy import (Column, Integer, String, Float,
                         Boolean, DateTime, Text, ForeignKey)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from web.database import Base


class Shop(Base):
    """
    One row = one shop owner using the system.
    This is the master table.
    """
    __tablename__ = "shops"

    id           = Column(Integer, primary_key=True, index=True)
    created_at   = Column(DateTime, default=func.now())

    # Shop details
    shop_name    = Column(String, index=True)
    owner_name   = Column(String)
    owner_email  = Column(String, unique=True, index=True)
    owner_phone  = Column(String)

    # Google Sheet connection
    sheet_name   = Column(String)

    # Alert settings
    whatsapp_number = Column(String)
    email_alerts    = Column(Boolean, default=True)
    whatsapp_alerts = Column(Boolean, default=True)
    report_time     = Column(String, default="08:00")

    # Subscription
    is_active       = Column(Boolean, default=True)
    plan            = Column(String, default="free")

    # Relationships — one shop has many reports
    reports     = relationship("DailyReport", back_populates="shop")
    inventories = relationship("InventorySnapshot",
                               back_populates="shop")


class DailyReport(Base):
    """One row = one day's report for one shop."""
    __tablename__ = "daily_reports"

    id          = Column(Integer, primary_key=True, index=True)
    shop_id     = Column(Integer, ForeignKey("shops.id"), index=True)
    report_date = Column(String, index=True)
    created_at  = Column(DateTime, default=func.now())

    # Problem counts
    critical_count = Column(Integer, default=0)
    high_count     = Column(Integer, default=0)
    medium_count   = Column(Integer, default=0)
    total_products = Column(Integer, default=0)

    # Money
    money_at_risk     = Column(Float, default=0.0)
    estimated_savings = Column(Float, default=0.0)

    # Full report text
    full_report = Column(Text, default="")

    # Delivery status
    email_sent    = Column(Boolean, default=False)
    whatsapp_sent = Column(Boolean, default=False)

    # Relationship back to shop
    shop = relationship("Shop", back_populates="reports")


class InventorySnapshot(Base):
    """One row = one product on one day for one shop."""
    __tablename__ = "inventory_snapshots"

    id            = Column(Integer, primary_key=True, index=True)
    shop_id       = Column(Integer, ForeignKey("shops.id"), index=True)
    snapshot_date = Column(String, index=True)
    created_at    = Column(DateTime, default=func.now())

    # Product details
    product_name = Column(String)
    category     = Column(String)
    stock_qty    = Column(Integer)
    expiry_date  = Column(String)
    price        = Column(Float)
    min_stock    = Column(Integer)

    # Status
    expiry_status  = Column(String, default="SAFE")
    stock_status   = Column(String, default="NORMAL")
    days_to_expiry = Column(Integer, default=999)

    # Relationship
    shop = relationship("Shop", back_populates="inventories")