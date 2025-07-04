# 💸 SmartTracker – Your Personal Financial Control Center

SmartTracker is a modern, intelligent, and user-friendly **expense tracking system** designed using Python, MySQL, HTML, CSS, and JavaScript — crafted to give you **complete control over your finances**.  

Developed by [**Akshat Mittal**](https://github.com/akshat-mittal1), **Founder & CEO of Cynaloras**.

---

## ⚡ Key Features

- 🔐 OTP-based secure signup & login with email validation
- 📊 Dashboard with dark/light mode and detailed analytics
- 🧾 Track income, expenses, transfers with editable records
- 🎯 Set custom budgets per category with warnings and edits
- 📑 Auto-send and download monthly PDF reports
- 🏦 Manage accounts (Cash, Card, UPI, Personal)
- 🧩 Add/remove income and expense categories

---

## 🖥️ Tech Stack

| Layer     | Tech                          |
|-----------|-------------------------------|
| Backend   | Python (Flask)                |
| Frontend  | HTML, CSS, JavaScript         |
| Database  | MySQL                         |
| Mailing   | SMTP / Flask-Mail             |
| Graphs    | Charts.js / Plotly / Matplotlib |

---

## 📦 Folder Structure

Explore the full directory breakdown in [📁 Folder Structure](docs/folder-structure.md)

---

## 📄 Setup & Installation

To run the project locally, follow the guide below:

```bash
git clone https://github.com/your-username/SmartTracker.git
cd SmartTracker
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# 🔧 Fill in your details in .env
python app.py
```

For complete setup instructions, visit:  
👉 [📚 Setup Guide](docs/setup-guide.md)

---

## 🔐 Environment Variables

All environment variables are listed in:  
👉 [🔐 Environment Guide](docs/env-guide.md)

You can start with the `.env.example` provided.

---

## 📬 Monthly Reports & Permissions

SmartTracker supports:
- Instant PDF generation
- Email delivery for previous/current months
- Auto-send on 1st of each month at 9:00 AM (optional)


---

## 👤 Author

> Built with ❤️ by  
> **Akshat Mittal**  
> Founder, CEO & Owner of **Cynaloras**

---

## 📄 License

Licensed under the MIT License. See [LICENSE.md](LICENSE.md)

---
