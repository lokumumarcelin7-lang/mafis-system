import streamlit as st
import pandas as pd
import hashlib
import re
from datetime import datetime

# --- CONFIGURATION DU SYSTÈME ---
st.set_page_config(
    page_title="MAFIS - Core Pipeline", 
    page_icon="🛡️", 
    layout="wide"
)

# Style CSS pour une interface FinTech Professionnelle
st.markdown("""
    <style>
    .system-title {font-size: 30px; font-weight: bold; color: #1E3A8A; font-family: 'Arial';}
    .compliance-badge {background-color: #E0F2FE; color: #0369A1; padding: 6px 12px; border-radius: 20px; font-size: 13px; font-weight: bold;}
    .crypto-box {background-color: #F8FAFC; border: 1px solid #E2E8F0; padding: 15px; border-radius: 8px; font-family: 'Courier New';}
    .regex-success {color: #10B981; font-weight: bold;}
    .fee-alert {color: #EF4444; font-weight: bold;}
    </style>
    """, unsafe_style_allowed=True)

class SemanticExtractor:
    """
    Moteur d'expressions régulières (Regex) calibré pour les SMS de MTN MoMo et Airtel Money à Kigali.
    """
    @staticmethod
    def calculate_p2p_transfer_fee(amount: int) -> int:
        """Applique la grille tarifaire réelle du Rwanda pour les transferts directs (sans code)"""
        if amount < 10000:
            return 100
        elif amount < 150000:
            return 250
        else:
            return 1500

    @staticmethod
    def parse_sms(sms_text: str):
        # Patterns Regex pour capturer les données clés dans les structures réelles reçues
        txid_match = re.search(r"(?:FT Id:|TxId:)\s*([A-Za-z0-9\-]+)", sms_text, re.IGNORECASE)
        amount_match = re.search(r"(?:transaction of|payment of)\s*([0-9\s,]+)\s*RWF", sms_text, re.IGNORECASE)
        balance_match = re.search(r"Balance:\s*([0-9\s,]+)\s*RWF", sms_text, re.IGNORECASE)
        fee_match = re.search(r"Fee\s*([0-9\s,]+)\s*RWF", sms_text, re.IGNORECASE)

        def clean_int(match):
            if match:
                return int(match.group(1).replace(",", "").replace(" ", ""))
            return 0

        txid = txid_match.group(1) if txid_match else "NOT_FOUND"
        amount = clean_int(amount_match)
        balance = clean_int(balance_match)
        extracted_fee = clean_int(fee_match)
        
        # Analyse sémantique intelligente de la nature du flux financier
        if "received" in sms_text.lower() or "transaction of" in sms_text.lower():
            tx_type = "Cash In (Réception - Gratuit)"
            transfer_fee = 0
        elif "payment of" in sms_text.lower() and any(x in sms_text.lower() for x in ["ltd", "inc", "code"]):
            tx_type = "Merchant Payment (Code MoMo - Gratuit)"
            transfer_fee = 0
        else:
            tx_type = "P2P Transfer (Transfert direct sans code)"
            transfer_fee = SemanticExtractor.calculate_p2p_transfer_fee(amount)

        return {
            "TxID": txid,
            "Type": tx_type,
            "Amount": amount,
            "SMS_Stated_Fee": extracted_fee,
            "Applied_Transfer_Fee": transfer_fee,
            "Balance": balance
        }

# --- INITIALISATION DE LA BASE DE DONNÉES EN MÉMOIRE ---
if "extracted_tx_logs" not in st.session_state:
    st.session_state.extracted_tx_logs = []

# --- INTERFACE GRAPHIQUE ---
st.markdown('<div class="system-title">🛡️ MAFIS Architectural Pipeline — Phase 2</div>', unsafe_style_allowed=True)
st.markdown('<span class="compliance-badge">🇷🇼 Calibrated for Rwanda Telecom Regulations & Banking Standards</span>', unsafe_style_allowed=True)
st.markdown("---")

col_sms, col_ledger = st.columns([1, 1.2])

with col_sms:
    st.subheader("Raw Text Stream Ingestion")
    
    sample_type = st.radio(
        "Load Real Kigali Transaction Logs:",
        ["Exemple 1: Réception FDI (Gratuit)", "Exemple 2: Transfert direct à Anida (Sans code)", "Custom"]
    )
    
    if sample_type == "Exemple 1: Réception FDI (Gratuit)":
        current_sms = "*164*S*Y'ello, A transaction of 500 RWF by FUTURE DYNAMIC INNOVATIONS (FDI) FUTURE DYNAMIC INLtd was completed at 2026-06-28 20:13:21. Balance:135963 RWF. Fee 0 RWF. FT Id: 28845768783.*EN#"
    elif sample_type == "Exemple 2: Transfert direct à Anida (Sans code)":
        current_sms = "TxId:28844417174*S*Your payment of 300 RWF to Anida 421426 was completed at 2026-06-28 19:23:57. Balance: 136,463 RWF. Fee 0 RWF.*EN#"
    else:
        current_sms = ""

    sms_input = st.text_area("Paste Raw Operator SMS Stream:", value=current_sms, height=120)
    
    if sms_input:
        parsed = SemanticExtractor.parse_sms(sms_input)
        
        st.markdown("**Parser Extraction Output:**")
        st.markdown(f"""
        <div class="crypto-box">
        🔑 <b>TxID Detected:</b> <span class="regex-success">{parsed['TxID']}</span><br>
        📌 <b>Inferred Category:</b> <b>{parsed['Type']}</b><br>
        💰 <b>Volume (Amount):</b> <span class="regex-success">{parsed['Amount']:,} RWF</span><br>
        💸 <b>SMS Stated Fee:</b> {parsed['SMS_Stated_Fee']} RWF<br>
        ⚠️ <b>Theoretical Transfer Cost (Sans Code):</b> <span class="fee-alert">{parsed['Applied_Transfer_Fee']} RWF</span><br>
        📈 <b>Running Balance:</b> {parsed['Balance']:,} RWF
        </div>
        """, unsafe_style_allowed=True)

        if st.button("🚀 Commit To Normalized Accounting Ledger"):
            if parsed["TxID"] == "NOT_FOUND" or parsed["Amount"] == 0:
                st.error("Normalization Error: Key attributes missing.")
            else:
                st.session_state.extracted_tx_logs.append(parsed)
                st.success("Transaction successfully structured.")

with col_ledger:
    st.subheader("Structured Alternative Accounting Ledger")
    st.markdown("This database simulates the clean structured view compiled for alternative credit scoring.")
    
    if st.session_state.extracted_tx_logs:
        st.dataframe(pd.DataFrame(st.session_state.extracted_tx_logs), use_container_width=True)
        if st.button("🗑️ Reset Ledger"):
            st.session_state.extracted_tx_logs = []