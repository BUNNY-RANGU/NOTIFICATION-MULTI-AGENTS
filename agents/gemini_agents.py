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

GROQ_MODEL = "llama-3.3-70b-versatile"


def call_gemini(prompt):
    """
    Calls Groq with retry logic.
    Tries 3 times before using fallback.
    """
    MAX_RETRIES = 3

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            client = get_groq_client()
            response = client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            return response.choices[0].message.content

        except Exception as e:
            print(f"⚠️  AI attempt {attempt}/{MAX_RETRIES}: {e}")
            if attempt < MAX_RETRIES:
                import time
                time.sleep(3)
            else:
                print("❌ AI failed! Using fallback.")
                return None

# =====================================================
# AGENT 3 — STOCK ANALYST
# Job: Analyze stock problems deeply
# =====================================================

def agent_stock_analyst(stock_issues, inventory):
    """
    Agent 3: Analyzes stock problems.
    Identifies what's missing, what's excess.
    """
    print("\n🤖 Agent 3 (Gemini) → Analyzing stock...")

    if not stock_issues:
        print("✅ Agent 3 done! No stock issues.")
        return "All stock levels are healthy. No reorders needed today."

    # Build stock issues text
    issues_text = ""
    for issue in stock_issues:
        issues_text += f"""
Product: {issue['product_name']}
Status: {issue['status']}
Current Stock: {issue['stock_qty']}
Minimum Required: {issue['min_stock']}
Action Needed: {issue['action']}
---"""

    prompt = f"""You are a stock management expert for small Indian shops.

These stock problems were found in the shop:
{issues_text}

Total products in shop: {len(inventory)}

Give a SHORT stock analysis (max 6 lines):
1. Which items to order TODAY (most urgent first)
2. Estimated quantities to order
3. Which items have too much stock

Use ₹ for prices. Be direct. Indian shop context.
No long paragraphs. Use simple language."""

    result = call_gemini(prompt)

    if result:
        print("✅ Agent 3 done!")
        return result
    else:
        return "Check stock levels and reorder critical items immediately."


# =====================================================
# AGENT 4 — RECOMMENDER
# Job: Generate 5 brutal actionable moves for today
# =====================================================

def agent_recommender(analysis, inventory):
    """
    Agent 4: The strategic brain.
    Generates 5 specific actions the owner must take today.
    """
    print("\n🤖 Agent 4 (Gemini) → Generating recommendations...")

    # Build full context for AI
    expiry_count = len(analysis["expiry_issues"])
    stock_count = len(analysis["stock_issues"])
    money_at_risk = analysis["total_potential_loss"]
    critical = analysis["critical_count"]

    prompt = f"""You are a ruthless business advisor for small Indian shops.

TODAY'S SHOP SITUATION:
- Total products: {len(inventory)}
- Expiry problems: {expiry_count} products
- Stock problems: {stock_count} products  
- Critical issues: {critical}
- Money at risk: ₹{money_at_risk}

Expiry Issues:
{chr(10).join([f"- {i['product_name']}: {i['status']} ({i['days_left']} days) - ₹{i['potential_loss']} at risk" for i in analysis['expiry_issues']])}

Stock Issues:
{chr(10).join([f"- {i['product_name']}: {i['status']} (have {i['stock_qty']}, need {i['min_stock']})" for i in analysis['stock_issues']])}

Give me EXACTLY 5 numbered actions the shop owner must do TODAY.
Each action must be:
- Specific (say exactly what to do)
- Have a time (morning/afternoon/evening)
- Have expected result in ₹ if possible
- Written in simple English + Hindi mix (like real Indian shop owner talks)

Format:
1. [TIME] Action → Expected Result
2. [TIME] Action → Expected Result
...and so on"""

    result = call_gemini(prompt)

    if result:
        print("✅ Agent 4 done!")
        return result
    else:
        return """1. [MORNING] Apply 50% discount on expired items → Clear stock fast
2. [MORNING] Order out-of-stock items immediately → Stop losing sales
3. [AFTERNOON] Post WhatsApp status for near-expiry deals → Get customers
4. [AFTERNOON] Bundle overstocked items → Move excess inventory
5. [EVENING] Update stock sheet with new inventory → Stay accurate"""


# =====================================================
# AGENT 5 — REPORT WRITER
# Job: Compile everything into 1 clean WhatsApp message
# =====================================================

def agent_report_writer(data_summary, expiry_analysis, 
                         stock_analysis, recommendations, analysis):
    """
    Agent 5: The final report writer.
    Takes all agent outputs and writes ONE clean report.
    Under 300 words. WhatsApp friendly. Emoji rich.
    """
    print("\n🤖 Agent 5 (Gemini) → Writing final report...")

    from datetime import date
    today = date.today().strftime("%d %B %Y")

    money_at_risk = analysis["total_potential_loss"]
    critical = analysis["critical_count"]
    
    # Calculate estimated savings if owner acts now
    estimated_savings = round(money_at_risk * 0.7, 2)

    prompt = f"""You are writing a WhatsApp message for a small Indian shop owner.

Today's Date: {today}
Money at Risk: ₹{money_at_risk}
Critical Issues: {critical}
Estimated Savings if they act now: ₹{estimated_savings}

Data Summary from Agent 1:
{data_summary}

Expiry Analysis from Agent 2:
{expiry_analysis}

Stock Analysis from Agent 3:
{stock_analysis}

Top Recommendations from Agent 4:
{recommendations}

Write a WhatsApp report in EXACTLY this format.
Keep it under 300 words. Use emojis. Simple English.

📊 DAILY SHOP REPORT — {today}
━━━━━━━━━━━━━━━━━━━━━━
🔴 URGENT — EXPIRING SOON:
[list expiry issues with actions]

📦 STOCK ALERTS:
[list stock issues]

💡 TOP 5 ACTIONS FOR TODAY:
[numbered list]

💰 ESTIMATED SAVINGS IF YOU ACT NOW: ₹{estimated_savings}

✅ [Write one encouraging line for the owner]
━━━━━━━━━━━━━━━━━━━━━━

Make it feel like a helpful friend is sending this message.
Indian context. Warm but urgent tone."""

    result = call_gemini(prompt)

    if result:
        print("✅ Agent 5 done!")
        return result
    else:
        return f"""📊 DAILY SHOP REPORT — {today}
━━━━━━━━━━━━━━━━━━━━━━
🔴 URGENT: Check expiring products immediately!
📦 STOCK: Reorder out-of-stock items today!
💰 ESTIMATED SAVINGS: ₹{estimated_savings}
✅ Take action now and protect your profits!
━━━━━━━━━━━━━━━━━━━━━━"""