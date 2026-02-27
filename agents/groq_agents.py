# agents/groq_agents.py
# =====================================================
# GROQ AGENTS — Fast thinking using LLaMA 3.3 70B
# Agent 1: Data Reader
# Agent 2: Expiry Checker
# =====================================================

import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# Lazy initialization of Groq client
_client = None

def get_groq_client():
    """Lazy initialization of Groq client to avoid SSL hang during import."""
    global _client
    if _client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")
        _client = Groq(api_key=api_key)
    return _client

# The model we use — fastest free model available
GROQ_MODEL = "llama-3.3-70b-versatile"


def call_groq(system_prompt, user_message):
    """
    Calls Groq with retry logic.
    Tries 3 times before using fallback.
    """
    MAX_RETRIES = 3

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            return response.choices[0].message.content

        except Exception as e:
            print(f"⚠️  Groq attempt {attempt}/{MAX_RETRIES}: {e}")
            if attempt < MAX_RETRIES:
                import time
                time.sleep(3)
            else:
                print("❌ Groq failed! Using fallback response.")
                return None


# =====================================================
# AGENT 1 — DATA READER
# Job: Look at raw inventory and give clean summary
# =====================================================

def agent_data_reader(inventory):
    """
    Agent 1: Reads raw inventory data.
    Returns a clean plain-english summary.
    """
    print("\n🤖 Agent 1 (Groq) → Reading data...")

    # Convert inventory list to readable text for the AI
    inventory_text = ""
    for item in inventory:
        inventory_text += f"""
Product: {item['product_name']}
Category: {item['category']}
Stock: {item['stock_qty']} units
Expiry: {item['expiry_date']}
Price: ₹{item['price']}
Min Stock: {item['min_stock']}
---"""

    system_prompt = """You are a data analyst for a small Indian shop.
Your job is to read raw inventory data and give a clean, 
simple summary in 5-8 lines.
Focus on: total products, categories, price range.
Be brief. No bullet points. Plain text only."""

    user_message = f"""Here is the shop inventory data:
{inventory_text}

Give me a clean 5-line summary of this inventory."""

    result = call_groq(system_prompt, user_message)

    if result:
        print("✅ Agent 1 done!")
        return result
    else:
        # Fallback if Groq fails
        return f"Shop has {len(inventory)} products across multiple categories."


# =====================================================
# AGENT 2 — EXPIRY CHECKER
# Job: Look at expiry problems and suggest discounts
# =====================================================

def agent_expiry_checker(expiry_issues):
    """
    Agent 2: Analyzes expiry problems.
    Gives specific discount and action recommendations.
    """
    print("\n🤖 Agent 2 (Groq) → Checking expiry issues...")

    if not expiry_issues:
        print("✅ Agent 2 done! No expiry issues.")
        return "No expiry issues found. All products are within safe dates."

    # Build expiry issues text
    issues_text = ""
    for issue in expiry_issues:
        issues_text += f"""
Product: {issue['product_name']}
Status: {issue['status']}
Days Left: {issue['days_left']}
Suggested Action: {issue['action']}
Money at Risk: ₹{issue['potential_loss']}
---"""

    system_prompt = """You are an expiry management expert for small Indian shops.
Your job is to look at expiring products and give 
SPECIFIC, URGENT, ACTIONABLE advice.
Use Indian context — mention WhatsApp status, local customers, bundling.
Keep it SHORT — max 8 lines total.
Use emojis. Be direct. No fluff."""

    user_message = f"""These products have expiry issues in my shop:
{issues_text}

Give me specific actions for each product to avoid losing money.
Be brutal and direct. What should the owner do TODAY?"""

    result = call_groq(system_prompt, user_message)

    if result:
        print("✅ Agent 2 done!")
        return result
    else:
        return "Check expiring products immediately and apply discounts."