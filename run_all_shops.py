# run_all_shops.py
# =====================================================
# Runs reports for ALL shops at once!
# Command: python run_all_shops.py
# =====================================================

from web.database import init_db
from utils.shop_manager import run_all_shops

if __name__ == "__main__":
    init_db()
    run_all_shops()