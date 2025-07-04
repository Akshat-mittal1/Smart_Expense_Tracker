```markdown
# 🔐 Environment Variables Guide

SmartTracker uses a `.env` file to securely store credentials. Below are required keys:

| Key               | Description                          |
|------------------|--------------------------------------|
| FLASK_SECRET_KEY | Secret key for Flask sessions        |
| DB_PASSWORD      | MySQL Password                       |
| MAIL_USERNAME    | Email address used to send OTP/mail  |
| MAIL_PASSWORD    | App-specific or real email password  |

> ⚠️ Never upload your real `.env` file to GitHub.
