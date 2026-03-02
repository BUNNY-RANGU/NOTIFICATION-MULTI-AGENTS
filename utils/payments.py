# utils/payments.py
# =====================================================
# JOB: Handle payments for shop subscriptions
# Uses Razorpay — India's best payment gateway
# =====================================================

import razorpay
import os
import hmac
import hashlib
from dotenv import load_dotenv

load_dotenv()

# Connect to Razorpay
client = razorpay.Client(
    auth=(
        os.getenv("RAZORPAY_KEY_ID"),
        os.getenv("RAZORPAY_KEY_SECRET")
    )
)


def create_order(amount_rupees, shop_name, owner_email):
    """
    Creates a Razorpay payment order.

    amount_rupees = how much to charge (e.g. 499)
    Returns order_id that frontend uses to open payment popup
    """
    try:
        # Convert rupees to paise
        # Razorpay works in paise (1 rupee = 100 paise)
        amount_paise = int(amount_rupees * 100)

        order_data = {
            "amount"  : amount_paise,
            "currency": "INR",
            "receipt" : f"shop_{owner_email[:10]}",
            "notes"   : {
                "shop_name"  : shop_name,
                "owner_email": owner_email,
                "plan"       : "monthly"
            }
        }

        order = client.order.create(data=order_data)

        print(f"✅ Payment order created!")
        print(f"   Order ID: {order['id']}")
        print(f"   Amount  : ₹{amount_rupees}")

        return {
            "success"  : True,
            "order_id" : order["id"],
            "amount"   : amount_paise,
            "currency" : "INR",
            "key_id"   : os.getenv("RAZORPAY_KEY_ID")
        }

    except Exception as e:
        print(f"❌ Error creating order: {e}")
        return {"success": False, "error": str(e)}


def verify_payment(order_id, payment_id, signature):
    """
    Verifies payment was successful and not fake.
    Razorpay sends a signature we must verify.

    Returns True if payment is genuine.
    Returns False if payment is fake/tampered.
    """
    try:
        # Create expected signature
        message = f"{order_id}|{payment_id}"
        secret  = os.getenv("RAZORPAY_KEY_SECRET").encode()

        expected_signature = hmac.new(
            secret,
            message.encode(),
            hashlib.sha256
        ).hexdigest()

        # Compare signatures
        if expected_signature == signature:
            print(f"✅ Payment verified! ID: {payment_id}")
            return True
        else:
            print(f"❌ Payment signature mismatch!")
            return False

    except Exception as e:
        print(f"❌ Payment verification error: {e}")
        return False


def activate_shop_subscription(owner_email, payment_id):
    """
    Activates shop subscription after successful payment.
    Updates shop status in database.
    """
    try:
        from web.database import SessionLocal
        from web.models import Shop

        db = SessionLocal()

        # Find the shop
        shop = db.query(Shop).filter(
            Shop.owner_email == owner_email
        ).first()

        if shop:
            shop.is_active = True
            shop.plan      = "paid"
            db.commit()
            print(f"✅ Subscription activated for {owner_email}")
            return True
        else:
            print(f"⚠️  Shop not found: {owner_email}")
            return False

    except Exception as e:
        print(f"❌ Error activating subscription: {e}")
        return False
    finally:
        db.close()