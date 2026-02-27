# utils/analyzer.py
# =====================================================
# JOB: Detect ALL problems in the inventory
# No AI here — pure Python rules
# This is the brain that never makes mistakes
# =====================================================

from datetime import datetime, date


# =====================================================
# EXPIRY RULES (hard coded — no guessing)
# Expired      → Remove immediately
# 1-2 days     → 50% discount flash sale
# 3 days       → 30% off
# 4-7 days     → 15% off bundle deal
# 8+ days      → Safe, no action
# =====================================================

def check_expiry(item):
    """
    Checks ONE product's expiry date.
    Returns a dictionary with the problem details.
    
    Example output:
    {
        "product_name": "Milk",
        "status": "EXPIRED",
        "days_left": -5,
        "action": "Remove from shelf immediately!",
        "discount": 100,
        "urgency": "CRITICAL"
    }
    """
    product_name = item["product_name"]
    expiry_str = item["expiry_date"]
    price = item["price"]
    stock_qty = item["stock_qty"]

    # If no expiry date given, skip this product
    if not expiry_str:
        return {
            "product_name": product_name,
            "status": "NO_EXPIRY_DATE",
            "days_left": None,
            "action": "Add expiry date to sheet",
            "discount": 0,
            "urgency": "LOW",
            "potential_loss": 0
        }

    # Try to parse the date
    expiry_date = parse_date(expiry_str)

    if not expiry_date:
        return {
            "product_name": product_name,
            "status": "INVALID_DATE",
            "days_left": None,
            "action": f"Fix date format in sheet. Use YYYY-MM-DD format",
            "discount": 0,
            "urgency": "LOW",
            "potential_loss": 0
        }

    # Calculate how many days left until expiry
    today = date.today()
    days_left = (expiry_date - today).days

    # Calculate how much money we lose if this expires unsold
    potential_loss = round(price * stock_qty, 2)

    # Now apply the rules
    if days_left < 0:
        # Already expired!
        return {
            "product_name": product_name,
            "status": "EXPIRED",
            "days_left": days_left,
            "action": "🚨 REMOVE FROM SHELF IMMEDIATELY! Do not sell!",
            "discount": 100,
            "urgency": "CRITICAL",
            "potential_loss": potential_loss
        }

    elif days_left <= 2:
        # Expiring in 1-2 days — flash sale!
        return {
            "product_name": product_name,
            "status": "EXPIRING_CRITICAL",
            "days_left": days_left,
            "action": f"🔴 50% FLASH SALE NOW! Only {days_left} day(s) left!",
            "discount": 50,
            "urgency": "CRITICAL",
            "potential_loss": potential_loss
        }

    elif days_left == 3:
        # 3 days left
        return {
            "product_name": product_name,
            "status": "EXPIRING_HIGH",
            "days_left": days_left,
            "action": "🟠 30% OFF today. Push on WhatsApp status now!",
            "discount": 30,
            "urgency": "HIGH",
            "potential_loss": potential_loss
        }

    elif days_left <= 7:
        # 4-7 days left
        return {
            "product_name": product_name,
            "status": "EXPIRING_MEDIUM",
            "days_left": days_left,
            "action": f"🟡 15% OFF. Bundle with other items. {days_left} days left.",
            "discount": 15,
            "urgency": "MEDIUM",
            "potential_loss": potential_loss
        }

    else:
        # 8+ days — safe!
        return {
            "product_name": product_name,
            "status": "SAFE",
            "days_left": days_left,
            "action": "✅ Safe. No action needed.",
            "discount": 0,
            "urgency": "NONE",
            "potential_loss": 0
        }


# =====================================================
# STOCK RULES
# Stock = 0           → OUT OF STOCK alert
# Stock < Min Stock   → LOW STOCK, reorder today
# Stock > 3x Min Stock → OVERSTOCKED, run BOGO
# Stock is normal     → All good
# =====================================================

def check_stock(item):
    """
    Checks ONE product's stock level.
    Returns a dictionary with the stock problem details.
    
    Example output:
    {
        "product_name": "Cooking Oil",
        "status": "OUT_OF_STOCK",
        "stock_qty": 0,
        "min_stock": 4,
        "action": "Order immediately!",
        "urgency": "CRITICAL"
    }
    """
    product_name = item["product_name"]
    stock_qty = item["stock_qty"]
    min_stock = item["min_stock"]
    price = item["price"]

    if stock_qty == 0:
        # Completely out of stock!
        return {
            "product_name": product_name,
            "status": "OUT_OF_STOCK",
            "stock_qty": stock_qty,
            "min_stock": min_stock,
            "action": "🚨 OUT OF STOCK! Order immediately. Losing sales right now!",
            "urgency": "CRITICAL",
            "reorder_qty": min_stock * 2  # order double the minimum
        }

    elif stock_qty < min_stock:
        # Running low
        reorder_qty = (min_stock * 2) - stock_qty
        return {
            "product_name": product_name,
            "status": "LOW_STOCK",
            "stock_qty": stock_qty,
            "min_stock": min_stock,
            "action": f"🟠 LOW STOCK! Only {stock_qty} left. Order {reorder_qty} units today!",
            "urgency": "HIGH",
            "reorder_qty": reorder_qty
        }

    elif stock_qty > (min_stock * 3):
        # Too much stock — money stuck in inventory
        excess = stock_qty - (min_stock * 2)
        money_stuck = round(excess * price, 2)
        return {
            "product_name": product_name,
            "status": "OVERSTOCKED",
            "stock_qty": stock_qty,
            "min_stock": min_stock,
            "action": f"🟡 OVERSTOCKED! Run BOGO deal. ₹{money_stuck} stuck in excess stock!",
            "urgency": "MEDIUM",
            "reorder_qty": 0
        }

    else:
        # Stock is normal
        return {
            "product_name": product_name,
            "status": "NORMAL",
            "stock_qty": stock_qty,
            "min_stock": min_stock,
            "action": "✅ Stock level is good.",
            "urgency": "NONE",
            "reorder_qty": 0
        }


# =====================================================
# FULL INVENTORY ANALYSIS
# Runs both expiry + stock check on every product
# Returns a complete summary of all problems
# =====================================================

def analyze_inventory(inventory):
    """
    Analyzes the FULL inventory.
    Runs expiry check AND stock check on every product.
    
    Returns a big dictionary with everything:
    - expiry_issues: list of expiry problems
    - stock_issues: list of stock problems
    - total_potential_loss: total money at risk
    - summary: counts of each problem type
    """
    print("\n🔍 Analyzing inventory for problems...")

    expiry_results = []
    stock_results = []
    total_potential_loss = 0

    for item in inventory:
        # Check expiry for this product
        expiry_result = check_expiry(item)
        expiry_results.append(expiry_result)

        # Check stock for this product
        stock_result = check_stock(item)
        stock_results.append(stock_result)

        # Add up potential losses
        total_potential_loss += expiry_result.get("potential_loss", 0)

    # Separate problems from safe items
    expiry_issues = [r for r in expiry_results if r["urgency"] != "NONE"]
    stock_issues = [r for r in stock_results if r["urgency"] != "NONE"]

    # Count by urgency level
    critical_count = len([r for r in expiry_results + stock_results 
                         if r["urgency"] == "CRITICAL"])
    high_count = len([r for r in expiry_results + stock_results 
                     if r["urgency"] == "HIGH"])
    medium_count = len([r for r in expiry_results + stock_results 
                       if r["urgency"] == "MEDIUM"])

    print(f"✅ Analysis complete!")
    print(f"   🚨 Critical issues : {critical_count}")
    print(f"   🟠 High issues     : {high_count}")
    print(f"   🟡 Medium issues   : {medium_count}")
    print(f"   💰 Money at risk   : ₹{total_potential_loss}")

    return {
        "expiry_results": expiry_results,
        "stock_results": stock_results,
        "expiry_issues": expiry_issues,
        "stock_issues": stock_issues,
        "total_potential_loss": total_potential_loss,
        "critical_count": critical_count,
        "high_count": high_count,
        "medium_count": medium_count,
        "total_products": len(inventory)
    }


# =====================================================
# HELPER FUNCTIONS
# =====================================================

def parse_date(date_str):
    """
    Tries to convert a date string into a Python date object.
    Handles multiple formats so owner's typos don't crash system.
    """
    # List of formats we try — in order
    formats = [
        "%Y-%m-%d",   # 2024-12-01  (our standard)
        "%d-%m-%Y",   # 01-12-2024
        "%d/%m/%Y",   # 01/12/2024
        "%Y/%m/%d",   # 2024/12/01
        "%d-%b-%Y",   # 01-Dec-2024
    ]

    for fmt in formats:
        try:
            return datetime.strptime(str(date_str).strip(), fmt).date()
        except ValueError:
            continue

    # None of the formats worked
    print(f"⚠️  Could not parse date: {date_str}")
    return None