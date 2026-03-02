# utils/sheets_reader.py
# JOB: Read inventory from Google Sheets
# If Sheets fails → read from local backup

import gspread
from google.oauth2.service_account import Credentials
import json
import os
from dotenv import load_dotenv

load_dotenv()

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

CACHE_FILE = "data/inventory_cache.json"


def connect_to_sheet():
    """
    Connects to Google Sheets with retry logic.
    Tries 3 times before giving up.
    """
    MAX_RETRIES = 3

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            credentials_file = os.getenv(
                "GOOGLE_CREDENTIALS_FILE", "credentials.json"
            )
            creds = Credentials.from_service_account_file(
                credentials_file,
                scopes=SCOPES
            )
            client = gspread.authorize(creds)
            sheet_name = os.getenv("GOOGLE_SHEET_NAME", "ShopInventory")
            spreadsheet = client.open(sheet_name)
            worksheet = spreadsheet.sheet1
            print("Google Sheets connected!")
            return worksheet

        except FileNotFoundError:
            print("credentials.json not found!")
            return None

        except gspread.exceptions.SpreadsheetNotFound:
            print("Sheet not found! Check name in .env")
            return None

        except Exception as e:
            print(f"Attempt {attempt}/{MAX_RETRIES} failed: {e}")
            if attempt < MAX_RETRIES:
                print(f"   Retrying in 5 seconds...")
                import time
                time.sleep(5)
            else:
                print("All retries failed! Using backup.")
                return None


def read_inventory():
    print("\nReading inventory...")
    worksheet = connect_to_sheet()

    if worksheet:
        inventory = read_from_sheet(worksheet)
        if inventory:
            save_cache(inventory)
            return inventory

    print("Trying local backup...")
    return read_from_cache()


def read_from_sheet(worksheet):
    try:
        all_rows = worksheet.get_all_records()

        if not all_rows:
            print("Sheet is empty!")
            return []

        clean_inventory = []

        for row in all_rows:
            if not row.get("Product Name"):
                continue

            item = {
                "product_name": str(row.get("Product Name", "Unknown")).strip(),
                "category": str(row.get("Category", "Uncategorized")).strip(),
                "stock_qty": safe_int(row.get("Stock Qty", 0)),
                "expiry_date": str(row.get("Expiry Date", "")).strip(),
                "price": safe_float(row.get("Price", 0)),
                "min_stock": safe_int(row.get("Min Stock", 5))
            }
            clean_inventory.append(item)

        print(f"Read {len(clean_inventory)} products!")
        return clean_inventory

    except Exception as e:
        print(f"ERROR reading sheet: {e}")
        return []


def save_cache(inventory):
    try:
        os.makedirs("data", exist_ok=True)
        cache_data = {"inventory": inventory}
        with open(CACHE_FILE, "w") as f:
            json.dump(cache_data, f, indent=2)
        print(f"Backup saved!")
    except Exception as e:
        print(f"Could not save backup: {e}")


def read_from_cache():
    try:
        if not os.path.exists(CACHE_FILE):
            print("No backup found!")
            return []

        with open(CACHE_FILE, "r") as f:
            cache_data = json.load(f)

        inventory = cache_data.get("inventory", [])
        print(f"Loaded {len(inventory)} products from backup!")
        return inventory

    except Exception as e:
        print(f"ERROR reading backup: {e}")
        return []


def safe_int(value):
    try:
        return int(float(str(value).strip()))
    except:
        return 0


def safe_float(value):
    try:
        return float(str(value).strip())
    except:
        return 0.0