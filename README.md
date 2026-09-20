# XenProfile
A bot that forwards XenForo forum notifications to Telegram with detailed information and links. It also features an auto-reply system with predefined phrases or AI-generated responses for profile messages and monitored topics. Authentication uses your XenForo credentials with 2FA support.

## Installing
1. Download Python and a virtual environment, and activate it.
2. Settings "cfg.json":
- SUCCESS_URL — link to you forum
- LOGIN — pseudonym or email address
- PASSWORD — your password
- TELEGRAM_TOKEN - your telegram-token (BotFather)
- TELEGRAM_CHAT_ID — your profile ID
- random_responses — list of phrases for automated responses
- gemini — Settings AI:
- flags — Automating replies and tracking forum notifications
3. pip install -r requirements
4. python xenforo.py
