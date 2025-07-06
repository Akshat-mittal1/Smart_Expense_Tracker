# 📁 Folder Structure – SmartTracker Project

This structure reflects the actual SmartTracker Flask project setup:

```
SmartTracker/
├── app.py                    # 🚀 Initializes the Flask app
├── app_routes.py             # 🔁 Route handlers (views)
├── app_user_settings.py      # ⚙️ User settings, mail permissions
├── run.py                    # ▶️ Run script to launch the app
│
├── templates/                # 🧾 HTML Templates (Jinja2)
│   ├── login.html
│   ├──complete_signup.html
│   ├──dashboard.html
│   ├──email_permission.html
│   ├──verify_otp.html
│   ├── signup.html
│   ├── base.html             # Common layout for all pages
│   ├── dashboard/            # 📂 Dashboard-related views
│       ├── index.html
│       ├── records.html
│       ├── analysis.html
│       ├── budget.html
│       ├── account.html
│       ├── base.html
│       ├── category.html
│       ├── main.html
│       └── reports.html│   
│
├── static/                   # 🎨 Static files (CSS, JS, images)
│   ├── css/
│   │   ├── style.css
|   |   ├── reports.css
|   |   ├── notifications.css
|   |   └── dashboard.css
│   ├── js/
|   |   ├── dashboard-common.js
|   |   ├── reports.js
|   |   ├── script.js
│   │   └── dashboard.js
│   └── images/
│       └── logo.png
│
├── scripts/                  # 🛠️ Utility scripts (e.g., SQL, backup)
│   ├── database_setup.sql
│   └── add_user_setting_api.sql
│
├── docs/                     # 📚 Documentation files
│   ├── setup-guide.md
│   ├── env-guide.md
│   └── folder-structure.md
│
├── .env.example              # 🗝️ Template for environment variables
├── .gitignore                # 🙈 Files/Folders to ignore in Git
├── requirements.txt          # 📦 Python dependencies
├── LICENSE.md                # 📄 MIT License
└── README.md                 # 📘 Project summary & usage

```

---

### 📌 Notes

- `templates/dashboard/` holds all **dashboard tab-specific HTML files**.
- Use `base.html` for layout inheritance across all pages.
- Modular Python files ensure **clean separation** of logic.
- Docs and scripts are separated for **clarity and reusability**.

---

