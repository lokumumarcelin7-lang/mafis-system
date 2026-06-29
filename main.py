import streamlit as st
import pandas as pd
import re

# --- CONFIGURATION DU SYSTÈME ---
st.set_page_config(
    page_title="MAFIS - Core Pipeline", 
    page_icon="🛡️", 
    layout="wide"
)

# Style CSS FinTech
st.markdown("""
    <style>
    .system-title {font-size: 30px; font-weight: bold; color: #1E3A8A; font-family: 'Arial';}
    .compliance-badge {background-color: #E0F2FE; color: #0369A1; padding: 6px 12px; border-radius: 20px; font-size: 13px; font-weight: bold;}
    .crypto-box {background-color: #F8FAFC; border: 1px solid #E2E8F0; padding: 15px; border-radius: 8px; font-family: 'Courier New';}
    .regex-success {color: #10B981; font-weight: bold;}
    .fee-alert {color: #EF4444; font-weight: bold;}
    </style>
    """, unsafe_allow_html=True)

class SemanticExtractor:
    
    @staticmethod
    def calculate_transfer_fee(amount: int, is_airtel: bool) -> int:
        # Règle Airtel : L'envoi est gratuit
        if is_airtel:
            return 0
        # Grille tarifaire standard MTN MoMo (P2P direct sans code)
        if amount < 10000:
            return 100
        elif amount < 150000:
            return 250
        else:
            return 1500

    @staticmethod
    def parse_sms(sms_text: str):
        sms_lower = sms_text.lower()
        
        # 1. Détection de l'opérateur (MTN vs Airtel)
        # Airtel utilise souvent des patterns comme "Txn ID", "TID", "NEW BALANCE" ou la mention directe d'Airtel
        is_airtel = any(x in sms_lower for x in ["txn id", "tid", "new balance", "bal rwf"])

        # 2. Extraction du TxID (Gère MTN: FT Id/TxId et Airtel: Txn ID/TID)
        txid_match = re.search(r"(?:FT\s*Id:|TxId:|Txn\s*ID|TID)\s*([A-Za-z0-9\.\-]+)", sms_text, re.IGNORECASE)
        txid = txid_match.group(1) if txid_match else "NOT_FOUND"
        
        # 3. Extraction dynamique du montant (Gère MTN et le format Airtel "RWF 500" ou "Amt RWF 2000")
        amount = 0
        amount_match = re.search(r"(?:received|transaction of|payment of|amt)\s*(?:rwf)?\s*([0-9\s,]+)\s*(?:rwf)?", sms_text, re.IGNORECASE)
        if amount_match and amount_match.group(1).strip():
            amount = int(amount_match.group(1).replace(",", "").replace(" ", ""))
        else:
            # Pattern secondaire pour le format MTN inversé "3000 RWF transferred"
            reverse_match = re.search(r"(?:S\*|:\s*|^)\s*([0-9\s,]+)\s*RWF\s*transferred", sms_text, re.IGNORECASE)
            if reverse_match:
                amount = int(reverse_match.group(1).replace(",", "").replace(" ", ""))

        # 4. Extraction du Running Balance (Gère MTN: Balance:X RWF et Airtel: NEW BALANCE is RWF X / BAL RWF X)
        balance_match = re.search(r"(?:balance\s*is|balance:|bal)\s*(?:rwf)?\s*([0-9\s,]+)\s*(?:rwf)?", sms_text, re.IGNORECASE)
        balance = int(balance_match.group(1).replace(",", "").replace(" ", "")) if balance_match else 0

        # 5. Extraction des frais déclarés par l'opérateur
        fee_match = re.search(r"fee:?\s*(?:rwf)?\s*([0-9\s,]+)\s*(?:rwf)?", sms_text, re.IGNORECASE)
        extracted_fee = int(fee_match.group(1).replace(",", "").replace(" ", "")) if fee_match else 0
        
        # 6. Qualification sémantique du flux financier
        if "received" in sms_lower:
            tx_type = f"Cash In ({'Airtel' if is_airtel else 'MTN'} Réception - Gratuit)"
            transfer_fee = 0
        elif "payment of" in sms_lower or "by" in sms_lower or "mp" in sms_lower:
            tx_type = f"Merchant Payment ({'Airtel' if is_airtel else 'MoMo'} - Gratuit)"
            transfer_fee = 0
        else:
            tx_type = f"P2P Transfer ({'Airtel' if is_airtel else 'MTN'} Sortant)"
            transfer_fee = SemanticExtractor.calculate_transfer_fee(amount, is_airtel)

        return {
            "TxID": txid,
            "Operator": "Airtel Money" if is_airtel else "MTN MoMo",
            "Type": tx_type,
            "Amount": amount,
            "SMS_Stated_Fee": extracted_fee,
            "Applied_Transfer_Fee": transfer_fee,
            "Balance": balance
        }

# --- INITIALISATION DE LA SESSION ---
if "extracted_tx_logs" not in st.session_state:
    st.session_state.extracted_tx_logs = []

# --- INTERFACE ---
st.markdown('<div class="system-title">🛡️ MAFIS Architectural Pipeline — Phase 2</div>', unsafe_allow_html=True)
st.markdown('<span class="compliance-badge">🇷🇼 Calibrated for Rwanda Telecom Regulations & Banking Standards</span>', unsafe_allow_html=True)
st.markdown("---")

col_sms, col_ledger = st.columns([1, 1.2])

with col_sms:
    st.subheader("Raw Text Stream Ingestion")
    
    sample_type = st.selectbox(
        "Select Live Kigali Feed Template:",
        [
            "Custom / Paste Text",
            "Airtel 1: Réception felix (500 RWF)",
            "Airtel 2: Envoi Fransine (2 000 RWF)",
            "MTN 1: FUTURE DYNAMIC (Marchand)",
            "MTN 2: Honorine ABIJURU (Réception)",
            "MTN 3: Enock TWIRINGIRIMANA (Transfert Sortant)"
        ]
    )
    
    templates = {
        "Airtel 1: Réception felix (500 RWF)": "151*Txn ID CI260629.0959.B00815*R You have received RWF 500 from 727937980 niyoyandinze felix.Your NEW BALANCE is RWF 500. *EN#",
        "Airtel 2: Envoi Fransine (2 000 RWF)": "*165* TID MP260531.0040.B02157*S* sent to Fransine NIWEMUGENI in MTN. Amt RWF 2000. Fee RWF 0. BAL RWF 2250. *EN#",
        "MTN 1: FUTURE DYNAMIC (Marchand)": "*164*S*Y'ello, A transaction of 500 RWF by FUTURE DYNAMIC INNOVATIONS (FDI) FUTURE DYNAMIC INLtd was completed at 2026-06-28 20:13:21. Balance:135963 RWF. Fee  0 RWF. FT Id: 28845768783.*EN#",
        "MTN 2: Honorine ABIJURU (Réception)": "You have received 10000 RWF from Honorine ABIJURU (*********510) at 2026-06-26 15:15:54 . Balance:172403 RWF. FT Id: 28794607448",
        "MTN 3: Enock TWIRINGIRIMANA (Transfert Sortant)": "*165*S*3000 RWF transferred to Enock TWIRINGIRIMANA (250782993500) at 2026-06-26 19:44:12 .Fee: 100RWF.Balance: 168283RWF.*EN#"
    }
    
    current_sms = templates.get(sample_type, "")
    sms_input = st.text_area("Paste Raw Operator SMS Stream:", value=current_sms, height=130)
    
    if sms_input:
        parsed = SemanticExtractor.parse_sms(sms_input)
        
        st.markdown("**Parser Extraction Output:**")
        st.markdown(f"""
        <div class="crypto-box">
        🔑 <b>TxID Detected:</b> <span class="regex-success">{parsed['TxID']}</span><br>
        📡 <b>Network Operator:</b> {parsed['Operator']}<br>
        📌 <b>Inferred Category:</b> <b>{parsed['Type']}</b><br>
        💰 <b>Volume (Amount):</b> <span class="regex-success">{parsed['Amount']:,} RWF</span><br>
        💸 <b>SMS Stated Fee:</b> {parsed['SMS_Stated_Fee']:,} RWF<br>
        ⚠️ <b>Theoretical Cost (Sans Code):</b> <span class="fee-alert">{parsed['Applied_Transfer_Fee']:,} RWF</span><br>
        📈 <b>Running Balance:</b> {parsed['Balance']:,} RWF
        </div>
        """, unsafe_allow_html=True)

        if st.button("🚀 Commit To Normalized Accounting Ledger"):
            if parsed["Amount"] == 0:
                st.error("Normalization Error: Financial amount attribute missing.")
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
            st.rerun()
    else:
        st.info("Awaiting live stream ingestion.")