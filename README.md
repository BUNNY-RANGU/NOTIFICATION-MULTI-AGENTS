# 🏪 Shop AI Agent — Multi-Agent Inventory Alert System

> Built by [RANGU SUCHANDRA] | B.Tech 2nd Year | Python Full Stack Developer

An autonomous multi-agent AI system that reads shop inventory 
from Google Sheets, detects problems before the owner loses money, 
and fires WhatsApp + Email alerts every morning at 8AM — automatically.

---

## 🎥 What It Does
```
Google Sheets (inventory)
        ↓
5 AI Agents analyze everything
        ↓
WhatsApp + Email sent at 8AM
        ↓
Shop owner takes action. Saves money. ✅
```

## 🤖 Agent Architecture

| Agent | Model | Job |
|-------|-------|-----|
| Agent 1 | Groq LLaMA 3.3 | Reads & cleans inventory data |
| Agent 2 | Groq LLaMA 3.3 | Detects expiry issues |
| Agent 3 | Groq LLaMA 3.3 | Analyzes stock levels |
| Agent 4 | Groq LLaMA 3.3 | Generates 5 action recommendations |
| Agent 5 | Groq LLaMA 3.3 | Writes final WhatsApp report |

## 🧠 Business Rules (Hard-Coded)

### Expiry Rules
| Days Left | Action |
|-----------|--------|
| Expired | Remove from shelf immediately |
| 1-2 days | 50% flash sale NOW |
| 3 days | 30% off, push on WhatsApp |
| 4-7 days | 15% off, bundle deals |
| 8+ days | Safe ✅ |

### Stock Rules
| Condition | Action |
|-----------|--------|
| Stock = 0 | OUT OF STOCK alert |
| Stock < Min | LOW STOCK, reorder today |
| Stock > 3x Min | OVERSTOCKED, run BOGO |

## 🛠️ Tech Stack

- **AI Agents**: Groq LLaMA 3.3 70B (fast reasoning)
- **Database**: Google Sheets (free, owner already uses it)
- **Email**: Brevo API (300 free emails/day)
- **WhatsApp**: Twilio Sandbox (free testing)
- **Scheduler**: Python schedule library
- **Language**: Python 3.11+

## 📁 Project Structure
```
shop-ai-agent/
├── agents/
│   ├── groq_agents.py      # Agents 1 & 2
│   └── gemini_agents.py    # Agents 3, 4 & 5
├── utils/
│   ├── sheets_reader.py    # Google Sheets connection
│   ├── analyzer.py         # Business logic engine
│   ├── email_sender.py     # Brevo email delivery
│   └── whatsapp_sender.py  # Twilio WhatsApp delivery
├── scheduler.py            # 8AM daily automation
├── main.py                 # Full pipeline runner
└── .env.template           # Environment variables template
```

## ⚡ Setup In 10 Steps

### Prerequisites
- Python 3.11+
- Google account
- Groq account (free)
- Brevo account (free)
- Twilio account (free)

### Step 1 — Clone the repo
```bash
git clone https://github.com/yourusername/shop-ai-agent.git
cd shop-ai-agent
```

### Step 2 — Create virtual environment
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Mac/Linux
```

### Step 3 — Install packages
```bash
pip install -r requirements.txt
```

### Step 4 — Copy environment template
```bash
cp .env.template .env
```

### Step 5 — Fill in your API keys in .env
```
GROQ_API_KEY=your_key
BREVO_API_KEY=your_key
TWILIO_ACCOUNT_SID=your_sid
TWILIO_AUTH_TOKEN=your_token
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
OWNER_WHATSAPP=whatsapp:+91XXXXXXXXXX
OWNER_EMAIL=your@email.com
GOOGLE_SHEET_NAME=ShopInventory
GOOGLE_CREDENTIALS_FILE=credentials.json
```

### Step 6 — Set up Google Sheets
- Create sheet named `ShopInventory`
- Add columns: Product Name, Category, Stock Qty, Expiry Date, Price, Min Stock
- Share with your service account email

### Step 7 — Add credentials.json
- Download from Google Cloud Console
- Place in project root folder

### Step 8 — Test the pipeline
```bash
python main.py
```

### Step 9 — Start the scheduler
```bash
python scheduler.py
```

### Step 10 — Done!
```
Report fires at 8AM every day automatically! ✅
```

## 📱 Sample WhatsApp Report
```
📊 DAILY SHOP REPORT — 27 February 2026
━━━━━━━━━━━━━━━━━━━━━━
🔴 URGENT — EXPIRING SOON:
Milk: 50% FLASH SALE TODAY 📣
Bread: 30% OFF, post on WhatsApp status NOW 📱

📦 STOCK ALERTS:
Cooking Oil: OUT OF STOCK! Order immediately!
Sugar: LOW STOCK! Only 3 units left!

💡 TOP 5 ACTIONS FOR TODAY:
1. Flash sale on Milk immediately
2. Order Cooking Oil urgently
3. Bundle Tomatoes with Bread
4. Post deals on WhatsApp status
5. Restock Sugar before evening

💰 ESTIMATED SAVINGS IF YOU ACT NOW: ₹374.5
✅ Arre bhai, act now and save money! 🙏
━━━━━━━━━━━━━━━━━━━━━━
```

## 🚀 What I Learned Building This

- Multi-agent AI architecture
- Google Sheets API integration
- Groq LLaMA API usage
- Automated email with Brevo
- WhatsApp messaging with Twilio
- Python scheduling and automation
- Error handling and fallback systems
- Real-world problem solving with AI

## 👤 Built By

**Rangu Suchandra**
B.Tech 2nd Year | AI  Python Full Stack Developer
- GitHub: github.com/BUNNY-RANGU

---
⭐ Star this repo if it helped you!
