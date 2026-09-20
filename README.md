
# 🦾 XenProfile

**XenProfile** is a feature-rich automation tool designed to bridge your **XenForo** forum account with **Telegram**. It forwards forum notifications and private messages directly to your Telegram chat with direct links, while providing automated responses using custom phrases or **Google Gemini AI**.

## ✨ Features

* **🔔 Instant Notification Forwarding:** Sends detailed alerts and direct links to Telegram whenever events happen on your XenForo profile or monitored topics.

* **💬 Profile Message Tracking:** monitors relevant posts on your wall and responds to them

* **🤖 Smart Auto-Reply System:**

  * **Static Mode:** Sends randomized pre-defined responses.

  * **AI Mode:** Generates dynamic, context-aware replies using **Google Gemini AI**.

* **🔐 Secure Authentication:** Supports standard XenForo user login alongside full **Two-Factor Authentication (2FA)** handling.

## 🛠️ Installation & Setup

### **1. Environment Setup**

Ensure you have **Python 3.10+** installed. Clone the repository, create a virtual environment, and activate it:

```
# Create a virtual environment
python -m venv venv

# Activate on Linux / macOS
source venv/bin/activate

# Activate on Windows
venv\Scripts\activate

```

### **2. Install Dependencies**

Install the required Python packages and set up Playwright browser binaries:

```
pip install -r requirements.txt
playwright install

```

## ⚙️ Configuration (`cfg.json`)

Create a **`cfg.json`** file in the root directory with the following structure:

| Key | Type | Description | 
 | ----- | ----- | ----- | 
| **`SUCCESS_URL`** | `string` | **Base URL of your targeted XenForo forum** | 
| **`LOGIN`** | `string` | **Your forum username or email address** | 
| **`PASSWORD`** | `string` | **Your forum password** | 
| **`TELEGRAM_TOKEN`** | `string` | **Bot token received from [@BotFather](https://t.me/BotFather?utm_source=gemini)** | 
| **`TELEGRAM_CHAT_ID`** | `number / string` | **Your Telegram user/chat ID** | 
| **`random_responses`** | `array` | **List of default phrases for automated static replies** | 
| **`gemini`** | `object` | **Google Gemini AI credentials and settings** | 
| **`flags`** | `object` | **Feature toggles (enabling/disabling auto-replies, tracking, etc.)** | 

```
{
  "SUCCESS_URL": "https://your-forum-domain.com/",
  "LOGIN": "YourUsername",
  "PASSWORD": "YourPassword123",
  "TELEGRAM_TOKEN": "1234567890:ABCdefGHIjklMNOpqrsTUVwxyZ",
  "TELEGRAM_CHAT_ID": 123456789,
  "random_responses": [
    "Hello! I will get back to you shortly.",
    "Thanks for reaching out! I'll read this soon.",
    "Currently away, talk to you later!"
  ],
  "gemini": {
    "api_key": "YOUR_GEMINI_API_KEY",
    "enabled": true
  },
  "flags": {
    "auto_reply": true,
    "track_notifications": true,
    "track_conversations": true
  }
}

```

## 🚀 Running the Bot

Once your configuration is complete, execute the main script:

```
python xenforo.py

```
