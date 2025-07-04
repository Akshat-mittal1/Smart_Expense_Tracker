# ⚙️ Setup Guide for SmartTracker

Follow the steps below to run SmartTracker locally:

## 🔧 Prerequisites
- Python 3.8+
- MySQL installed & running
- Git

## 🛠️ Installation Steps

```bash
# 1. Clone the repo
https://github.com/your-username/SmartTracker.git

# 2. Navigate to project directory
cd SmartTracker

# 3. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 4. Install requirements
pip install -r requirements.txt

# 5. Copy environment config
cp .env.example .env

# 6. Configure database connection in .env

# 7. Start the application
python run.py
```
---
🔗 Access

Open your browser at: http://localhost:5000
