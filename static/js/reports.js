import { Chart } from "@/components/ui/chart"
// Reports page functionality
class ReportsManager {
  constructor() {
    this.currentReports = []
    this.currentReportData = null
    this.charts = {}
    this.init()
  }

  init() {
    this.loadUserSettings()
    this.loadReports()
    this.setupEventListeners()
  }

  setupEventListeners() {
    // Settings toggle
    const emailCheckbox = document.getElementById("emailNotifications")
    if (emailCheckbox) {
      emailCheckbox.addEventListener("change", (e) => {
        this.updateEmailSettings(e.target.checked)
      })
    }

    // Year filter
    const yearFilter = document.getElementById("yearFilter")
    if (yearFilter) {
      yearFilter.addEventListener("change", (e) => {
        this.filterReportsByYear(e.target.value)
      })
    }

    // Modal close
    const modal = document.getElementById("reportModal")
    if (modal) {
      const closeBtn = modal.querySelector(".modal-close")
      if (closeBtn) {
        closeBtn.addEventListener("click", () => {
          this.closeModal()
        })
      }

      modal.addEventListener("click", (e) => {
        if (e.target === modal) {
          this.closeModal()
        }
      })
    }

    // Modal action buttons
    const downloadBtn = document.getElementById("downloadPdfBtn")
    const emailBtn = document.getElementById("emailReportBtn")

    if (downloadBtn) {
      downloadBtn.addEventListener("click", () => {
        this.downloadCurrentReport()
      })
    }

    if (emailBtn) {
      emailBtn.addEventListener("click", () => {
        this.emailCurrentReport()
      })
    }

    // Keyboard shortcuts
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") {
        const modal = document.getElementById("reportModal")
        if (modal && modal.style.display === "block") {
          this.closeModal()
        }
        const emailModal = document.getElementById("emailSettingsModal")
        if (emailModal && emailModal.style.display === "block") {
          this.closeModal("emailSettingsModal")
        }
      }
    })
  }

  async loadUserSettings() {
    try {
      const response = await fetch("/api/user-settings")
      if (response.ok) {
        const settings = await response.json()
        const emailCheckbox = document.getElementById("emailNotifications")
        if (emailCheckbox) {
          emailCheckbox.checked = settings.email_notifications
        }
      }
    } catch (error) {
      console.error("Error loading user settings:", error)
    }
  }

  async updateEmailSettings(enabled) {
    try {
      const response = await fetch("/api/user-settings", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email_notifications: enabled,
        }),
      })

      if (response.ok) {
        this.showMessage("Settings updated successfully", "success")
      } else {
        throw new Error("Failed to update settings")
      }
    } catch (error) {
      console.error("Error updating settings:", error)
      this.showMessage("Failed to update settings", "error")
      // Revert checkbox state
      const emailCheckbox = document.getElementById("emailNotifications")
      if (emailCheckbox) {
        emailCheckbox.checked = !enabled
      }
    }
  }

  async loadReports() {
    try {
      const response = await fetch("/api/monthly-reports")
      if (response.ok) {
        this.currentReports = await response.json()
        this.renderReports()
        this.populateYearFilter()
      } else {
        throw new Error("Failed to load reports")
      }
    } catch (error) {
      console.error("Error loading reports:", error)
      this.showEmptyState("Failed to load reports")
    }
  }

  populateYearFilter() {
    const yearFilter = document.getElementById("yearFilter")
    if (!yearFilter) return

    const years = [...new Set(this.currentReports.map((report) => report.year))].sort((a, b) => b - a)

    // Clear existing options except "All Years"
    yearFilter.innerHTML = '<option value="">All Years</option>'

    years.forEach((year) => {
      const option = document.createElement("option")
      option.value = year
      option.textContent = year
      yearFilter.appendChild(option)
    })
  }

  filterReportsByYear(year) {
    const filteredReports = year
      ? this.currentReports.filter((report) => report.year.toString() === year)
      : this.currentReports

    this.renderReports(filteredReports)
  }

  renderReports(reports = this.currentReports) {
    const grid = document.getElementById("reportsGrid")
    if (!grid) return

    if (reports.length === 0) {
      this.showEmptyState("No reports available for the selected period")
      return
    }

    grid.innerHTML = reports.map((report) => this.createReportCard(report)).join("")

    // Add click listeners to report cards
    grid.querySelectorAll(".report-card").forEach((card) => {
      card.addEventListener("click", (e) => {
        if (!e.target.closest(".report-action-btn")) {
          const year = card.dataset.year
          const month = card.dataset.month
          this.openReportModal(year, month)
        }
      })
    })

    // Add listeners to action buttons
    grid.querySelectorAll(".report-action-btn").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        e.stopPropagation()
        const action = btn.dataset.action
        const year = btn.closest(".report-card").dataset.year
        const month = btn.closest(".report-card").dataset.month

        if (action === "download") {
          this.downloadReport(year, month)
        } else if (action === "email") {
          this.emailReport(year, month)
        }
      })
    })
  }

  createReportCard(report) {
    return `
            <div class="report-card" data-year="${report.year}" data-month="${report.month}">
                <div class="report-header">
                    <h4 class="report-title">${report.display_name}</h4>
                    <span class="report-date">${report.transaction_count} transactions</span>
                </div>
                <div class="report-stats">
                    <div class="stat-item">
                        <div class="stat-value income">₹0</div>
                        <div class="stat-label">Income</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value expense">₹0</div>
                        <div class="stat-label">Expenses</div>
                    </div>
                </div>
                <div class="transaction-count">
                    <i class="fas fa-receipt"></i> ${report.transaction_count} transactions
                </div>
                <div class="report-actions">
                    <button class="report-action-btn" data-action="download">
                        <i class="fas fa-download"></i> PDF
                    </button>
                    <button class="report-action-btn secondary" data-action="email">
                        <i class="fas fa-envelope"></i> Email
                    </button>
                </div>
            </div>
        `
  }

  async openReportModal(year, month) {
    const modal = document.getElementById("reportModal")
    const modalTitle = document.getElementById("modalTitle")
    const reportPreview = document.getElementById("reportPreview")

    if (!modal || !modalTitle || !reportPreview) return

    // Set modal title
    const monthName = new Date(year, month - 1).toLocaleString("default", { month: "long" })
    modalTitle.textContent = `${monthName} ${year} Report`

    // Show loading state
    reportPreview.innerHTML = `
            <div class="loading-state">
                <i class="fas fa-spinner fa-spin"></i>
                <p>Loading report...</p>
            </div>
        `

    // Store current report info
    this.currentReportData = { year, month }

    // Show modal
    modal.style.display = "block"
    document.body.style.overflow = "hidden"

    try {
      const response = await fetch(`/api/monthly-report/${year}/${month}`)
      if (response.ok) {
        const reportData = await response.json()
        this.renderReportPreview(reportData)
      } else {
        throw new Error("Failed to load report data")
      }
    } catch (error) {
      console.error("Error loading report:", error)
      reportPreview.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-exclamation-triangle"></i>
                    <h3>Error Loading Report</h3>
                    <p>Failed to load report data. Please try again.</p>
                </div>
            `
    }
  }

  renderReportPreview(data) {
    const reportPreview = document.getElementById("reportPreview")
    if (!reportPreview) return

    const savingsClass = data.total_saving >= 0 ? "positive" : "negative"

    reportPreview.innerHTML = `
            <div class="preview-summary">
                <div class="summary-card">
                    <h4>Total Income</h4>
                    <p class="summary-value income">₹${data.total_income.toLocaleString("en-IN", { minimumFractionDigits: 2 })}</p>
                </div>
                <div class="summary-card">
                    <h4>Total Expenses</h4>
                    <p class="summary-value expense">₹${data.total_expense.toLocaleString("en-IN", { minimumFractionDigits: 2 })}</p>
                </div>
                <div class="summary-card">
                    <h4>Net Savings</h4>
                    <p class="summary-value saving ${savingsClass}">₹${data.total_saving.toLocaleString("en-IN", { minimumFractionDigits: 2 })}</p>
                </div>
            </div>
            
            <div class="charts-section">
                <div class="chart-container">
                    <h4>Expense Breakdown</h4>
                    <div class="chart-wrapper">
                        <canvas id="expenseChart"></canvas>
                    </div>
                </div>
                <div class="chart-container">
                    <h4>Income Sources</h4>
                    <div class="chart-wrapper">
                        <canvas id="incomeChart"></canvas>
                    </div>
                </div>
            </div>
            
            <div class="insights-section">
                <h4><i class="fas fa-lightbulb"></i> Financial Insights</h4>
                <div id="insightsContainer"></div>
            </div>
        `

    // Render charts
    this.renderCharts(data)
    this.renderInsights(data)
  }

  renderCharts(data) {
    // Destroy existing charts
    Object.values(this.charts).forEach((chart) => {
      if (chart) chart.destroy()
    })
    this.charts = {}

    // Expense Chart
    if (data.expense_categories && data.expense_categories.length > 0) {
      const expenseCtx = document.getElementById("expenseChart")
      if (expenseCtx) {
        this.charts.expense = new Chart(expenseCtx, {
          type: "doughnut",
          data: {
            labels: data.expense_categories.map((cat) => cat.name),
            datasets: [
              {
                data: data.expense_categories.map((cat) => cat.amount),
                backgroundColor: [
                  "#ef4444",
                  "#f97316",
                  "#eab308",
                  "#22c55e",
                  "#06b6d4",
                  "#3b82f6",
                  "#8b5cf6",
                  "#ec4899",
                ],
                borderWidth: 2,
                borderColor: "#ffffff",
              },
            ],
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: {
                position: "bottom",
                labels: {
                  padding: 20,
                  usePointStyle: true,
                },
              },
              tooltip: {
                callbacks: {
                  label: (context) => {
                    const value = context.parsed
                    const total = context.dataset.data.reduce((a, b) => a + b, 0)
                    const percentage = ((value / total) * 100).toFixed(1)
                    return `${context.label}: ₹${value.toLocaleString("en-IN")} (${percentage}%)`
                  },
                },
              },
            },
          },
        })
      }
    } else {
      const expenseChart = document.querySelector("#expenseChart")
      if (expenseChart) {
        expenseChart.closest(".chart-wrapper").innerHTML =
          '<div class="no-data-message">No expense data available</div>'
      }
    }

    // Income Chart
    if (data.income_categories && data.income_categories.length > 0) {
      const incomeCtx = document.getElementById("incomeChart")
      if (incomeCtx) {
        this.charts.income = new Chart(incomeCtx, {
          type: "doughnut",
          data: {
            labels: data.income_categories.map((cat) => cat.name),
            datasets: [
              {
                data: data.income_categories.map((cat) => cat.amount),
                backgroundColor: [
                  "#22c55e",
                  "#16a34a",
                  "#15803d",
                  "#166534",
                  "#14532d",
                  "#052e16",
                  "#84cc16",
                  "#65a30d",
                ],
                borderWidth: 2,
                borderColor: "#ffffff",
              },
            ],
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: {
                position: "bottom",
                labels: {
                  padding: 20,
                  usePointStyle: true,
                },
              },
              tooltip: {
                callbacks: {
                  label: (context) => {
                    const value = context.parsed
                    const total = context.dataset.data.reduce((a, b) => a + b, 0)
                    const percentage = ((value / total) * 100).toFixed(1)
                    return `${context.label}: ₹${value.toLocaleString("en-IN")} (${percentage}%)`
                  },
                },
              },
            },
          },
        })
      }
    } else {
      const incomeChart = document.querySelector("#incomeChart")
      if (incomeChart) {
        incomeChart.closest(".chart-wrapper").innerHTML = '<div class="no-data-message">No income data available</div>'
      }
    }
  }

  renderInsights(data) {
    const container = document.getElementById("insightsContainer")
    if (!container) return

    const insights = []

    // Savings rate insight
    if (data.total_income > 0) {
      const savingsRate = (data.total_saving / data.total_income) * 100
      let insightClass = "positive"
      let insightText = ""

      if (savingsRate >= 20) {
        insightText = `🎉 Excellent! You saved ${savingsRate.toFixed(1)}% of your income this month. Keep up the great work!`
        insightClass = "positive"
      } else if (savingsRate >= 10) {
        insightText = `👍 Good job! You saved ${savingsRate.toFixed(1)}% of your income. Try to reach 20% for optimal savings.`
        insightClass = "positive"
      } else if (savingsRate > 0) {
        insightText = `⚠️ You saved ${savingsRate.toFixed(1)}% of your income. Consider reducing expenses to increase savings.`
        insightClass = "warning"
      } else {
        insightText = `🚨 You spent more than you earned this month. Review your expenses and create a budget.`
        insightClass = "negative"
      }

      insights.push({ text: insightText, class: insightClass })
    }

    // Top expense category
    if (data.expense_categories && data.expense_categories.length > 0) {
      const topExpense = data.expense_categories[0]
      const percentage = data.total_expense > 0 ? ((topExpense.amount / data.total_expense) * 100).toFixed(1) : 0

      insights.push({
        text: `📊 Your highest expense category is "${topExpense.name}" at ${percentage}% of total expenses (₹${topExpense.amount.toLocaleString("en-IN")}).`,
        class: "info",
      })
    }

    // Transaction frequency
    if (data.transaction_count > 0) {
      const avgPerDay = (data.transaction_count / 30).toFixed(1)
      insights.push({
        text: `📈 You made ${data.transaction_count} transactions this month (average ${avgPerDay} per day).`,
        class: "info",
      })
    }

    // Render insights
    container.innerHTML = insights
      .map((insight) => `<div class="insight-item ${insight.class}">${insight.text}</div>`)
      .join("")

    if (insights.length === 0) {
      container.innerHTML = '<div class="no-data-message">No insights available for this period.</div>'
    }
  }

  closeModal(modalId = "reportModal") {
    const modal = document.getElementById(modalId)
    if (modal) {
      modal.style.display = "none"
      document.body.style.overflow = ""
    }

    // Destroy charts to prevent memory leaks
    Object.values(this.charts).forEach((chart) => {
      if (chart) chart.destroy()
    })
    this.charts = {}

    this.currentReportData = null
  }

  async downloadReport(year, month) {
    try {
      this.showMessage("Generating PDF...", "info")

      const response = await fetch(`/api/monthly-report/${year}/${month}/pdf`)
      if (response.ok) {
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement("a")
        a.href = url
        a.download = `Monthly_Report_${new Date(year, month - 1).toLocaleString("default", { month: "long" })}_${year}.pdf`
        document.body.appendChild(a)
        a.click()
        window.URL.revokeObjectURL(url)
        document.body.removeChild(a)

        this.showMessage("Report downloaded successfully", "success")
      } else {
        throw new Error("Failed to generate PDF")
      }
    } catch (error) {
      console.error("Error downloading report:", error)
      this.showMessage("Failed to download report", "error")
    }
  }

  async downloadCurrentReport() {
    if (this.currentReportData) {
      await this.downloadReport(this.currentReportData.year, this.currentReportData.month)
    }
  }

  async emailReport(year, month) {
    try {
      this.showMessage("Sending email...", "info")

      const response = await fetch(`/api/send-monthly-report/${year}/${month}`, {
        method: "POST",
      })

      if (response.ok) {
        this.showMessage("Report sent to your email successfully", "success")
      } else {
        const error = await response.json()
        throw new Error(error.error || "Failed to send email")
      }
    } catch (error) {
      console.error("Error sending email:", error)
      this.showMessage("Failed to send email", "error")
    }
  }

  async emailCurrentReport() {
    if (this.currentReportData) {
      await this.emailReport(this.currentReportData.year, this.currentReportData.month)
    }
  }

  showEmptyState(message) {
    const grid = document.getElementById("reportsList")
    if (grid) {
      grid.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-file-alt"></i>
                <h3>No Reports Available</h3>
                <p>${message}</p>
            </div>
        `
    }
  }

  showMessage(message, type = "info") {
    // Remove existing messages
    const existingMessages = document.querySelectorAll(".notification")
    existingMessages.forEach((msg) => msg.remove())

    // Create new message
    const messageDiv = document.createElement("div")
    messageDiv.className = `notification ${type}`
    messageDiv.innerHTML = `
            <i class="fas fa-${type === "success" ? "check-circle" : type === "error" ? "exclamation-circle" : "info-circle"}"></i>
            <span>${message}</span>
            <button class="notification-close" onclick="this.parentElement.remove()">
                <i class="fas fa-times"></i>
            </button>
        `

    // Insert at the top of body
    document.body.appendChild(messageDiv)

    // Auto remove after 5 seconds
    setTimeout(() => {
      if (messageDiv.parentNode) {
        messageDiv.remove()
      }
    }, 5000)
  }
}

// Initialize when DOM is loaded
document.addEventListener("DOMContentLoaded", () => {
  new ReportsManager()
})
