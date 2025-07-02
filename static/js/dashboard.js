import { Chart } from "@/components/ui/chart"
// Dashboard JavaScript
let currentTab = "records"
let accounts = []
let categories = []
let chart = null

// Initialize dashboard when page loads
document.addEventListener("DOMContentLoaded", () => {
  console.log("Dashboard loading...")
  initializeDashboard()
  loadDashboardData()
  setupEventListeners()
})

function initializeDashboard() {
  // Set up tab navigation
  const navItems = document.querySelectorAll(".nav-item")
  navItems.forEach((item) => {
    item.addEventListener("click", function (e) {
      e.preventDefault()
      const tab = this.getAttribute("data-tab")
      switchTab(tab)
    })
  })

  // Set up add transaction button
  const addTransactionBtn = document.getElementById("addTransactionBtn")
  if (addTransactionBtn) {
    addTransactionBtn.addEventListener("click", () => openModal("addTransactionModal"))
  }

  // Set up transaction form
  setupTransactionForm()

  // Set up account form
  setupAccountForm()
}

function switchTab(tabName) {
  // Update navigation
  document.querySelectorAll(".nav-item").forEach((item) => {
    item.classList.remove("active")
  })
  document.querySelector(`[data-tab="${tabName}"]`).classList.add("active")

  // Update content
  document.querySelectorAll(".tab-content").forEach((content) => {
    content.classList.remove("active")
  })
  document.getElementById(`${tabName}-tab`).classList.add("active")

  // Update page title
  const pageTitle = document.querySelector(".page-title")
  pageTitle.textContent = tabName.charAt(0).toUpperCase() + tabName.slice(1)

  currentTab = tabName

  // Load tab-specific data
  loadTabData(tabName)
}

async function loadDashboardData() {
  try {
    console.log("Loading dashboard data...")

    // Load summary data
    const summaryData = await apiRequest("/api/dashboard_data")
    console.log("Summary data:", summaryData)
    updateSummaryCards(summaryData)

    // Load accounts and categories
    accounts = await apiRequest("/api/accounts")
    categories = await apiRequest("/api/categories")

    console.log("Accounts:", accounts)
    console.log("Categories:", categories)

    // Update transaction form options
    updateTransactionFormOptions()

    // Load initial tab data
    loadTabData(currentTab)
  } catch (error) {
    console.error("Failed to load dashboard data:", error)
    showNotification("Failed to load dashboard data", "error")
  }
}

function updateSummaryCards(data) {
  // Update all summary cards across tabs
  const incomeElements = document.querySelectorAll("#totalIncome, #analysisIncome, #budgetIncome, #accountIncome")
  const expenseElements = document.querySelectorAll("#totalExpense, #analysisExpense, #budgetExpense, #accountExpense")
  const savingElements = document.querySelectorAll("#totalSaving, #analysisSaving, #budgetSaving, #accountSaving")

  incomeElements.forEach((el) => {
    el.textContent = formatCurrency(data.total_income)
  })

  expenseElements.forEach((el) => {
    el.textContent = formatCurrency(data.total_expense)
  })

  savingElements.forEach((el) => {
    el.textContent = formatCurrency(data.total_saving)
    el.className = `amount ${data.total_saving >= 0 ? "text-success" : "text-danger"}`
  })
}

function setupTransactionForm() {
  const typeButtons = document.querySelectorAll(".type-btn")
  const transactionForm = document.getElementById("transactionForm")

  // Transaction type selection
  typeButtons.forEach((btn) => {
    btn.addEventListener("click", function () {
      typeButtons.forEach((b) => b.classList.remove("active"))
      this.classList.add("active")

      const type = this.getAttribute("data-type")
      updateFormForType(type)
    })
  })

  // Form submission
  if (transactionForm) {
    transactionForm.addEventListener("submit", async (e) => {
      e.preventDefault()
      await submitTransaction()
    })
  }
}

function setupAccountForm() {
  const accountForm = document.getElementById("accountForm")
  if (accountForm) {
    accountForm.addEventListener("submit", async (e) => {
      e.preventDefault()
      await submitAccount()
    })
  }
}

function updateFormForType(type) {
  const categoryGroup = document.getElementById("categoryGroup")
  const toAccountGroup = document.getElementById("toAccountGroup")
  const categorySelect = document.getElementById("transactionCategory")
  const toAccountSelect = document.getElementById("toAccount")

  if (type === "transfer") {
    categoryGroup.style.display = "none"
    toAccountGroup.style.display = "block"
    categorySelect.removeAttribute("required")
    toAccountSelect.setAttribute("required", "required")
  } else {
    categoryGroup.style.display = "block"
    toAccountGroup.style.display = "none"
    categorySelect.setAttribute("required", "required")
    toAccountSelect.removeAttribute("required")

    // Update categories based on type
    updateCategoriesForType(type)
  }
}

function updateCategoriesForType(type) {
  const categorySelect = document.getElementById("transactionCategory")
  categorySelect.innerHTML = '<option value="">Select Category</option>'

  const filteredCategories = categories.filter((cat) => cat.type === type)
  filteredCategories.forEach((category) => {
    const option = document.createElement("option")
    option.value = category.id
    option.textContent = category.name
    categorySelect.appendChild(option)
  })
}

function updateTransactionFormOptions() {
  const accountSelect = document.getElementById("transactionAccount")
  const toAccountSelect = document.getElementById("toAccount")

  if (!accountSelect || !toAccountSelect) return

  // Clear existing options
  accountSelect.innerHTML = '<option value="">Select Account</option>'
  toAccountSelect.innerHTML = '<option value="">Select Account</option>'

  // Add account options
  accounts.forEach((account) => {
    const option1 = document.createElement("option")
    option1.value = account.id
    option1.textContent = `${account.name} (${formatCurrency(account.balance)})`
    accountSelect.appendChild(option1)

    const option2 = document.createElement("option")
    option2.value = account.id
    option2.textContent = `${account.name} (${formatCurrency(account.balance)})`
    toAccountSelect.appendChild(option2)
  })

  // Initialize with expense categories
  updateCategoriesForType("expense")
}

async function submitTransaction() {
  const form = document.getElementById("transactionForm")
  const formData = new FormData(form)
  const activeTypeBtn = document.querySelector(".type-btn.active")
  const type = activeTypeBtn.getAttribute("data-type")

  const transactionData = {
    type: type,
    account_id: Number.parseInt(formData.get("account_id")),
    amount: Number.parseFloat(formData.get("amount")),
  }

  if (type !== "transfer") {
    transactionData.category_id = Number.parseInt(formData.get("category_id"))
  } else {
    transactionData.to_account_id = Number.parseInt(formData.get("to_account_id"))
  }

  try {
    const response = await apiRequest("/api/add_transaction", {
      method: "POST",
      body: JSON.stringify(transactionData),
    })

    if (response.success) {
      showNotification("Transaction added successfully", "success")
      closeModal("addTransactionModal")
      form.reset()

      // Reset to expense type
      document.querySelectorAll(".type-btn").forEach((btn) => btn.classList.remove("active"))
      document.querySelector('[data-type="expense"]').classList.add("active")
      updateFormForType("expense")

      // Reload dashboard data
      loadDashboardData()
    } else {
      showNotification(response.error || "Failed to add transaction", "error")
    }
  } catch (error) {
    console.error("Transaction submission error:", error)
    showNotification("Failed to add transaction", "error")
  }
}

async function submitAccount() {
  const form = document.getElementById("accountForm")
  const formData = new FormData(form)

  const accountData = {
    name: formData.get("name"),
    initial_amount: Number.parseFloat(formData.get("initial_amount")) || 0,
    account_type: "personal",
  }

  try {
    const response = await apiRequest("/api/accounts", {
      method: "POST",
      body: JSON.stringify(accountData),
    })

    if (response.success) {
      showNotification("Account added successfully", "success")
      closeModal("addAccountModal")
      form.reset()

      // Reload data
      accounts = await apiRequest("/api/accounts")
      updateTransactionFormOptions()
      if (currentTab === "account") {
        loadAccountData()
      }
    } else {
      showNotification(response.error || "Failed to add account", "error")
    }
  } catch (error) {
    console.error("Account submission error:", error)
    showNotification("Failed to add account", "error")
  }
}

function loadTabData(tabName) {
  switch (tabName) {
    case "records":
      loadRecordsData()
      break
    case "analysis":
      loadAnalysisData()
      break
    case "budget":
      loadBudgetData()
      break
    case "account":
      loadAccountData()
      break
    case "category":
      loadCategoryData()
      break
  }
}

async function loadRecordsData() {
  try {
    const transactions = await apiRequest("/api/transactions")
    displayTransactions(transactions)
  } catch (error) {
    console.error("Failed to load transactions:", error)
    showNotification("Failed to load transactions", "error")
  }
}

function displayTransactions(transactions) {
  const transactionsList = document.getElementById("transactionsList")

  if (!transactions || transactions.length === 0) {
    transactionsList.innerHTML =
      '<div class="empty-message"><i class="fas fa-receipt"></i><p>No transactions found</p><small>Add your first transaction using the + button</small></div>'
    return
  }

  transactionsList.innerHTML = transactions
    .map(
      (transaction) => `
            <div class="transaction-item">
                <div class="transaction-info">
                    <div class="transaction-type ${transaction.type}">
                        <i class="fas fa-${getTransactionIcon(transaction.type)}"></i>
                    </div>
                    <div class="transaction-details">
                        <h4>${transaction.category_name || "Transfer"}</h4>
                        <p>${transaction.account_name}${transaction.to_account_name ? ` → ${transaction.to_account_name}` : ""}</p>
                        <small>${formatDate(transaction.transaction_date)}</small>
                    </div>
                </div>
                <div class="transaction-amount ${transaction.type}">
                    ${transaction.type === "expense" ? "-" : "+"}${formatCurrency(transaction.amount)}
                </div>
                <button class="btn-delete" onclick="deleteTransaction(${transaction.id})" title="Delete transaction">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        `,
    )
    .join("")
}

function getTransactionIcon(type) {
  switch (type) {
    case "income":
      return "arrow-up"
    case "expense":
      return "arrow-down"
    case "transfer":
      return "exchange-alt"
    default:
      return "circle"
  }
}

function formatDate(dateString) {
  if (!dateString) return "Unknown"
  return new Date(dateString).toLocaleDateString("en-IN")
}

async function deleteTransaction(transactionId) {
  if (!confirm("Are you sure you want to delete this transaction?")) {
    return
  }

  try {
    const response = await apiRequest(`/api/transactions/${transactionId}`, {
      method: "DELETE",
    })

    if (response.success) {
      showNotification("Transaction deleted successfully", "success")
      loadDashboardData()
    } else {
      showNotification("Failed to delete transaction", "error")
    }
  } catch (error) {
    console.error("Failed to delete transaction:", error)
    showNotification("Failed to delete transaction", "error")
  }
}

async function loadAnalysisData() {
  const analysisType = document.getElementById("analysisType")
  if (!analysisType) return

  analysisType.addEventListener("change", updateAnalysisChart)
  updateAnalysisChart()
}

async function updateAnalysisChart() {
  const analysisType = document.getElementById("analysisType").value
  const ctx = document.getElementById("analysisChart")

  if (!ctx) return

  try {
    const response = await apiRequest(`/api/analysis/${analysisType}`)

    if (chart) {
      chart.destroy()
    }

    if (response.labels.length === 0) {
      ctx.getContext("2d").clearRect(0, 0, ctx.width, ctx.height)
      const container = ctx.parentElement
      container.innerHTML =
        '<div class="empty-message"><i class="fas fa-chart-pie"></i><p>No data available</p><small>Add some transactions to see analysis</small></div>'
      return
    }

    // Restore canvas if it was replaced
    if (!document.getElementById("analysisChart")) {
      const container = document.querySelector(".chart-container")
      container.innerHTML = '<canvas id="analysisChart"></canvas>'
    }

    const canvas = document.getElementById("analysisChart")
    if (analysisType.includes("overview")) {
      createPieChart(canvas, response)
    } else {
      createLineChart(canvas, response)
    }
  } catch (error) {
    console.error("Failed to load analysis data:", error)
    showNotification("Failed to load analysis data", "error")
  }
}

function createPieChart(ctx, data) {
  chart = new Chart(ctx, {
    type: "pie",
    data: {
      labels: data.labels,
      datasets: [
        {
          data: data.values,
          backgroundColor: ["#3b82f6", "#ef4444", "#10b981", "#f59e0b", "#8b5cf6", "#06b6d4", "#f97316", "#84cc16"],
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: "bottom",
        },
      },
    },
  })
}

function createLineChart(ctx, data) {
  chart = new Chart(ctx, {
    type: "line",
    data: {
      labels: data.labels,
      datasets: [
        {
          label: "Amount",
          data: data.values,
          borderColor: "#3b82f6",
          backgroundColor: "rgba(59, 130, 246, 0.1)",
          tension: 0.4,
          fill: true,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            callback: (value) => "₹" + value.toLocaleString("en-IN"),
          },
        },
      },
    },
  })
}

async function loadBudgetData() {
  try {
    const budgets = await apiRequest("/api/budgets")
    displayBudgets(budgets)
  } catch (error) {
    console.error("Failed to load budget data:", error)
    showNotification("Failed to load budget data", "error")
  }
}

function displayBudgets(budgets) {
  const budgetCategories = document.getElementById("budgetCategories")
  const expenseCategories = categories.filter((cat) => cat.type === "expense")

  if (expenseCategories.length === 0) {
    budgetCategories.innerHTML =
      '<div class="empty-message"><i class="fas fa-wallet"></i><p>No expense categories found</p></div>'
    return
  }

  budgetCategories.innerHTML = expenseCategories
    .map((category) => {
      const budget = budgets.find((b) => b.category_id === category.id)
      const spent = budget ? budget.spent : 0
      const budgetAmount = budget ? budget.amount : 0
      const percentage = budgetAmount > 0 ? (spent / budgetAmount) * 100 : 0

      return `
                <div class="budget-item">
                    <div class="budget-header">
                        <h4>${category.name}</h4>
                        <div class="budget-actions">
                            <button class="btn btn-sm btn-outline" onclick="setBudget(${category.id}, '${category.name}', ${budgetAmount})">
                                <i class="fas fa-${budget ? "edit" : "plus"}"></i>
                                ${budget ? "Edit" : "Set"} Budget
                            </button>
                        </div>
                    </div>
                    ${
                      budget
                        ? `
                        <div class="budget-progress">
                            <div class="progress-bar">
                                <div class="progress-fill ${percentage > 100 ? "over-budget" : ""}" style="width: ${Math.min(percentage, 100)}%"></div>
                            </div>
                            <div class="budget-info">
                                <span>${formatCurrency(spent)} / ${formatCurrency(budgetAmount)}</span>
                                <span class="${percentage > 100 ? "text-danger" : "text-success"}">${percentage.toFixed(1)}%</span>
                            </div>
                        </div>
                    `
                        : '<div class="no-budget-message">No budget set for this category</div>'
                    }
                </div>
            `
    })
    .join("")
}

function setBudget(categoryId, categoryName, currentAmount = 0) {
  const amount = prompt(`Set budget for ${categoryName}:`, currentAmount || "")
  if (amount && !isNaN(amount) && Number.parseFloat(amount) > 0) {
    saveBudget(categoryId, Number.parseFloat(amount))
  }
}

async function saveBudget(categoryId, amount) {
  try {
    const response = await apiRequest("/api/budgets", {
      method: "POST",
      body: JSON.stringify({
        category_id: categoryId,
        amount: amount,
      }),
    })

    if (response.success) {
      showNotification("Budget saved successfully", "success")
      loadBudgetData()
    } else {
      showNotification("Failed to save budget", "error")
    }
  } catch (error) {
    console.error("Failed to save budget:", error)
    showNotification("Failed to save budget", "error")
  }
}

async function loadAccountData() {
  const accountsGrid = document.getElementById("accountsGrid")

  if (accounts.length === 0) {
    accountsGrid.innerHTML =
      '<div class="empty-message"><i class="fas fa-credit-card"></i><p>No accounts found</p></div>'
    return
  }

  accountsGrid.innerHTML = accounts
    .map(
      (account) => `
            <div class="account-card">
                <div class="account-header">
                    <h4>${account.name}</h4>
                    <span class="account-type">${account.type.toUpperCase()}</span>
                </div>
                <div class="account-balance ${account.balance >= 0 ? "positive" : "negative"}">
                    ${formatCurrency(account.balance)}
                </div>
                ${
                  account.type === "personal"
                    ? `
                    <div class="account-actions">
                        <button class="btn btn-sm btn-outline btn-danger" onclick="deleteAccount(${account.id})">
                            <i class="fas fa-trash"></i> Delete
                        </button>
                    </div>
                `
                    : ""
                }
            </div>
        `,
    )
    .join("")

  // Add "Add Account" button
  accountsGrid.innerHTML += `
        <div class="account-card add-account-card">
            <button class="btn btn-primary" onclick="openModal('addAccountModal')">
                <i class="fas fa-plus"></i>
                Add Personal Account
            </button>
        </div>
    `
}

async function deleteAccount(accountId) {
  if (!confirm("Are you sure you want to delete this account? All transactions will be affected.")) {
    return
  }

  try {
    const response = await apiRequest(`/api/accounts/${accountId}`, {
      method: "DELETE",
    })

    if (response.success) {
      showNotification("Account deleted successfully", "success")
      accounts = await apiRequest("/api/accounts")
      updateTransactionFormOptions()
      loadAccountData()
    } else {
      showNotification(response.error || "Failed to delete account", "error")
    }
  } catch (error) {
    console.error("Failed to delete account:", error)
    showNotification("Failed to delete account", "error")
  }
}

function loadCategoryData() {
  const incomeCategories = document.getElementById("incomeCategories")
  const expenseCategories = document.getElementById("expenseCategories")

  const incomeList = categories.filter((cat) => cat.type === "income")
  const expenseList = categories.filter((cat) => cat.type === "expense")

  incomeCategories.innerHTML = incomeList
    .map(
      (category) => `
            <div class="category-item">
                <span class="category-name">${category.name}</span>
                <div class="category-actions">
                    ${
                      !category.is_default
                        ? `
                        <button class="btn btn-sm btn-outline btn-danger" onclick="deleteCategory(${category.id})" title="Delete category">
                            <i class="fas fa-trash"></i>
                        </button>
                    `
                        : '<span class="default-badge">Default</span>'
                    }
                </div>
            </div>
        `,
    )
    .join("")

  expenseCategories.innerHTML = expenseList
    .map(
      (category) => `
            <div class="category-item">
                <span class="category-name">${category.name}</span>
                <div class="category-actions">
                    ${
                      !category.is_default
                        ? `
                        <button class="btn btn-sm btn-outline btn-danger" onclick="deleteCategory(${category.id})" title="Delete category">
                            <i class="fas fa-trash"></i>
                        </button>
                    `
                        : '<span class="default-badge">Default</span>'
                    }
                </div>
            </div>
        `,
    )
    .join("")
}

function addCategory(type) {
  const name = prompt(`Enter ${type} category name:`)
  if (name && name.trim()) {
    saveCategory(name.trim(), type)
  }
}

async function saveCategory(name, type) {
  try {
    const response = await apiRequest("/api/categories", {
      method: "POST",
      body: JSON.stringify({
        name: name,
        type: type,
      }),
    })

    if (response.success) {
      showNotification("Category added successfully", "success")
      categories = await apiRequest("/api/categories")
      loadCategoryData()
      updateTransactionFormOptions()
    } else {
      showNotification(response.error || "Failed to add category", "error")
    }
  } catch (error) {
    console.error("Failed to add category:", error)
    showNotification("Failed to add category", "error")
  }
}

async function deleteCategory(categoryId) {
  if (!confirm("Are you sure you want to delete this category? This action cannot be undone.")) {
    return
  }

  try {
    const response = await apiRequest(`/api/categories/${categoryId}`, {
      method: "DELETE",
    })

    if (response.success) {
      showNotification("Category deleted successfully", "success")
      categories = await apiRequest("/api/categories")
      loadCategoryData()
      updateTransactionFormOptions()
    } else {
      showNotification(response.error || "Failed to delete category", "error")
    }
  } catch (error) {
    console.error("Failed to delete category:", error)
    showNotification("Failed to delete category", "error")
  }
}

function setupEventListeners() {
  // Close modal when clicking outside
  document.addEventListener("click", (e) => {
    if (e.target.classList.contains("modal")) {
      closeModal(e.target.id)
    }
  })

  // Escape key to close modal
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      const activeModal = document.querySelector(".modal.active")
      if (activeModal) {
        closeModal(activeModal.id)
      }
    }
  })
}

// Utility functions
function openModal(modalId) {
  const modal = document.getElementById(modalId)
  if (modal) {
    modal.classList.add("active")
    document.body.style.overflow = "hidden"
  }
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId)
  if (modal) {
    modal.classList.remove("active")
    document.body.style.overflow = ""
  }
}

async function apiRequest(url, options = {}) {
  try {
    const response = await fetch(url, {
      headers: {
        "Content-Type": "application/json",
        ...options.headers,
      },
      ...options,
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    return await response.json()
  } catch (error) {
    console.error("API request failed:", error)
    throw error
  }
}

function formatCurrency(amount) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount)
}

function showNotification(message, type = "info") {
  // Remove existing notifications
  const existingNotifications = document.querySelectorAll(".notification")
  existingNotifications.forEach((notification) => notification.remove())

  const notification = document.createElement("div")
  notification.className = `notification notification-${type}`
  notification.innerHTML = `
        <i class="fas fa-${getNotificationIcon(type)}"></i>
        <span>${message}</span>
    `

  document.body.appendChild(notification)

  setTimeout(() => {
    notification.classList.add("show")
  }, 100)

  setTimeout(() => {
    notification.classList.remove("show")
    setTimeout(() => {
      if (notification.parentNode) {
        notification.parentNode.removeChild(notification)
      }
    }, 300)
  }, 3000)
}

function getNotificationIcon(type) {
  switch (type) {
    case "success":
      return "check-circle"
    case "error":
      return "exclamation-circle"
    case "warning":
      return "exclamation-triangle"
    default:
      return "info-circle"
  }
}
