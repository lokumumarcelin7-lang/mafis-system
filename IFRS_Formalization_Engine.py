# IFRS_Formalization_Engine.py
import pandas as pd

class IFRSFormalizationEngine:
    """
    MAFIS Enterprise Core: IFRS_Formalization_Engine.py
    Engineered to match QuickBooks Online & IASB Standard Reporting Templates.
    Enforces Net-Balance Trial Balance mapping and hierarchical presentation layers.
    """
    
    def __init__(self):
        # Universal Chart of Accounts (COA) with Standard Accounting Classifications
        self.chart_of_accounts = {
            "1100": {"name": "Cash and Cash Equivalents (Mobile Wallet)", "type": "Asset"},
            "2200": {"name": "Current Tax Liabilities (RRA Payable)", "type": "Liability"},
            "3200": {"name": "Retained Earnings / Capital Base", "type": "Equity"},
            "4100": {"name": "Revenue from Contracts with Customers (Gross Sales)", "type": "Revenue"},
            "5100": {"name": "Cost of Sales (COGS / Direct Business Expenses)", "type": "Expense"},
            "5200": {"name": "Distribution and Operational Processing Fees", "type": "Expense"},
            "5300": {"name": "Administrative Tax Expenses (Momo Tax Layer)", "type": "Expense"}
        }
        self.reset_ledger()

    def reset_ledger(self):
        self.general_ledger = []

    def generate_double_entry(self, transaction: dict) -> list:
        tx_id = transaction.get("TxID", "UNKNOWN")
        tx_type = transaction.get("Type", "UNKNOWN")
        amount = float(transaction.get("Amount", 0))
        stated_fee = float(transaction.get("SMS_Stated_Fee", 0))
        applied_fee = float(transaction.get("Applied_Transfer_Fee", 0))
        rra_tax = float(transaction.get("RRA_Tax", 0.0))
        
        entries = []
        active_fee = stated_fee if stated_fee > 0 else applied_fee

        if amount <= 0 or tx_id == "FAILED_QUAL_GATE":
            return entries

        # --- REVENUE FLOWS (Cash In) ---
        if "Cash In" in tx_type:
            entries.append({"TxID": tx_id, "AccountCode": "1100", "Debit": amount, "Credit": 0.0})
            entries.append({"TxID": tx_id, "AccountCode": "4100", "Debit": 0.0, "Credit": amount})

        # --- COMMERCIAL PURCHASES (Merchant Payments) ---
        elif "Merchant Payment" in tx_type:
            entries.append({"TxID": tx_id, "AccountCode": "5100", "Debit": amount, "Credit": 0.0})
            entries.append({"TxID": tx_id, "AccountCode": "1100", "Debit": 0.0, "Credit": amount})

        # --- OPERATIONAL DISBURSEMENTS (P2P Outbound) ---
        elif "P2P Transfer" in tx_type:
            entries.append({"TxID": tx_id, "AccountCode": "5100", "Debit": amount, "Credit": 0.0})
            entries.append({"TxID": tx_id, "AccountCode": "1100", "Debit": 0.0, "Credit": amount})

        # --- INTERMEDIARY FEES ---
        if active_fee > 0:
            entries.append({"TxID": tx_id, "AccountCode": "5200", "Debit": active_fee, "Credit": 0.0})
            entries.append({"TxID": tx_id, "AccountCode": "1100", "Debit": 0.0, "Credit": active_fee})

        # --- REGULATORY TAX LAYER ---
        if rra_tax > 0:
            entries.append({"TxID": tx_id, "AccountCode": "5300", "Debit": rra_tax, "Credit": 0.0})
            entries.append({"TxID": tx_id, "AccountCode": "2200", "Debit": 0.0, "Credit": rra_tax})

        # Quality Gate Check
        total_debit = sum(e["Debit"] for e in entries)
        total_credit = sum(e["Credit"] for e in entries)
        if round(total_debit - total_credit, 4) != 0.0:
            raise ValueError(f"IFRS Unbalanced Entry Violation on Tx {tx_id}")
            
        return entries

    def compile_bookkeeping_ledger(self, transaction_logs: list):
        self.reset_ledger()
        for tx in transaction_logs:
            self.general_ledger.extend(self.generate_double_entry(tx))
        return pd.DataFrame(self.general_ledger)

    def get_account_balances(self) -> dict:
        """Calculates historical balances per account code."""
        balances = {code: 0.0 for code in self.chart_of_accounts}
        for entry in self.general_ledger:
            code = entry["AccountCode"]
            balances[code] += (entry["Debit"] - entry["Credit"])
        return balances

    # =========================================================
    #   QUICKBOOKS STANDARD FINANCIAL REPORTS COMPILATION
    # =========================================================

    def compile_trial_balance(self) -> tuple:
        """Generates a QuickBooks-style Net-Balance Trial Balance."""
        balances = self.get_account_balances()
        trial_rows = []
        total_debits = 0.0
        total_credits = 0.0
        
        for code, details in self.chart_of_accounts.items():
            raw_bal = balances.get(code, 0.0)
            if raw_bal == 0:
                continue
                
            acct_type = details["type"]
            dr_val = 0.0
            cr_val = 0.0
            
            # QuickBooks Rule: Net presentation based on normal account balance sign
            if acct_type in ["Asset", "Expense"]:
                if raw_bal > 0:
                    dr_val = raw_bal
                else:
                    cr_val = abs(raw_bal)
            else: # Liability, Equity, Revenue (Normal Credit balance)
                # In our raw calculation, Debit - Credit means a normal credit balance comes out negative
                if raw_bal < 0:
                    cr_val = abs(raw_bal)
                else:
                    dr_val = raw_bal
            
            if dr_val > 0 or cr_val > 0:
                trial_rows.append({
                    "Account Code": code,
                    "Account Name": details["name"],
                    "Debit (RWF)": round(dr_val, 2),
                    "Credit (RWF)": round(cr_val, 2)
                })
                total_debits += dr_val
                total_credits += cr_val
                
        return pd.DataFrame(trial_rows), round(total_debits, 2), round(total_credits, 2)

    def compile_income_statement(self) -> tuple:
        """QuickBooks Pro Format: Multi-Step Income Statement (Profit & Loss)."""
        balances = self.get_account_balances()
        
        # Pull values and invert sign for normal credit balances (Revenue)
        revenue = abs(balances.get("4100", 0.0))
        cogs = balances.get("5100", 0.0)
        dist_fees = balances.get("5200", 0.0)
        tax_fees = balances.get("5300", 0.0)
        
        gross_profit = revenue - cogs
        total_opex = dist_fees + tax_fees
        net_income = gross_profit - total_opex
        
        statement_rows = [
            {"Account / Line Item": "Ordinary Income/Expense", "Amount (RWF)": ""},
            {"Account / Line Item": "   4100 · Revenue from Contracts with Customers", "Amount (RWF)": revenue},
            {"Account / Line Item": "Total Income", "Amount (RWF)": revenue},
            {"Account / Line Item": "Cost of Goods Sold", "Amount (RWF)": ""},
            {"Account / Line Item": "   5100 · Cost of Sales (COGS)", "Amount (RWF)": cogs},
            {"Account / Line Item": "Total COGS", "Amount (RWF)": cogs},
            {"Account / Line Item": "GROSS PROFIT", "Amount (RWF)": gross_profit},
            {"Account / Line Item": "Expense", "Amount (RWF)": ""},
            {"Account / Line Item": "   5200 · Distribution and Operational Processing Fees", "Amount (RWF)": dist_fees},
            {"Account / Line Item": "   5300 · Administrative Tax Expenses", "Amount (RWF)": tax_fees},
            {"Account / Line Item": "Total Expense", "Amount (RWF)": total_opex},
            {"Account / Line Item": "NET ORDINARY INCOME / NET PROFIT", "Amount (RWF)": net_income}
        ]
        return pd.DataFrame(statement_rows), net_income

    def compile_balance_sheet(self, net_income: float) -> pd.DataFrame:
        """QuickBooks Pro Format: Standard Hierarchical Balance Sheet."""
        balances = self.get_account_balances()
        cash = balances.get("1100", 0.0)
        rra_payable = abs(balances.get("2200", 0.0))
        retained_earnings = net_income
        
        sheet_rows = [
            {"Classification": "ASSETS", "Account / Line Item": "Current Assets", "Amount (RWF)": ""},
            {"Classification": "ASSETS", "Account / Line Item": "   1100 · Cash and Cash Equivalents (Wallet)", "Amount (RWF)": cash},
            {"Classification": "ASSETS", "Account / Line Item": "TOTAL CURRENT ASSETS", "Amount (RWF)": cash},
            {"Classification": "ASSETS", "Account / Line Item": "TOTAL ASSETS", "Amount (RWF)": cash},
            {"Classification": "LIABILITIES & EQUITY", "Account / Line Item": "Liabilities -> Current Liabilities", "Amount (RWF)": ""},
            {"Classification": "LIABILITIES & EQUITY", "Account / Line Item": "   2200 · Current Tax Liabilities (RRA)", "Amount (RWF)": rra_payable},
            {"Classification": "LIABILITIES & EQUITY", "Account / Line Item": "TOTAL CURRENT LIABILITIES", "Amount (RWF)": rra_payable},
            {"Classification": "LIABILITIES & EQUITY", "Account / Line Item": "Equity", "Amount (RWF)": ""},
            {"Classification": "LIABILITIES & EQUITY", "Account / Line Item": "   3200 · Retained Earnings", "Amount (RWF)": retained_earnings},
            {"Classification": "LIABILITIES & EQUITY", "Account / Line Item": "TOTAL EQUITY", "Amount (RWF)": retained_earnings},
            {"Classification": "LIABILITIES & EQUITY", "Account / Line Item": "TOTAL LIABILITIES & EQUITY", "Amount (RWF)": rra_payable + retained_earnings}
        ]
        return pd.DataFrame(sheet_rows)

    def compile_cash_flow_statement(self) -> pd.DataFrame:
        """QuickBooks Pro Format: Statement of Cash Flows (IAS 7 Direct Method)."""
        operating_inflows = 0.0
        operating_outflows = 0.0
        
        for entry in self.general_ledger:
            if entry["AccountCode"] == "1100":
                if entry["Debit"] > 0:
                    operating_inflows += entry["Debit"]
                if entry["Credit"] > 0:
                    operating_outflows += entry["Credit"]
                    
        net_cash_ops = operating_inflows - operating_outflows
        
        cf_rows = [
            {"Classification": "OPERATING ACTIVITIES", "Cash Flow Line Item": "Cash receipts from customers", "Amount (RWF)": operating_inflows},
            {"Classification": "OPERATING ACTIVITIES", "Cash Flow Line Item": "Cash paid for cost of sales & network fees", "Amount (RWF)": -operating_outflows},
            {"Classification": "OPERATING ACTIVITIES", "Cash Flow Line Item": "Net Cash Provided by Operating Activities", "Amount (RWF)": net_cash_ops},
            {"Classification": "INVESTING ACTIVITIES", "Cash Flow Line Item": "Net Cash Provided by Investing Activities", "Amount (RWF)": 0.0},
            {"Classification": "FINANCING ACTIVITIES", "Cash Flow Line Item": "Net Cash Provided by Financing Activities", "Amount (RWF)": 0.0},
            {"Classification": "SUMMARY", "Cash Flow Line Item": "Net Cash Increase/Decrease for Period", "Amount (RWF)": net_cash_ops},
            {"Classification": "SUMMARY", "Cash Flow Line Item": "Cash at Beginning of Period", "Amount (RWF)": 0.0},
            {"Classification": "SUMMARY", "Cash Flow Line Item": "CASH AT END OF PERIOD", "Amount (RWF)": net_cash_ops}
        ]
        return pd.DataFrame(cf_rows)