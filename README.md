# Kanakkupulla (கணக்குப்புள்ள) 🪙
### *Enterprise-Grade, 100% Offline-First Personal & Family Finance Desktop Platform*

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![PySide6](https://img.shields.io/badge/PySide6-Qt6-41CD52?style=for-the-badge&logo=qt&logoColor=white)](https://wiki.qt.io/Qt_for_Python)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=white)](https://www.sqlalchemy.org/)
[![SQLite](https://img.shields.io/badge/SQLite-WAL_Mode-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![Tests](https://img.shields.io/badge/Tests-48%20Passed-success?style=for-the-badge&logo=pytest&logoColor=white)](https://pytest.org/)
[![Security](https://img.shields.io/badge/Password_Security-Argon2id-blue?style=for-the-badge)](https://argon2-cffi.readthedocs.io/)
[![Platform](https://img.shields.io/badge/Platform-Windows%20Desktop-0078D6?style=for-the-badge&logo=windows&logoColor=white)](https://microsoft.com/windows)

---

## 🌟 Executive Overview

**Kanakkupulla (கணக்குப்புள்ள)** is a standalone, local-first Windows desktop financial operating system designed for modern Indian households and individuals. Built with **Python 3.11+**, **PySide6 (Qt6)**, and **SQLAlchemy 2.x**, it eliminates cloud lock-in, recurring subscriptions, and third-party data tracking.

All financial state is stored locally inside an ACID-compliant, WAL-mode SQLite database using integer paise arithmetic ($1\text{ INR} = 100\text{ paise}$) and an immutable, balanced double-entry general ledger.

---

## 🏗️ Core Architecture & Invariants

```
                                  +------------------------------------+
                                  |     Kanakkupulla Windows Desktop   |
                                  |   (PySide6 Qt6 Fintech Dark UI)    |
                                  +-----------------+------------------+
                                                    |
                      +-----------------------------+-----------------------------+
                      |                                                           |
                      v                                                           v
+------------------------------------+                     +------------------------------------+
|       Presentation Layer           |                     |       Application & Auth           |
| • 19 Stacked Responsive Pages      |                     | • Argon2id Secure Password Hashing |
| • Dual-Mode Family/Personal View   |                     | • Role-Based Access Control (RBAC) |
| • Live Charts & Interactive Heatmap|                     | • Session Context & Multi-User     |
+-----------------+------------------+                     +------------------+-----------------+
                  |                                                           |
                  +-----------------------------+-----------------------------+
                                                |
                                                v
                        +-----------------------------------------------+
                        |          Financial Services Layer             |
                        | • Core Expenses & Multi-User Attribution      |
                        | • Income Management & Budget Utilization      |
                        | • Savings Goals & Investment Portfolio Engine |
                        | • Loan Amortization (Mathematical EMI)        |
                        | • Rule-Based Recurring Scheduler              |
                        | • Smart Receipt OCR Pre-fill Engine           |
                        +-----------------------+-----------------------+
                                                |
                                                v
                        +-----------------------------------------------+
                        |      Double-Entry General Ledger Engine       |
                        | • Invariant: sum(Debits) == sum(Credits)      |
                        | • Multi-Account Transfers (Rule 1)            |
                        | • Credit Card vs Bill Settlement (Rule 2)     |
                        | • Principal / Interest Amortization (Rule 4)  |
                        | • Audit Trails & Reversible Refunds (Rule 5)  |
                        +-----------------------+-----------------------+
                                                |
                                                v
                        +-----------------------------------------------+
                        |        Local SQLite Database Storage          |
                        | • 24 Normalized SQLAlchemy Entities           |
                        | • WAL Mode (Write-Ahead Logging) + ForeignKeys|
                        | • Integer Paise Precision (Zero Float Errors) |
                        | • Checkpointed .kpk Compressed Backups        |
                        +-----------------------------------------------+
```

---

## 📐 The Five Mandatory Accounting Invariants

1. **Rule 1 (Internal Account Transfers)**: Moving funds between owned accounts (e.g., Bank to Cash or Bank A to Bank B) debits the destination asset and credits the source asset without generating expense or income.
2. **Rule 2 (Credit Card Settlement)**: A credit card purchase registers as an expense and increases card liability. Settling the credit card bill reduces bank assets and clears the card liability without duplicating expenses.
3. **Rule 3 (Savings Goals Funding)**: Allocating money towards a savings goal is treated as a double-entry balance sheet transfer from liquid cash to goal reserves.
4. **Rule 4 (Loan Amortization & EMIs)**: Every loan repayment automatically computes interest expense based on the mathematical formula:
   $$\text{EMI} = \frac{P \cdot r \cdot (1+r)^n}{(1+r)^n - 1}$$
   The payment is split between principal reduction (liability) and interest cost (expense).
5. **Rule 5 (Refunds & Reversals)**: Returned items or refunds link back to original transaction identifiers, posting debit/credit reversals that restore account balances and deduct recorded category expenses.

---

## 📊 Modules & Functional Matrix

| # | Screen / Module | Functional Highlights |
|---|---|---|
| **01** | **Master Dashboard** | 8 Master KPIs, dual-mode (Consolidated Family vs Individual Member), spend trajectory chart. |
| **02** | **Daily Expenses** | Instant entry, search, multi-user attribution (Creator, Payer, Beneficiary), receipts. |
| **03** | **Other Expenses** | Occasional & discretionary expenses, festivals, major vacation purchases. |
| **04** | **Income Management** | Salary, freelance, dividend, and rental income logging with bank credit. |
| **05** | **Family Management** | Multi-user roles (Admin, Member, Viewer), permissions, and avatars. |
| **06** | **Category Management** | Tree structure with parent categories, custom subcategories, and color tags. |
| **07** | **Accounts & Payments** | Bank accounts, cash drawers, credit cards, digital wallets, and reconciliation. |
| **08** | **General Ledger** | Complete double-entry debit/credit journals and audit log verification. |
| **09** | **Savings Goals** | Target funds, emergency reserves, monthly milestone calculations. |
| **10** | **Investments Portfolio**| Mutual funds, equities, FDs, PPF, gold, real-time market valuations & P&L. |
| **11** | **Budget Management** | Monthly/Quarterly category allocations, 4-tier alerts (Normal, Caution, Warning, Exceeded). |
| **12** | **Loans & EMIs** | Loan master, amortization schedule, principal vs interest auto-split. |
| **13** | **Financial Planning** | Liquid cash runway calculator, 12-month forward predictive forecast. |
| **14** | **Recurring Rules** | Auto-generating subscription rules for OTT, broadband, insurance, and utilities. |
| **15** | **Financial Calendar** | Monthly view showing daily spend intensity, bill reminders, and EMI due dates. |
| **16** | **Reports & Exports** | Multi-tab Excel (.xlsx) workbook, publication-grade PDF report (ReportLab), CSV. |
| **17** | **Receipt OCR Scanner** | Heuristic & image parser extracting merchant, transaction date, amount, and category. |
| **18** | **Backup & Restore** | Encapsulated `.kpk` archives bundling SQLite DB, receipts, and JSON manifest. |
| **19** | **Application Settings**| Theme toggle (Fintech Dark / Clean Light), preferences, and system diagnostics. |

---

## 🚀 Quick Start Guide

### Prerequisites
- **Windows 10 / 11** (64-bit)
- **Python 3.11+** installed and added to PATH
- **PowerShell 7** or Windows PowerShell

### 1. Clone & Set Up Environment
```powershell
# Navigate to project directory
cd h:\Arun_Sir\16_AI\Kanakkupulla

# Create Python virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install production dependencies
pip install -r requirements.txt
```

### 2. Initialize Seed Database
```powershell
# Seeds default family profile, categories, accounts, and admin user
python -m database.seed
```

> **Default Admin Credentials:**
> - **Username**: `admin`
> - **Password**: `admin123`

### 3. Launch Kanakkupulla Desktop App
```powershell
$env:PYTHONPATH="."
.\venv\Scripts\python main.py
```

---

## 🧪 Comprehensive Test Suite

Kanakkupulla includes 48 automated test suites spanning all 8 development phases:

```powershell
# Run the entire test suite
$env:PYTHONPATH="."
.\venv\Scripts\pytest tests/ -v
```

### Test Coverage Highlights:
- **Phase 1**: Database schema creation, Argon2id hashing, and user authentication.
- **Phase 2**: Core expenses, receipt storage, and search indexer.
- **Phase 3**: General ledger invariant check ($\sum \text{Debits} == \sum \text{Credits}$) and Rule 2 credit card handling.
- **Phase 4**: Family budgets, savings goals, investment portfolio, and loan amortization.
- **Phase 5**: Recurring rules execution engine, financial calendar, and cash runway projections.
- **Phase 6**: Excel/PDF exports and smart receipt OCR parsing.
- **Phase 7**: `.kpk` checkpointed backups, SQLite PRAGMA integrity verification, and diagnostic health checks.
- **Phase 8**: Full end-to-end user lifecycle smoke test and headless 19-page PySide6 UI navigation.

---

## 📦 Packaging & Distribution

### Building the Standalone Executable (.exe)
Kanakkupulla is packaged into a self-contained Windows executable via PyInstaller:

```powershell
.\venv\Scripts\pyinstaller Kanakkupulla.spec --clean --noconfirm
```
The compiled output is placed in `dist/Kanakkupulla/Kanakkupulla.exe`.

### Generating the Inno Setup Windows Installer
The Inno Setup script is pre-configured at `installer/kanakkupulla_installer.iss`:
1. Open `installer/kanakkupulla_installer.iss` in **Inno Setup Compiler**.
2. Click **Build > Compile** (or run `ISCC.exe installer/kanakkupulla_installer.iss`).
3. The setup executable `Kanakkupulla_Setup_v1.0.0.exe` will be generated with start menu shortcuts, uninstaller, and desktop icon.

---

## 🔒 Security & Privacy Commitments

- **Zero Cloud Leakage**: No telemetry, analytics pings, cloud databases, or mandatory user accounts.
- **Argon2id Hashing**: Password hashes use memory-hard Argon2id configured with 64 MB memory and 3 iterations.
- **Data Protection**: Database files and receipt attachments reside entirely in the user's local application data directory.
- **Atomic Integrity**: SQLite WAL mode and foreign key constraints prevent database corruption during sudden power losses.

---

## 📜 License
Kanakkupulla is proprietary, private software developed for offline-first personal and family wealth management.
