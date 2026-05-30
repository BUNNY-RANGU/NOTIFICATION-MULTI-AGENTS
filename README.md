<div align="center">

# Notification Multi-Agents

Autonomous shop inventory alert system that uses AI agents to analyze stock, expiry risk, payments, and customer notifications.

[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-web%20API-green)](https://fastapi.tiangolo.com)
[![Groq](https://img.shields.io/badge/Groq-agent%20reasoning-orange)](#agent-workflow)
[![Gemini](https://img.shields.io/badge/Gemini-analysis-blue)](#agent-workflow)

</div>

## Overview

Notification Multi-Agents is a business automation project for small shops. It reads inventory data, detects expiry and stock problems, creates recommendations, and sends daily alerts through WhatsApp and email.

The project combines AI agents, business rules, Google Sheets, payment utilities, web routes, and a scheduler.

## Agent Workflow

```text
Google Sheets Inventory
  -> Data reader agent
  -> Expiry analysis agent
  -> Stock-level agent
  -> Recommendation agent
  -> WhatsApp and Email report agent
```

## Features

- Multi-agent inventory analysis
- Expiry alerts and discount recommendations
- Low-stock and overstock detection
- WhatsApp notifications
- Email reports
- Google Sheets data source
- Razorpay/payment helper utilities
- Scheduler for daily automation
- FastAPI/web interface modules

## Tech Stack

- Python
- Groq
- Google Gemini
- Google Sheets API
- Twilio WhatsApp
- Brevo email
- Razorpay
- FastAPI
- SQLite / SQLAlchemy

## Run Locally

```bash
git clone https://github.com/BUNNY-RANGU/NOTIFICATION-MULTI-AGENTS.git
cd NOTIFICATION-MULTI-AGENTS
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Copy the environment template:

```bash
copy .env.template .env
```

Run the pipeline:

```bash
python main.py
```

Run scheduler:

```bash
python scheduler.py
```

## Environment

Use `.env.template` as the source of required keys. Do not commit real credentials.

## Best For

- Small shop inventory monitoring
- Expiry-based sales planning
- Automated owner alerts
- AI agent orchestration demos

## Author

Built by [Rangu Suchandra](https://github.com/BUNNY-RANGU).
