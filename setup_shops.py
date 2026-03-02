# setup_shops.py
# =====================================================
# RUN THIS FILE to add shops to your system!
# Command: python setup_shops.py
# =====================================================

from web.database import init_db
from utils.shop_manager import add_shop, get_all_active_shops

def setup():
    print("=" * 55)
    print("SHOP AI AGENT -- ADDING SHOPS")
    print("=" * 55)

    # Initialize database first
    init_db()

    # ── ADD YOUR SHOPS HERE!
    # Format: add_shop(
    #     shop_name, owner_name, owner_email,
    #     owner_phone, sheet_name, whatsapp_number
    # )

    # SHOP 1 — YOUR TEST SHOP
    add_shop(
        shop_name       = "Rangu General Store",
        owner_name      = "Rangu Suchandra",
        owner_email     = "bunnyrangu29@gmail.com",
        owner_phone     = "+919985784511",
        sheet_name      = "ShopInventory",
        whatsapp_number = "+919985784511"
    )

    # SHOP 2 — Example second shop
    # add_shop(
    #     shop_name       = "Kumar Kirana",
    #     owner_name      = "Ravi Kumar",
    #     owner_email     = "ravi@gmail.com",
    #     owner_phone     = "+919999999999",
    #     sheet_name      = "KumarInventory",
    #     whatsapp_number = "+919999999999"
    # )

    # ── SHOW ALL SHOPS
    shops = get_all_active_shops()
    print(f"\nACTIVE SHOPS IN SYSTEM: {len(shops)}")
    print("-" * 40)
    for shop in shops:
        print(f"Shop: {shop.shop_name}")
        print(f"   Owner : {shop.owner_name}")
        print(f"   Email : {shop.owner_email}")
        print(f"   Sheet : {shop.sheet_name}")
        print()

    print("=" * 55)
    print("Setup complete!")
    print("   Run: python run_all_shops.py")
    print("=" * 55)


if __name__ == "__main__":
    setup()