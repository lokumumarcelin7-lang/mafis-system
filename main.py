# main.py
import streamlit as st
import pandas as pd
from Collection_Agent_Parser import CollectionAgentParser

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="MAFIS - Core Terminal", 
    page_icon="🛡️", 
    layout="wide"
)

# --- FINTECH PREMIUM DESIGN SYSTEM (CSS INJECTION) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght=300;400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #F8FAFC; }
    .main-header {
        background: linear-gradient(135deg, #0F172A 0%, #1E3A8A 100%);
        padding: 30px; border-radius: 16px; color: white; margin-bottom: 30px;
        box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.1);
    }
    .system-title { font-size: 28px; font-weight: 700; letter-spacing: -0.03em; margin: 0 0 6px 0; }
    .compliance-badge {
        background-color: rgba(255, 255, 255, 0.12); color: #38BDF8; padding: 6px 14px; 
        border-radius: 30px; font-size: 12px; font-weight: 600; border: 1px solid rgba(255, 255, 255, 0.08);
        text-transform: uppercase; letter-spacing: 0.05em;
    }
    .dashboard-card {
        background-color: #FFFFFF; border: 1px solid #E2E8F0; padding: 24px;
        border-radius: 16px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); margin-bottom: 20px;
    }
    .invoice-box { background-color: #0F172A; border-left: 4px solid #3B82F6; padding: 20px; border-radius: 12px; margin-top: 20px; color: #E2E8F0; }
    .invoice-row { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #334155; font-size: 14px; }
    .invoice-row:last-child { border-bottom: none; }
    .inv-label { color: #94A3B8; font-weight: 500; }
    .inv-val { font-weight: 600; font-family: 'Courier New', monospace; }
    .status-badge { background-color: #1E293B; color: #38BDF8; padding: 2px 8px; border-radius: 4px; font-size: 12px; }
    .status-error-badge { background-color: #7F1D1D; color: #FCA5A5; padding: 2px 8px; border-radius: 4px; font-size: 12px; }
    
    div.stButton > button {
        background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%) !important;
        color: white !important; border-radius: 10px !important; padding: 12px 24px !important;
        font-weight: 600 !important; border: none !important; box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2) !important;
        width: 100%; transition: all 0.2s ease-in-out;
    }
    div.stButton > button:hover { transform: translateY(-1px); box-shadow: 0 6px 20px rgba(37, 99, 235, 0.3) !important; }
    </style>
    """, unsafe_allow_html=True)

if "extracted_tx_logs" not in st.session_state:
    st.session_state.extracted_tx_logs = []

# --- TERMINAL HEADER ---
st.markdown("""
    <div class="main-header">
        <div class="system-title">🛡️ MAFIS Architectural Terminal — Version 2.5 (Production)</div>
        <span class="compliance-badge">🇷🇼 RRA Regulation Layer & Robustness Quality Gate Active</span>
    </div>
    """, unsafe_allow_html=True)

# --- CALCULATE AGGREGATED METRICS ---
logs = st.session_state.extracted_tx_logs
total_tx = len([x for x in logs if x["TxID"] != "FAILED_QUAL_GATE"])
total_volume = sum(item['Amount'] for item in logs if item["TxID"] != "FAILED_QUAL_GATE")
total_rra_tax = sum(item['RRA_Tax'] for item in logs if item["TxID"] != "FAILED_QUAL_GATE")

kpi1, kpi2, kpi3 = st.columns(3)
with kpi1:
    st.metric(label="Total Validated Ingested Volume", value=f"{total_volume:,} RWF", delta=f"{total_tx} Blocks Committed")
with kpi2:
    st.metric(label="Total RRA Taxes Compiled", value=f"{total_rra_tax:,} RWF", delta="Consolidated Ledger")
with kpi3:
    st.metric(label="Quality Gate Status", value="Active & Robust", delta="Rejects Malicious Injections")

st.markdown("<br>", unsafe_allow_html=True)

# --- MAIN WORKSPACE WORKFLOW ---
col_sms, col_ledger = st.columns([1, 1.3])

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
            "MTN 3: Enock TWIRINGIRIMANA (P2P Outgoing)",
            "🚨 FRAUD TEST: Fake payload or invalid prefix architecture"
        ]
    )
    
    templates = {
        "Airtel 1: Cash In Felix (500 RWF)": "151*Txn ID CI260629.0959.B00815*R You have received RWF 500 from 727937980 niyoyandinze felix.Your NEW BALANCE is RWF 500. *EN#",
        "Airtel 2: P2P Transfer Fransine (2,000 RWF)": "*165* TID MP260531.0040.B02157*S* sent to Fransine NIWEMUGENI in MTN. Amt RWF 2000. Fee RWF 0. BAL RWF 2250. *EN#",
        "MTN 1: FUTURE DYNAMIC (Merchant Payment)": "*164*S*Y'ello, A transaction of 500 RWF by FUTURE DYNAMIC INNOVATIONS (FDI) FUTURE DYNAMIC INLtd was completed at 2026-06-28 20:13:21. Balance:135963 RWF. Fee  0 RWF. FT Id: 28845768783.*EN#",
        "MTN 2: Honorine ABIJURU (Cash In)": "You have received 10000 RWF from Honorine ABIJURU (*********510) at 2026-06-26 15:15:54 . Balance:172403 RWF. FT Id: 28794607448",
        "MTN 3: Enock TWIRINGIRIMANA (P2P Outgoing)": "*165*S*3000 RWF transferred to Enock TWIRINGIRIMANA (250782993500) at 2026-06-26 19:44:12 .Fee: 100RWF.Balance: 168283RWF.*EN#",
        "🚨 FRAUD TEST: Fake payload or invalid prefix architecture": "ATTENTION: You have received 50000 RWF from Bank of Kigali. Balance 54000 RWF. No transaction tracking ID available."
    }
    
    current_sms = templates.get(sample_type, "")
    sms_input = st.text_area("Paste Raw Mobile Money SMS Payload:", value=current_sms, height=130)
    
    if sms_input:
        # Link autonomous parser agent decoupled for Phase 2
        parsed = CollectionAgentParser.parse_sms(sms_input)
        
        is_rejected = parsed["TxID"] == "FAILED_QUAL_GATE"
        badge_class = "status-error-badge" if is_rejected else "status-badge"
        
        st.markdown(f"""
        <div class="invoice-box" style="border-left-color: {'#EF4444' if is_rejected else '#3B82F6'};">
            <div style="font-weight:700; color:#F8FAFC; margin-bottom:12px; font-size:13px; text-transform:uppercase; letter-spacing:0.05em;">⚡ AUTONOMOUS AGENT PARSER OUTPUT</div>
            <div class="invoice-row"><span class="inv-label">Transaction ID</span><span class="inv-val" style="color:{'#EF4444' if is_rejected else '#F59E0B'};">{parsed['TxID']}</span></div>
            <div class="invoice-row"><span class="inv-label">Network Carrier</span><span class="{badge_class}">{parsed['Operator']}</span></div>
            <div class="invoice-row"><span class="inv-label">Inferred Category</span><span class="inv-val">{parsed['Type']}</span></div>
            <div class="invoice-row"><span class="inv-label">Counterparty Entity</span><span class="inv-val">{parsed['Counterparty']}</span></div>
            <div class="invoice-row"><span class="inv-label">Captured Volume</span><span class="inv-val" style="color:#10B981;">{parsed['Amount']:,} RWF</span></div>
            <div class="invoice-row"><span class="inv-label">⚖️ Calculated RRA Tax</span><span class="inv-val" style="color:#38BDF8; font-weight:700;">{parsed['RRA_Tax']:,} RWF</span></div>
            <div class="invoice-row"><span class="inv-label">Gate Security Status</span><span class="inv-val" style="color:{'#FCA5A5' if is_rejected else '#34D399'};">{parsed['Status']}</span></div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🚀 Commit To Normalized Accounting Ledger") and not is_rejected:
            if parsed["Amount"] == 0:
                st.error("Normalization Error: Target financial attributes unreached.")
            else:
                st.session_state.extracted_tx_logs.append(parsed)
                st.rerun()
                
    st.markdown('</div>', unsafe_allow_html=True)

with col_ledger:
    st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
    st.subheader("📊 Structured Alternative Accounting Ledger")
    st.markdown("This ledger simulates the clean, verified data architecture used for alternative risk analysis and credit scoring calculation kernels.")
    
    # Filter validation history out of database view
    valid_logs = [x for x in st.session_state.extracted_tx_logs if x["TxID"] != "FAILED_QUAL_GATE"]
    
    if valid_logs:
        df = pd.DataFrame(valid_logs)
        df_display = df[["TxID", "Operator", "Type", "Counterparty", "Amount", "SMS_Stated_Fee", "Applied_Transfer_Fee", "RRA_Tax", "Balance"]]
        st.dataframe(df_display, use_container_width=True, hide_index=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🗑️ Reset Internal Ledger"):
            st.session_state.extracted_tx_logs = []
            st.rerun()
    else:
        st.info("No records committed. Ingest a valid stream on the left pane to populate the accounting ledger framework.")
    st.markdown('</div>', unsafe_allow_html=True)