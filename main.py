import streamlit as st
import pandas as pd
import re

# --- CONFIGURATION DU SYSTÈME ---
st.set_page_config(
    page_title="MAFIS - Core Pipeline", 
    page_icon="🛡️", 
    layout="wide"
)

# Style CSS FinTech Professionnel
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
        if is_airtel:
            return 0  # Politique de gratuité Airtel Money Rwanda
        if amount < 10000:
            return 100
        elif amount < 150000:
            return 250
        else:
            return 1500

    @staticmethod
    def parse_sms(sms_text: str):
        # Normalisation absolue : remplace les espaces insécables (\xa0) et espaces multiples par un espace standard
        cleaned_sms = re.sub(r'\s+', ' ', sms_text).strip()
        sms_lower = cleaned_sms.lower()
        
        # Détection de l'écosystème réseau
        is_airtel = any(x in sms_lower for x in ["txn id", "tid", "new balance", "bal rwf"])

        # Fonction de nettoyage numérique ultra-robuste contre le crash ValueError
        def safe_int_extract(regex_pattern, text):
            match = re.search(regex_pattern, text, re.IGNORECASE)
            if match and match.group(1):
                # Supprime absolument tout ce qui n'est pas un chiffre (lettres, espaces, virgules)
                digits = re.sub(r'\D', '', match.group(1))
                return int(digits) if digits else 0
            return 0

        # 1. Extraction du Identifiant Unique (TxID / TID)
        txid_match = re.search(r"(?:FT\s*Id|TxId|Txn\s*ID|TID)[:\s]+([A-Za-z0-9\.\-]+)", cleaned_sms, re.IGNORECASE)
        txid = txid_match.group(1) if txid_match else "NOT_FOUND"
        
        # 2. Extraction du Montant (Amount) avec gestion des structures directes et inversées
        amount = safe_int_extract(r"(?:received|transaction of|payment of|amt)[:\s]+(?:rwf)?\s*([0-9\s, ]+)", cleaned_sms)
        if amount == 0:
            # Fallback pour le format Airtel/MTN inversé: "3000 RWF transferred"
            amount = safe_int_extract(r"([0-9\s, ]+)\s*rwf\s+transferred", cleaned_sms)

        # 3. Extraction du Solde Courant (Running Balance)
        balance = safe_int_extract(r"(?:balance is|balance:|bal)[:\s]+(?:rwf)?\s*([0-9\s, ]+)", cleaned_sms)

        # 4. Extraction des Frais Déclarés (Stated Fee)
        extracted_fee = safe_int_extract(r"fee[:\s]+(?:rwf)?\s*([0-9\s, ]+)", cleaned_sms)
        
        # 5. Extraction de la Contrepartie (Counterparty) - Pivot pour le Credit Scoring
        counterparty = "Unknown Ecosystem"
        cp_match = re.search(r"(?:from|to|by|sent to)\s+([A-Za-z\s]+)(?:\(|at|was|in\s|via|\d|$)", cleaned_sms, re.IGNORECASE)
        if cp_match:
            counterparty = cp_match.group(1).replace("Ltd", "").strip()

        # 6. Catégorisation Sémantique
        if "received" in sms_lower:
            tx_type = "Cash In (Réception)"
            transfer_fee = 0
        elif "payment of" in sms_lower or "by" in sms_lower:
            tx_type = "Merchant Payment (Achat)"
            transfer_fee = 0
        else:
            tx_type = "P2P Transfer (Envoi)"
            transfer_fee = SemanticExtractor.calculate_transfer_fee(amount, is_airtel)

        return {
            "TxID": txid,
            "Operator": "Airtel Money" if is_airtel else "MTN MoMo",
            "Type": tx_type,
            "Counterparty": counterparty if counterparty else "Internal Network",
            "Amount": amount,
            "SMS_Stated_Fee": extracted_fee,
            "Applied_Transfer_Fee": transfer_fee,
            "Balance": balance
        }

# --- INITIALISATION DE LA SESSION ---
if "extracted_tx_logs" not in st.session_state:
    st.session_state.extracted_tx_logs = []

# --- INTERFACE ---
st.markdown('<div class="system-title">🛡️ MAFIS Architectural Pipeline — Phase 2 Pro</div>', unsafe_allow_html=True)
st.markdown('<span class="compliance-badge">🇷🇼 Production Grade - Anti-Crash Pattern Matching & Multi-Operator Calibration</span>', unsafe_allow_html=True)
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
            "MTN 3: Enock TWIRINGIRIMANA (Transfert Sortant)",
            "MTN 4: BK Techouse (UrubutoPay)"
        ]
    )
    
    templates = {
        "Airtel 1: Réception felix (500 RWF)": "151*Txn ID CI260629.0959.B00815*R You have received RWF 500 from 727937980 niyoyandinze felix.Your NEW BALANCE is RWF 500. *EN#",
        "Airtel 2: Envoi Fransine (2 000 RWF)": "*165* TID MP260531.0040.B02157*S* sent to Fransine NIWEMUGENI in MTN. Amt RWF 2000. Fee RWF 0. BAL RWF 2250. *EN#",
        "MTN 1: FUTURE DYNAMIC (Marchand)": "*164*S*Y'ello, A transaction of 500 RWF by FUTURE DYNAMIC INNOVATIONS (FDI) FUTURE DYNAMIC INLtd was completed at 2026-06-28 20:13:21. Balance:135963 RWF. Fee  0 RWF. FT Id: 28845768783.*EN#",
        "MTN 2: Honorine ABIJURU (Réception)": "You have received 10000 RWF from Honorine ABIJURU (*********510) at 2026-06-26 15:15:54 . Balance:172403 RWF. FT Id: 28794607448",
        "MTN 3: Enock TWIRINGIRIMANA (Transfert Sortant)": "*165*S*3000 RWF transferred to Enock TWIRINGIRIMANA (250782993500) at 2026-06-26 19:44:12 .Fee: 100RWF.Balance: 168283RWF.*EN#",
        "MTN 4: BK Techouse (UrubutoPay)": "*164*S*Y'ello, A transaction of 150000 RWF by BK Techouse   via UrubutoPay was completed at 2026-06-08 09:15:18. Balance:250473 RWF. Fee  600 RWF. FT Id: 28411778641.*EN#"
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
        👤 <b>Counterparty Entity:</b> <b>{parsed['Counterparty']}</b><br>
        📌 <b>Inferred Category:</b> <b>{parsed['Type']}</b><br>
        💰 <b>Volume (Amount):</b> <span class="regex-success">{parsed['Amount']:,} RWF</span><br>
        💸 <b>SMS Stated Fee:</b> {parsed['SMS_Stated_Fee']:,} RWF<br>
        ⚠️ <b>Theoretical Cost (P2P):</b> <span class="fee-alert">{parsed['Applied_Transfer_Fee']:,} RWF</span><br>
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