from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash, send_file
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import random
import string
import re
from dotenv import load_dotenv
load_dotenv() 
from datetime import datetime, timedelta
import os
from functools import wraps
import json
import calendar
import io
import base64
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.units import inch
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.legends import Legend
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.backends.backend_agg import FigureCanvasAgg
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import atexit

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': os.getenv("DB_PASSWORD"),  # Change this
    'database': 'expense_tracker1'
}

# Email configuration
EMAIL_CONFIG = {
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587,
    'email': os.getenv("EMAIL"),  # Change this
    'password': os.getenv("EMAIL_PASSWORD")   # Change this
}

# Initialize APScheduler
scheduler = BackgroundScheduler()
scheduler.start()

# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())

def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def send_otp_email(email, otp):
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_CONFIG['email']
        msg['To'] = email
        msg['Subject'] = "Expense Tracker - OTP Verification"
        
        body = f"""
        Your OTP for Expense Tracker registration is: {otp}
        This OTP is valid for 5 minutes only.
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port'])
        server.starttls()
        server.login(EMAIL_CONFIG['email'], EMAIL_CONFIG['password'])
        text = msg.as_string()
        server.sendmail(EMAIL_CONFIG['email'], email, text)
        server.quit()
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def send_monthly_report_email(email, username, report_data, pdf_buffer):
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_CONFIG['email']
        msg['To'] = email
        msg['Subject'] = f"Monthly Financial Report - {report_data['month_year']}"
        
        # Create HTML email body
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2563eb; text-align: center;">Monthly Financial Report</h2>
                <h3 style="color: #64748b;">Hello {username},</h3>
                
                <p>Here's your financial summary for <strong>{report_data['month_year']}</strong>:</p>
                
                <div style="background-color: #f8fafc; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h4 style="margin-top: 0; color: #1e293b;">Financial Summary</h4>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr>
                            <td style="padding: 8px 0; border-bottom: 1px solid #e2e8f0;">
                                <span style="color: #10b981; font-weight: bold;">💰 Total Income:</span>
                            </td>
                            <td style="padding: 8px 0; border-bottom: 1px solid #e2e8f0; text-align: right;">
                                <strong>₹{report_data['total_income']:,.2f}</strong>
                            </td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; border-bottom: 1px solid #e2e8f0;">
                                <span style="color: #ef4444; font-weight: bold;">💸 Total Expenses:</span>
                            </td>
                            <td style="padding: 8px 0; border-bottom: 1px solid #e2e8f0; text-align: right;">
                                <strong>₹{report_data['total_expense']:,.2f}</strong>
                            </td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0;">
                                <span style="color: #f59e0b; font-weight: bold;">🏦 Total Savings:</span>
                            </td>
                            <td style="padding: 8px 0; text-align: right;">
                                <strong style="color: {'#10b981' if report_data['total_saving'] >= 0 else '#ef4444'};">
                                    ₹{report_data['total_saving']:,.2f}
                                </strong>
                            </td>
                        </tr>
                    </table>
                </div>
                
                <div style="background-color: #f1f5f9; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h4 style="margin-top: 0; color: #1e293b;">Top Expense Categories</h4>
                    <ul style="list-style: none; padding: 0;">
        """
        
        # Add top expense categories
        for category in report_data['expense_categories'][:5]:
            percentage = (category['amount'] / report_data['total_expense'] * 100) if report_data['total_expense'] > 0 else 0
            html_body += f"""
                        <li style="padding: 5px 0; border-bottom: 1px solid #cbd5e1;">
                            <span style="font-weight: bold;">{category['name']}:</span> 
                            ₹{category['amount']:,.2f} ({percentage:.1f}%)
                        </li>
            """
        
        html_body += f"""
                    </ul>
                </div>
                
                <p style="margin-top: 30px;">
                    📊 Please find your detailed monthly report attached as a PDF.
                </p>
                
                <p style="color: #64748b; font-size: 14px; margin-top: 30px;">
                    Best regards,<br>
                    Expense Tracker Team
                </p>
                
                <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 30px 0;">
                <p style="color: #94a3b8; font-size: 12px; text-align: center;">
                    You're receiving this email because you opted in for monthly financial reports. 
                    You can change your preferences in your account settings.
                </p>
            </div>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(html_body, 'html'))
        
        # Attach PDF report
        if pdf_buffer:
            pdf_attachment = MIMEBase('application', 'octet-stream')
            pdf_attachment.set_payload(pdf_buffer.getvalue())
            encoders.encode_base64(pdf_attachment)
            pdf_attachment.add_header(
                'Content-Disposition',
                f'attachment; filename="Monthly_Report_{report_data["month_year"].replace(" ", "_")}.pdf"'
            )
            msg.attach(pdf_attachment)
        
        server = smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port'])
        server.starttls()
        server.login(EMAIL_CONFIG['email'], EMAIL_CONFIG['password'])
        text = msg.as_string()
        server.sendmail(EMAIL_CONFIG['email'], email, text)
        server.quit()
        return True
    except Exception as e:
        print(f"Error sending monthly report email: {e}")
        return False

def generate_chart_image(data, chart_type='pie', title='Chart'):
    """Generate chart image for PDF reports"""
    fig, ax = plt.subplots(figsize=(8, 6))
    
    if chart_type == 'pie' and data:
        labels = [item['name'] for item in data]
        sizes = [item['amount'] for item in data]
        colors = plt.cm.Set3(range(len(labels)))
        
        wedges, texts, autotexts = ax.pie(sizes, labels=labels, autopct='%1.1f%%', 
                                         colors=colors, startangle=90)
        
        # Improve text readability
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
    
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
    plt.tight_layout()
    
    # Save to bytes buffer
    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
    img_buffer.seek(0)
    plt.close()
    
    return img_buffer

def generate_monthly_report_pdf(user_id, month, year):
    """Generate comprehensive monthly report PDF"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get user info
        cursor.execute("SELECT username, email FROM users WHERE id = %s", (user_id,))
        user_info = cursor.fetchone()
        if not user_info:
            return None
            
        username, email = user_info
        month_name = calendar.month_name[month]
        month_year = f"{month_name} {year}"
        
        # Get financial data
        report_data = get_monthly_report_data(user_id, month, year)
        
        # Create PDF buffer
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72,
                              topMargin=72, bottomMargin=18)
        
        # Container for the 'Flowable' objects
        elements = []
        
        # Define styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=1,  # Center alignment
            textColor=colors.HexColor('#2563eb')
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            spaceAfter=12,
            textColor=colors.HexColor('#1e293b')
        )
        
        # Title
        title = Paragraph(f"Monthly Financial Report<br/>{month_year}", title_style)
        elements.append(title)
        elements.append(Spacer(1, 20))
        
        # User info
        user_info_text = f"<b>Report for:</b> {username}<br/><b>Generated on:</b> {datetime.now().strftime('%B %d, %Y')}"
        elements.append(Paragraph(user_info_text, styles['Normal']))
        elements.append(Spacer(1, 30))
        
        # Financial Summary
        elements.append(Paragraph("Financial Summary", heading_style))
        
        summary_data = [
            ['Metric', 'Amount', 'Status'],
            ['Total Income', f"₹{report_data['total_income']:,.2f}", '✓'],
            ['Total Expenses', f"₹{report_data['total_expense']:,.2f}", '✓'],
            ['Net Savings', f"₹{report_data['total_saving']:,.2f}", 
             '✓ Positive' if report_data['total_saving'] >= 0 else '⚠ Negative']
        ]
        
        summary_table = Table(summary_data, colWidths=[2*inch, 1.5*inch, 1.5*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2563eb')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8fafc')),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0'))
        ]))
        
        elements.append(summary_table)
        elements.append(Spacer(1, 30))
        
        # Expense Categories
        if report_data['expense_categories']:
            elements.append(Paragraph("Expense Breakdown by Category", heading_style))
            
            expense_data = [['Category', 'Amount', 'Percentage']]
            for category in report_data['expense_categories']:
                percentage = (category['amount'] / report_data['total_expense'] * 100) if report_data['total_expense'] > 0 else 0
                expense_data.append([
                    category['name'],
                    f"₹{category['amount']:,.2f}",
                    f"{percentage:.1f}%"
                ])
            
            expense_table = Table(expense_data, colWidths=[2*inch, 1.5*inch, 1*inch])
            expense_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ef4444')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#fef2f2')),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#fecaca'))
            ]))
            
            elements.append(expense_table)
            elements.append(Spacer(1, 20))
        
        # Income Categories
        if report_data['income_categories']:
            elements.append(Paragraph("Income Breakdown by Category", heading_style))
            
            income_data = [['Category', 'Amount', 'Percentage']]
            for category in report_data['income_categories']:
                percentage = (category['amount'] / report_data['total_income'] * 100) if report_data['total_income'] > 0 else 0
                income_data.append([
                    category['name'],
                    f"₹{category['amount']:,.2f}",
                    f"{percentage:.1f}%"
                ])
            
            income_table = Table(income_data, colWidths=[2*inch, 1.5*inch, 1*inch])
            income_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#10b981')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f0fdf4')),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bbf7d0'))
            ]))
            
            elements.append(income_table)
            elements.append(Spacer(1, 30))
        
        # Financial Insights
        elements.append(Paragraph("Financial Insights & Recommendations", heading_style))
        
        insights = []
        
        # Savings rate
        if report_data['total_income'] > 0:
            savings_rate = (report_data['total_saving'] / report_data['total_income']) * 100
            if savings_rate >= 20:
                insights.append(f"✅ Excellent! You saved {savings_rate:.1f}% of your income this month.")
            elif savings_rate >= 10:
                insights.append(f"👍 Good job! You saved {savings_rate:.1f}% of your income. Try to reach 20% for optimal savings.")
            elif savings_rate > 0:
                insights.append(f"⚠️ You saved {savings_rate:.1f}% of your income. Consider reducing expenses to increase savings.")
            else:
                insights.append(f"🚨 You spent more than you earned this month. Review your expenses and create a budget.")
        
        # Top expense category
        if report_data['expense_categories']:
            top_expense = report_data['expense_categories'][0]
            top_percentage = (top_expense['amount'] / report_data['total_expense'] * 100) if report_data['total_expense'] > 0 else 0
            insights.append(f"📊 Your highest expense category is '{top_expense['name']}' at {top_percentage:.1f}% of total expenses.")
        
        # Monthly comparison (if previous month data exists)
        prev_month = month - 1 if month > 1 else 12
        prev_year = year if month > 1 else year - 1
        prev_data = get_monthly_report_data(user_id, prev_month, prev_year)
        
        if prev_data['total_expense'] > 0:
            expense_change = ((report_data['total_expense'] - prev_data['total_expense']) / prev_data['total_expense']) * 100
            if expense_change > 10:
                insights.append(f"📈 Your expenses increased by {expense_change:.1f}% compared to last month. Review your spending.")
            elif expense_change < -10:
                insights.append(f"📉 Great! Your expenses decreased by {abs(expense_change):.1f}% compared to last month.")
        
        for insight in insights:
            elements.append(Paragraph(f"• {insight}", styles['Normal']))
            elements.append(Spacer(1, 8))
        
        elements.append(Spacer(1, 20))
        
        # Footer
        footer_text = f"""
        <i>This report was automatically generated by Expense Tracker.<br/>
        For questions or support, please contact us through the application.</i>
        """
        elements.append(Paragraph(footer_text, styles['Normal']))
        
        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        
        cursor.close()
        conn.close()
        
        return buffer, report_data
        
    except Exception as e:
        print(f"Error generating PDF report: {e}")
        return None, None

def get_monthly_report_data(user_id, month, year):
    """Get comprehensive monthly report data"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Total income for the month
    cursor.execute("""
        SELECT COALESCE(SUM(amount), 0) FROM transactions 
        WHERE user_id = %s AND type = 'income' 
        AND MONTH(transaction_date) = %s AND YEAR(transaction_date) = %s
    """, (user_id, month, year))
    total_income = float(cursor.fetchone()[0])
    
    # Total expense for the month
    cursor.execute("""
        SELECT COALESCE(SUM(amount), 0) FROM transactions 
        WHERE user_id = %s AND type = 'expense' 
        AND MONTH(transaction_date) = %s AND YEAR(transaction_date) = %s
    """, (user_id, month, year))
    total_expense = float(cursor.fetchone()[0])
    
    # Income by category
    cursor.execute("""
        SELECT c.name, SUM(t.amount) as total
        FROM transactions t
        JOIN categories c ON t.category_id = c.id
        WHERE t.user_id = %s AND t.type = 'income'
        AND MONTH(transaction_date) = %s AND YEAR(transaction_date) = %s
        GROUP BY c.id, c.name
        ORDER BY total DESC
    """, (user_id, month, year))
    income_categories = [{'name': row[0], 'amount': float(row[1])} for row in cursor.fetchall()]
    
    # Expense by category
    cursor.execute("""
        SELECT c.name, SUM(t.amount) as total
        FROM transactions t
        JOIN categories c ON t.category_id = c.id
        WHERE t.user_id = %s AND t.type = 'expense'
        AND MONTH(transaction_date) = %s AND YEAR(transaction_date) = %s
        GROUP BY c.id, c.name
        ORDER BY total DESC
    """, (user_id, month, year))
    expense_categories = [{'name': row[0], 'amount': float(row[1])} for row in cursor.fetchall()]
    
    # Transaction count
    cursor.execute("""
        SELECT COUNT(*) FROM transactions 
        WHERE user_id = %s 
        AND MONTH(transaction_date) = %s AND YEAR(transaction_date) = %s
    """, (user_id, month, year))
    transaction_count = cursor.fetchone()[0]
    
    cursor.close()
    conn.close()
    
    return {
        'total_income': total_income,
        'total_expense': total_expense,
        'total_saving': total_income - total_expense,
        'income_categories': income_categories,
        'expense_categories': expense_categories,
        'transaction_count': transaction_count,
        'month_year': f"{calendar.month_name[month]} {year}"
    }

def send_monthly_reports():
    """Send monthly reports to all users who opted in"""
    try:
        print("Starting monthly report generation...")
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get all users who want email notifications
        cursor.execute("""
            SELECT id, username, email FROM users 
            WHERE email_notifications = TRUE
        """)
        users = cursor.fetchall()
        
        # Get previous month and year
        today = datetime.now()
        if today.month == 1:
            prev_month = 12
            prev_year = today.year - 1
        else:
            prev_month = today.month - 1
            prev_year = today.year
        
        print(f"Generating reports for {calendar.month_name[prev_month]} {prev_year}")
        
        for user_id, username, email in users:
            try:
                # Generate report data
                report_data = get_monthly_report_data(user_id, prev_month, prev_year)
                
                # Only send if user had any transactions
                if report_data['transaction_count'] > 0:
                    # Generate PDF
                    pdf_buffer, _ = generate_monthly_report_pdf(user_id, prev_month, prev_year)
                    
                    if pdf_buffer:
                        # Send email
                        success = send_monthly_report_email(email, username, report_data, pdf_buffer)
                        if success:
                            print(f"Monthly report sent to {email}")
                        else:
                            print(f"Failed to send monthly report to {email}")
                    else:
                        print(f"Failed to generate PDF for user {user_id}")
                else:
                    print(f"No transactions found for user {user_id} in {calendar.month_name[prev_month]} {prev_year}")
                    
            except Exception as e:
                print(f"Error processing monthly report for user {user_id}: {e}")
        
        cursor.close()
        conn.close()
        print("Monthly report generation completed.")
        
    except Exception as e:
        print(f"Error in send_monthly_reports: {e}")

# Schedule monthly reports using APScheduler (run on the 1st of each month at 9 AM)
scheduler.add_job(
    func=send_monthly_reports,
    trigger=CronTrigger(day=1, hour=9, minute=0),
    id='monthly_reports',
    name='Send Monthly Financial Reports',
    replace_existing=True
)

def generate_otp():
    return ''.join(random.choices(string.digits, k=6))

def create_default_accounts(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    default_accounts = [
        ('UPI', 'upi', 0.00),
        ('Card', 'card', 0.00),
        ('Cash', 'cash', 0.00)
    ]
    
    for name, account_type, balance in default_accounts:
        cursor.execute(
            "INSERT INTO accounts (user_id, name, account_type, balance) VALUES (%s, %s, %s, %s)",
            (user_id, name, account_type, balance)
        )
    
    conn.commit()
    cursor.close()
    conn.close()

def create_default_categories(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    income_categories = ['Home', 'Salary', 'Award', 'Lottery']
    expense_categories = ['Rent', 'Transport', 'Food', 'Shopping', 'Health', 'Others']
    
    for category in income_categories:
        cursor.execute(
            "INSERT INTO categories (user_id, name, type, is_default) VALUES (%s, %s, 'income', TRUE)",
            (user_id, category)
        )
    
    for category in expense_categories:
        cursor.execute(
            "INSERT INTO categories (user_id, name, type, is_default) VALUES (%s, %s, 'expense', TRUE)",
            (user_id, category)
        )
    
    conn.commit()
    cursor.close()
    conn.close()

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, password_hash FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user and check_password_hash(user[1], password):
            session['user_id'] = user[0]
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        
        # Validate email format
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, email):
            flash('Invalid email format', 'error')
            return render_template('signup.html')
        
        # Check if email already exists
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            flash('Email already registered', 'error')
            cursor.close()
            conn.close()
            return render_template('signup.html')
        
        # Generate and send OTP
        otp = generate_otp()
        expires_at = datetime.now() + timedelta(minutes=5)
        
        cursor.execute(
            "INSERT INTO otp_verification (email, otp, expires_at) VALUES (%s, %s, %s)",
            (email, otp, expires_at)
        )
        conn.commit()
        cursor.close()
        conn.close()
        
        if send_otp_email(email, otp):
            session['signup_email'] = email
            return redirect(url_for('verify_otp'))
        else:
            flash('Failed to send OTP. Please try again.', 'error')
    
    return render_template('signup.html')

@app.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():
    if 'signup_email' not in session:
        return redirect(url_for('signup'))
    
    if request.method == 'POST':
        otp = request.form['otp']
        email = session['signup_email']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id FROM otp_verification WHERE email = %s AND otp = %s AND expires_at > NOW() AND is_used = FALSE",
            (email, otp)
        )
        otp_record = cursor.fetchone()
        
        if otp_record:
            cursor.execute(
                "UPDATE otp_verification SET is_used = TRUE WHERE id = %s",
                (otp_record[0],)
            )
            conn.commit()
            cursor.close()
            conn.close()
            return redirect(url_for('complete_signup'))
        else:
            flash('Invalid or expired OTP', 'error')
            cursor.close()
            conn.close()
    
    return render_template('verify_otp.html')

@app.route('/complete_signup', methods=['GET', 'POST'])
def complete_signup():
    if 'signup_email' not in session:
        return redirect(url_for('signup'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        email = session['signup_email']
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('complete_signup.html')
        
        # Check if username already exists
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        if cursor.fetchone():
            flash('Username already exists', 'error')
            cursor.close()
            conn.close()
            return render_template('complete_signup.html')
        
        # Create user
        password_hash = generate_password_hash(password)
        cursor.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
            (username, email, password_hash)
        )
        user_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        conn.close()
        
        # Create default accounts and categories
        create_default_accounts(user_id)
        create_default_categories(user_id)
        
        session.pop('signup_email', None)
        session['user_id'] = user_id
        session['username'] = username
        
        return redirect(url_for('email_permission'))
    
    return render_template('complete_signup.html')

@app.route('/email_permission', methods=['GET', 'POST'])
def email_permission():
    if request.method == 'POST':
        allow_emails = request.form.get('allow_emails') == 'yes'
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET email_notifications = %s WHERE id = %s",
            (allow_emails, session['user_id'])
        )
        conn.commit()
        cursor.close()
        conn.close()
        
        return redirect(url_for('dashboard'))
    
    return render_template('email_permission.html')

# Dashboard Routes
@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard/main.html')

@app.route('/dashboard/records')
@login_required
def records():
    return render_template('dashboard/records.html')

@app.route('/dashboard/analysis')
@login_required
def analysis():
    return render_template('dashboard/analysis.html')

@app.route('/dashboard/budget')
@login_required
def budget():
    return render_template('dashboard/budget.html')

@app.route('/dashboard/account')
@login_required
def account():
    return render_template('dashboard/account.html')

@app.route('/dashboard/category')
@login_required
def category():
    return render_template('dashboard/category.html')

@app.route('/dashboard/reports')
@login_required
def reports():
    return render_template('dashboard/reports.html')

# Monthly Reports API Routes
@app.route('/api/monthly-reports')
@login_required
def get_monthly_reports():
    """Get available monthly reports for the user"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get months with transactions
        cursor.execute("""
            SELECT DISTINCT YEAR(transaction_date) as year, MONTH(transaction_date) as month,
                   COUNT(*) as transaction_count
            FROM transactions 
            WHERE user_id = %s 
            GROUP BY YEAR(transaction_date), MONTH(transaction_date)
            ORDER BY year DESC, month DESC
            LIMIT 12
        """, (session['user_id'],))
        
        reports = []
        for row in cursor.fetchall():
            year, month, count = row
            month_name = calendar.month_name[month]
            reports.append({
                'year': year,
                'month': month,
                'month_name': month_name,
                'display_name': f"{month_name} {year}",
                'transaction_count': count
            })
        
        cursor.close()
        conn.close()
        
        return jsonify(reports)
        
    except Exception as e:
        print(f"Error getting monthly reports: {e}")
        return jsonify({'error': 'Failed to load reports'}), 500

@app.route('/api/monthly-report/<int:year>/<int:month>')
@login_required
def get_monthly_report(year, month):
    """Get detailed monthly report data"""
    try:
        report_data = get_monthly_report_data(session['user_id'], month, year)
        return jsonify(report_data)
    except Exception as e:
        print(f"Error getting monthly report: {e}")
        return jsonify({'error': 'Failed to load report'}), 500

@app.route('/api/monthly-report/<int:year>/<int:month>/pdf')
@login_required
def download_monthly_report_pdf(year, month):
    """Download monthly report as PDF"""
    try:
        pdf_buffer, report_data = generate_monthly_report_pdf(session['user_id'], month, year)
        
        if pdf_buffer:
            filename = f"Monthly_Report_{calendar.month_name[month]}_{year}.pdf"
            return send_file(
                pdf_buffer,
                as_attachment=True,
                download_name=filename,
                mimetype='application/pdf'
            )
        else:
            return jsonify({'error': 'Failed to generate PDF'}), 500
            
    except Exception as e:
        print(f"Error generating PDF: {e}")
        return jsonify({'error': 'Failed to generate PDF'}), 500

@app.route('/api/send-monthly-report/<int:year>/<int:month>', methods=['POST'])
@login_required
def send_monthly_report_manual(year, month):
    """Manually send monthly report via email"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get user info
        cursor.execute("SELECT username, email FROM users WHERE id = %s", (session['user_id'],))
        user_info = cursor.fetchone()
        
        if not user_info:
            return jsonify({'error': 'User not found'}), 404
            
        username, email = user_info
        
        # Generate report data and PDF
        report_data = get_monthly_report_data(session['user_id'], month, year)
        pdf_buffer, _ = generate_monthly_report_pdf(session['user_id'], month, year)
        
        if pdf_buffer:
            # Send email
            success = send_monthly_report_email(email, username, report_data, pdf_buffer)
            
            if success:
                return jsonify({'success': True, 'message': 'Report sent successfully'})
            else:
                return jsonify({'error': 'Failed to send email'}), 500
        else:
            return jsonify({'error': 'Failed to generate PDF'}), 500
            
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error sending monthly report: {e}")
        return jsonify({'error': 'Failed to send report'}), 500

# User Settings API Routes
@app.route('/api/user-settings')
@login_required
def get_user_settings():
    """Get user settings including email preferences"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT email_notifications FROM users WHERE id = %s", (session['user_id'],))
        result = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if result:
            return jsonify({
                'email_notifications': bool(result[0])
            })
        else:
            return jsonify({'error': 'User not found'}), 404
            
    except Exception as e:
        print(f"Error getting user settings: {e}")
        return jsonify({'error': 'Failed to load settings'}), 500

@app.route('/api/user-settings', methods=['POST'])
@login_required
def update_user_settings():
    """Update user settings"""
    try:
        data = request.json
        email_notifications = data.get('email_notifications', False)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE users SET email_notifications = %s WHERE id = %s",
            (email_notifications, session['user_id'])
        )
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Settings updated successfully'})
        
    except Exception as e:
        print(f"Error updating user settings: {e}")
        return jsonify({'error': 'Failed to update settings'}), 500

# Existing API Routes (keeping all previous routes)
@app.route('/api/dashboard_data')
@login_required
def dashboard_data():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get current month data
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    # Total income for current month
    cursor.execute("""
        SELECT COALESCE(SUM(amount), 0) FROM transactions 
        WHERE user_id = %s AND type = 'income' 
        AND MONTH(transaction_date) = %s AND YEAR(transaction_date) = %s
    """, (session['user_id'], current_month, current_year))
    total_income = float(cursor.fetchone()[0])
    
    # Total expense for current month
    cursor.execute("""
        SELECT COALESCE(SUM(amount), 0) FROM transactions 
        WHERE user_id = %s AND type = 'expense' 
        AND MONTH(transaction_date) = %s AND YEAR(transaction_date) = %s
    """, (session['user_id'], current_month, current_year))
    total_expense = float(cursor.fetchone()[0])
    
    total_saving = total_income - total_expense
    
    cursor.close()
    conn.close()
    
    return jsonify({
        'total_income': total_income,
        'total_expense': total_expense,
        'total_saving': total_saving
    })

@app.route('/api/accounts')
@login_required
def get_accounts():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, balance, account_type FROM accounts WHERE user_id = %s ORDER BY id", (session['user_id'],))
    accounts = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return jsonify([{
        'id': account[0],
        'name': account[1],
        'balance': float(account[2]),
        'type': account[3]
    } for account in accounts])

@app.route('/api/categories')
@login_required
def get_categories():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, type, is_default FROM categories WHERE user_id = %s ORDER BY type, name", (session['user_id'],))
    categories = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return jsonify([{
        'id': category[0],
        'name': category[1],
        'type': category[2],
        'is_default': bool(category[3])
    } for category in categories])

@app.route('/api/transactions')
@login_required
def get_transactions():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT t.id, t.amount, t.type, t.transaction_date, t.description,
               c.name as category_name, a.name as account_name, 
               a2.name as to_account_name
        FROM transactions t
        LEFT JOIN categories c ON t.category_id = c.id
        LEFT JOIN accounts a ON t.account_id = a.id
        LEFT JOIN accounts a2 ON t.to_account_id = a2.id
        WHERE t.user_id = %s
        ORDER BY t.transaction_date DESC, t.created_at DESC
        LIMIT 50
    """, (session['user_id'],))
    
    transactions = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return jsonify([{
        'id': t[0],
        'amount': float(t[1]),
        'type': t[2],
        'transaction_date': t[3].isoformat() if t[3] else None,
        'description': t[4],
        'category_name': t[5],
        'account_name': t[6],
        'to_account_name': t[7]
    } for t in transactions])

@app.route('/api/add_transaction', methods=['POST'])
@login_required
def add_transaction():
    data = request.json
    transaction_type = data['type']
    account_id = data['account_id']
    amount = float(data['amount'])
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        if transaction_type in ['income', 'expense']:
            category_id = data['category_id']
            cursor.execute("""
                INSERT INTO transactions (user_id, account_id, category_id, amount, type, transaction_date)
                VALUES (%s, %s, %s, %s, %s, CURDATE())
            """, (session['user_id'], account_id, category_id, amount, transaction_type))
            
            # Update account balance
            if transaction_type == 'income':
                cursor.execute("UPDATE accounts SET balance = balance + %s WHERE id = %s", (amount, account_id))
            else:
                cursor.execute("UPDATE accounts SET balance = balance - %s WHERE id = %s", (amount, account_id))
        
        elif transaction_type == 'transfer':
            to_account_id = data['to_account_id']
            cursor.execute("""
                INSERT INTO transactions (user_id, account_id, to_account_id, amount, type, transaction_date)
                VALUES (%s, %s, %s, %s, %s, CURDATE())
            """, (session['user_id'], account_id, to_account_id, amount, transaction_type))
            
            # Update both account balances
            cursor.execute("UPDATE accounts SET balance = balance - %s WHERE id = %s", (amount, account_id))
            cursor.execute("UPDATE accounts SET balance = balance + %s WHERE id = %s", (amount, to_account_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'success': True})
    
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/transactions/<int:transaction_id>', methods=['DELETE'])
@login_required
def delete_transaction(transaction_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get transaction details first
        cursor.execute("""
            SELECT account_id, to_account_id, amount, type 
            FROM transactions 
            WHERE id = %s AND user_id = %s
        """, (transaction_id, session['user_id']))
        
        transaction = cursor.fetchone()
        if not transaction:
            return jsonify({'success': False, 'error': 'Transaction not found'})
        
        account_id, to_account_id, amount, trans_type = transaction
        
        # Reverse the account balance changes
        if trans_type == 'income':
            cursor.execute("UPDATE accounts SET balance = balance - %s WHERE id = %s", (amount, account_id))
        elif trans_type == 'expense':
            cursor.execute("UPDATE accounts SET balance = balance + %s WHERE id = %s", (amount, account_id))
        elif trans_type == 'transfer':
            cursor.execute("UPDATE accounts SET balance = balance + %s WHERE id = %s", (amount, account_id))
            if to_account_id:
                cursor.execute("UPDATE accounts SET balance = balance - %s WHERE id = %s", (amount, to_account_id))
        
        # Delete the transaction
        cursor.execute("DELETE FROM transactions WHERE id = %s AND user_id = %s", (transaction_id, session['user_id']))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True})
    
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/analysis/<analysis_type>')
@login_required
def get_analysis_data(analysis_type):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    if analysis_type == 'expense_overview':
        cursor.execute("""
            SELECT c.name, SUM(t.amount) as total
            FROM transactions t
            JOIN categories c ON t.category_id = c.id
            WHERE t.user_id = %s AND t.type = 'expense'
            AND MONTH(t.transaction_date) = %s AND YEAR(t.transaction_date) = %s
            GROUP BY c.id, c.name
            ORDER BY total DESC
        """, (session['user_id'], current_month, current_year))
        
    elif analysis_type == 'income_overview':
        cursor.execute("""
            SELECT c.name, SUM(t.amount) as total
            FROM transactions t
            JOIN categories c ON t.category_id = c.id
            WHERE t.user_id = %s AND t.type = 'income'
            AND MONTH(t.transaction_date) = %s AND YEAR(t.transaction_date) = %s
            GROUP BY c.id, c.name
            ORDER BY total DESC
        """, (session['user_id'], current_month, current_year))
        
    elif analysis_type == 'expense_flow':
        cursor.execute("""
            SELECT MONTH(t.transaction_date) as month, YEAR(t.transaction_date) as year, SUM(t.amount) as total
            FROM transactions t
            WHERE t.user_id = %s AND t.type = 'expense'
            AND t.transaction_date >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH)
            GROUP BY YEAR(t.transaction_date), MONTH(t.transaction_date)
            ORDER BY year, month
        """, (session['user_id'],))
        
    elif analysis_type == 'income_flow':
        cursor.execute("""
            SELECT MONTH(t.transaction_date) as month, YEAR(t.transaction_date) as year, SUM(t.amount) as total
            FROM transactions t
            WHERE t.user_id = %s AND t.type = 'income'
            AND t.transaction_date >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH)
            GROUP BY YEAR(t.transaction_date), MONTH(t.transaction_date)
            ORDER BY year, month
        """, (session['user_id'],))
    
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    
    if analysis_type in ['expense_overview', 'income_overview']:
        return jsonify({
            'labels': [row[0] for row in data],
            'values': [float(row[1]) for row in data]
        })
    else:
        labels = []
        values = []
        for row in data:
            month_name = calendar.month_abbr[row[0]]
            year = row[1]
            labels.append(f"{month_name} {year}")
            values.append(float(row[2]))
        
        return jsonify({
            'labels': labels,
            'values': values
        })

@app.route('/api/budgets')
@login_required
def get_budgets():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    cursor.execute("""
        SELECT b.category_id, b.amount, c.name,
               COALESCE(SUM(t.amount), 0) as spent
        FROM budgets b
        JOIN categories c ON b.category_id = c.id
        LEFT JOIN transactions t ON t.category_id = b.category_id 
            AND t.type = 'expense' 
            AND MONTH(t.transaction_date) = b.month 
            AND YEAR(t.transaction_date) = b.year
            AND t.user_id = %s
        WHERE b.user_id = %s AND b.month = %s AND b.year = %s
        GROUP BY b.category_id, b.amount, c.name
    """, (session['user_id'], session['user_id'], current_month, current_year))
    
    budgets = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return jsonify([{
        'category_id': budget[0],
        'amount': float(budget[1]),
        'category_name': budget[2],
        'spent': float(budget[3])
    } for budget in budgets])

@app.route('/api/budgets', methods=['POST'])
@login_required
def set_budget():
    data = request.json
    category_id = data['category_id']
    amount = data['amount']
    
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO budgets (user_id, category_id, amount, month, year)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE amount = %s
        """, (session['user_id'], category_id, amount, current_month, current_year, amount))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True})
    
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/accounts', methods=['POST'])
@login_required
def add_account():
    data = request.json
    name = data['name']
    initial_amount = data.get('initial_amount', 0)
    account_type = data.get('account_type', 'personal')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO accounts (user_id, name, balance, account_type)
            VALUES (%s, %s, %s, %s)
        """, (session['user_id'], name, initial_amount, account_type))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True})
    
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/accounts/<int:account_id>', methods=['DELETE'])
@login_required
def delete_account(account_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT account_type FROM accounts 
            WHERE id = %s AND user_id = %s
        """, (account_id, session['user_id']))
        
        account = cursor.fetchone()
        if not account:
            return jsonify({'success': False, 'error': 'Account not found'})
        
        if account[0] != 'personal':
            return jsonify({'success': False, 'error': 'Cannot delete default accounts'})
        
        cursor.execute("DELETE FROM accounts WHERE id = %s AND user_id = %s", (account_id, session['user_id']))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True})
    
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/categories', methods=['POST'])
@login_required
def add_category():
    data = request.json
    name = data['name']
    category_type = data['type']
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO categories (user_id, name, type, is_default)
            VALUES (%s, %s, %s, FALSE)
        """, (session['user_id'], name, category_type))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True})
    
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/categories/<int:category_id>', methods=['DELETE'])
@login_required
def delete_category(category_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT is_default FROM categories 
            WHERE id = %s AND user_id = %s
        """, (category_id, session['user_id']))
        
        category = cursor.fetchone()
        if not category:
            return jsonify({'success': False, 'error': 'Category not found'})
        
        if category[0]:
            return jsonify({'success': False, 'error': 'Cannot delete default categories'})
        
        cursor.execute("DELETE FROM categories WHERE id = %s AND user_id = %s", (category_id, session['user_id']))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True})
    
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
