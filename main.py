# main.py
import streamlit as st
import pandas as pd
from Collection_Agent_Parser import CollectionAgentParser
from IFRS_Formalization_Engine import IFRSFormalizationEngine

st.set_page_config(
    page_title="MAFIS - Corporate Core Terminal", 
    page_icon="🛡️", 
    layout="wide"
)

# --- CSS ARCHITECTURE ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght=300;400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #F8FAFC; }
    .main-header {
        background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
        padding: 24px; border-radius: 12px; color: white; margin-bottom: 25px;
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.08);
        border-bottom: 3px solid #3B82F6;
    }
    .system-title { font-size: 26px; font-weight: 700; letter-spacing: -0.02em; margin: 0; }
    .compliance-badge {
        background-color: #2563EB; color: white; padding: 4px 12px; 
        border-radius: 6px; font-size: 11px; font-weight: 600; text-transform: uppercase;
    }
    .dashboard-card { background-color: #FFFFFF; border: 1px solid #E2E8F0; padding: 20px; border-radius: 12px; }
    .invoice-box { background-color: #0F172A; border-left: 4px solid #10B981; padding: 16px; border-radius: 8px; color: #E2E8F0; }
    .invoice-row { display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px solid #334155; font-size: 13px; }
    .invoice-row:last-child { border-bottom: none; }
    .inv-label { color: #94A3B8; }
    .inv-val { font-weight: 600; font-family: 'Courier New', monospace; }
    
    /* QuickBooks Report Header Theme */
    .qb-report-frame { text-align: center; padding: 15px 0; margin-bottom: 15px; border-bottom: 1px solid #CBD5E1; }
    .qb-company { font-size: 16px; font-weight: 700; color: #1E293B; text-transform: uppercase; }
    .qb-report-name { font-size: 18px; font-weight: 600; color: #000000; }
    .qb-meta { font-size: 12px; color: #475569; font-weight: 500; }
    </style>
    """, unsafe_allow_html=True)

if "extracted_tx_logs" not in st.session_state:
    st.session_state.extracted_tx_logs = []

if "ifrs_engine" not in st.session_state:
    st.session_state.ifrs_engine = IFRSFormalizationEngine()

engine = st.session_state.ifrs_engine
valid_logs = [x for x in st.session_state.extracted_tx_logs if x["TxID"] != "FAILED_QUAL_GATE"]
engine.compile_bookkeeping_ledger(valid_logs)

# --- TERMINAL HEADER ---
st.markdown("""
    <div class="main-header">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div class="system-title">🛡️ MAFIS Core Terminal Engine</div>
            <span class="compliance-badge">QuickBooks Standard Export Validated</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- WORKSPACE ---
col_sms, col_ledger = st.columns([1, 1.4])

with col_sms:
    st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
    st.subheader("📥 Data Stream Ingestion")
    
    sample_type = st.selectbox(
        "Select Live Network Stream Template :",
        [
            "Custom Feed / Paste Text",
            "Airtel 1: Cash In Felix (500 RWF)",
            "Airtel 2: P2P Transfer Fransine (2,000 RWF)",
            "MTN 1: FUTURE DYNAMIC (Merchant Payment)",
            "MTN 2: Honorine ABIJURU (Cash In)",
            "MTN 3: Enock TWIRINGIRIMANA (P2P Outgoing)"
        ]
    )
    
    templates = {
        "Airtel 1: Cash In Felix (500 RWF)": "151*Txn ID CI260629.0959.B00815*R You have received RWF 500 from 727937980 niyoyandinze felix.Your NEW BALANCE is RWF 500. *EN#",
        "Airtel 2: P2P Transfer Fransine (2,000 RWF)": "*165* TID MP260531.0040.B02157*S* sent to Fransine NIWEMUGENI in MTN. Amt RWF 2000. Fee RWF 0. BAL RWF 2250. *EN#",
        "MTN 1: FUTURE DYNAMIC (Merchant Payment)": "*164*S*Y'ello, A transaction of 500 RWF by FUTURE DYNAMIC INNOVATIONS (FDI) FUTURE DYNAMIC INLtd was completed at 2026-06-28 20:13:21. Balance:135963 RWF. Fee  0 RWF. FT Id: 28845768783.*EN#",
        "MTN 2: Honorine ABIJURU (Cash In)": "You have received 10000 RWF from Honorine ABIJURU (*********510) at 2026-06-26 15:15:54 . Balance:172403 RWF. FT Id: 28794607448",
        "MTN 3: Enock TWIRINGIRIMANA (P2P Outgoing)": "*165*S*3000 RWF transferred to Enock TWIRINGIRIMANA (250782993500) at 2026-06-26 19:44:12 .Fee: 100RWF.Balance: 168283RWF.*EN#"
    }
    
    current_sms = templates.get(sample_type, "")
    sms_input = st.text_area("Paste Raw Mobile Money SMS Payload:", value=current_sms, height=110)
    
    if sms_input:
        parsed = CollectionAgentParser.parse_sms(sms_input)
        is_rejected = parsed["TxID"] == "FAILED_QUAL_GATE"
        
        st.markdown(f"""
        <div class="invoice-box">
            <div class="invoice-row"><span class="inv-label">Transaction ID</span><span class="inv-val" style="color:#F59E0B;">{parsed['TxID']}</span></div>
            <div class="invoice-row"><span class="inv-label">Captured Volume</span><span class="inv-val" style="color:#10B981;">{parsed['Amount']:,} RWF</span></div>
            <div class="invoice-row"><span class="inv-label">⚖️ Calculated RRA Tax</span><span class="inv-val" style="color:#38BDF8;">{parsed['RRA_Tax']:,} RWF</span></div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🚀 Commit To QuickBooks Ledger Structure") and not is_rejected:
            st.session_state.extracted_tx_logs.append(parsed)
            st.rerun()
                
    st.markdown('</div>', unsafe_allow_html=True)

with col_ledger:
    st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
    
    tab_ledger, tab_trial, tab_income, tab_balance, tab_cashflow = st.tabs([
        "📜 General Ledger", "⚖️ Trial Balance", "📊 Profit & Loss", "🏛️ Balance Sheet", "💸 Cash Flow"
    ])
    
    with tab_ledger:
        st.subheader("Auditable Transaction Logs")
        if valid_logs:
            df = pd.DataFrame(valid_logs)
            st.dataframe(df[["TxID", "Operator", "Type", "Amount", "RRA_Tax"]], use_container_width=True, hide_index=True)
            if st.button("🗑️ Reset All Ledgers"):
                st.session_state.extracted_tx_logs = []
                engine.reset_ledger()
                st.rerun()
        else:
            st.info("Ledger clear.")

    with tab_trial:
        st.markdown('<div class="qb-report-frame"><div class="qb-company">Kigali Micro-Enterprise Simulation</div><div class="qb-report-name">Trial Balance</div><div class="qb-meta">As of June 30, 2026 · Accrual Basis</div></div>', unsafe_allow_html=True)
        if valid_logs:
            df_trial, dr_total, cr_total = engine.compile_trial_balance()
            st.dataframe(
                df_trial, use_container_width=True, hide_index=True,
                column_config={
                    "Debit (RWF)": st.column_config.NumberColumn(format="%,.2f"),
                    "Credit (RWF)": st.column_config.NumberColumn(format="%,.2f")
                }
            )
            st.markdown(f"**Total Debits:** `{dr_total:,.2f} RWF` | **Total Credits:** `{cr_total:,.2f} RWF`")
        else:
            st.info("No data.")

    with tab_income:
        st.markdown('<div class="qb-report-frame"><div class="qb-company">Kigali Micro-Enterprise Simulation</div><div class="qb-report-name">Profit and Loss</div><div class="qb-meta">January through June 2026 · Accrual Basis</div></div>', unsafe_allow_html=True)
        if valid_logs:
            df_income, _ = engine.compile_income_statement()
            st.dataframe(
                df_income, use_container_width=True, hide_index=True,
                column_config={"Amount (RWF)": st.column_config.NumberColumn(format="%,.2f")}
            )
        else:
            st.info("No data.")

    with tab_balance:
        st.markdown('<div class="qb-report-frame"><div class="qb-company">Kigali Micro-Enterprise Simulation</div><div class="qb-report-name">Balance Sheet</div><div class="qb-meta">As of June 30, 2026</div></div>', unsafe_allow_html=True)
        if valid_logs:
            _, net_income = engine.compile_income_statement()
            df_bs = engine.compile_balance_sheet(net_income)
            st.dataframe(
                df_bs[["Account / Line Item", "Amount (RWF)"]], use_container_width=True, hide_index=True,
                column_config={"Amount (RWF)": st.column_config.NumberColumn(format="%,.2f")}
            )
        else:
            st.info("No data.")

    with tab_cashflow:
        st.markdown('<div class="qb-report-frame"><div class="qb-company">Kigali Micro-Enterprise Simulation</div><div class="qb-report-name">Statement of Cash Flows</div><div class="qb-meta">January through June 2026</div></div>', unsafe_allow_html=True)
        if valid_logs:
            df_cf = engine.compile_cash_flow_statement()
            st.dataframe(
                df_cf[["Cash Flow Line Item", "Amount (RWF)"]], use_container_width=True, hide_index=True,
                column_config={"Amount (RWF)": st.column_config.NumberColumn(format="%,.2f")}
            )
        else:
            st.info("No data.")

    st.markdown('</div>', unsafe_allow_html=True)