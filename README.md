# Kanakkupulla (கணக்குப்புள்ள)
## Windows Personal Finance, Expense Tracking & Financial Analytics Application

Kanakkupulla is an enterprise-grade, comprehensive personal and family financial management desktop application for Windows built using Python 3.11, PySide6 (Qt6), SQLite, SQLAlchemy, and Pandas.

### Key Features
- **100% Offline & Private**: Zero external cloud dependency; your personal financial records stay securely on your Windows desktop.
- **Accurate Financial Engine**: All monetary calculations operate using integer paise (1 INR = 100 paise) avoiding binary floating-point roundoff errors.
- **Multi-User & Family Support**: Record who made the payment (`Paid By`), who benefits (`Expense For`), and who entered it (`Created By`).
- **Comprehensive Expense Management**: Daily expenses, occasional event-based tracking (Diwali, Weddings, Renovations).
- **Accounts & Balance Management**: Seamlessly handle Cash, Savings Accounts, Current Accounts, UPI wallets, and Credit Cards without double-counting bill settlements.
- **Financial Projections & Planning**: Goal tracking, EMI schedules, and future forecast modeling.
- **Indian Financial Ecosystem**: Native support for Indian currency formatting (`₹1,00,000.00`), DD-MM-YYYY date formats, and localized expenditure categories.

---

### Installation & Setup

1. **Prerequisites**:
   - Python 3.11+ 64-bit on Windows.

2. **Setup Virtual Environment & Install Dependencies**:
   ```powershell
   py -3.11 -m venv venv
   .\venv\Scripts\pip install -r requirements.txt
   ```

3. **Run Application**:
   ```powershell
   .\venv\Scripts\python main.py
   ```

   **Default Credentials**:
   - Username: `admin`
   - Password: `admin123`

---

### Running Automated Tests
```powershell
.\venv\Scripts\pytest tests/ -v
```
# Kanakkupulla
