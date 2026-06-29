import streamlit as st
import pandas as pd
import re

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="MAFIS - Core Terminal", 
    page_icon="🛡️", 
    layout="wide"
)

# --- DESIGN SYSTEM PRESTIGE (CSS INJECTÉ) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Application globale de la police Inter */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #F8FAFC;
    }
    
    /* Bannière de Contrôle Principale */
    .main-header {
        background: linear-gradient(135deg, #0F172A 0%, #1E3A8A 100%);
        padding: 30px;
        border-radius: 16px;
        color: white;
        margin-bottom: 30px;
        box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.1);
    }
    .system-title {
        font-size: 28px; 
        font-weight: 700; 
        letter-spacing: -0.03em;
        margin: 0 0 6px 0;
    }
    .compliance-badge {
        background-color: rgba(255, 255, 255, 0.12); 
        color: #38BDF8; 
        padding: 6px 14px; 
        border-radius: 30px; 
        font-size: 12px; 
        font-weight: 600;
        border: 1px solid rgba(255, 255, 255, 0.08);
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    /* Conteneurs de blocs (Cards) */
    .dashboard-card {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        padding: 24px;
        border-radius: 16px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        margin-bottom: 20px;
    }
    
    /* Terminal de Facturation / Reçu Décrypté */
    .invoice-box {
        background-color: #0F172A; 
        border-left: 4px solid #3B82F6; 
        padding: 20px; 
        border-radius: 12px;
        margin-top: 20px;
        color: #E2E8F0;
    }
    .invoice-row {
        display: flex;
        justify-content: space-between;
        padding: 8px 0;
        border-bottom: 1px solid #334155;
        font-size: 14px;
    }
    .invoice-row:last-child {
        border-bottom: none;
    }
    .inv-label { color: #94A3B8; font-weight: 500; }
    .inv-val { font-weight: 600; font-family: 'Courier New', monospace; }
    
    .status-badge {
        background-color: #1E293B;
        color: #38BDF8;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 12px;
    }
    
    /* Optimisation des Boutons Streamlit */
    div.stButton > button {
        background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%) !important;
        color: white !important;
        border-radius: 10px !important;
        padding: 12px 24px !important;
        font-weight: 600 !important;
        border: none !important;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2) !important;
        transition: all 0.2s ease-in-out;
        width: 100%;
    }
    div.stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 20px rgba(37, 99, 235, 0.3) !important;
    }
    </style>
    """, unsafe_allow_html=True)

class SemanticExtractor:
    
    @staticmethod
    def calculate_transfer_fee(amount: int, is_airtel: bool) -> int:
        if is_airtel:
            return 0  # Airtel Money Rwanda Promotion (Gratuit)
        if amount < 10000:
            return 100
        elif amount < 150000:
            return 250
        else:
            return 1500

    @staticmethod
    def parse_sms(sms_text: str):
        cleaned_sms = re.sub(r'\s+', ' ', sms_text).strip()
        sms_lower = cleaned_sms.lower()
        
        is_airtel = any(x in sms_lower for x in ["txn id", "tid", "new balance", "bal rwf"])

        def safe_int_extract(regex_pattern, text):
            match = re.search(regex_pattern, text, re.IGNORECASE)
            if match and match.group(1):
                digits = re.sub(r'\D', '', match.group(1))
                return int(digits) if digits else 0
            return 0

        txid_match = re.search(r"(?:FT\s*Id|TxId|Txn\s*ID|TID)[:\s]+([A-Za-z0-9\.\-]+)", cleaned_sms, re.IGNORECASE)
        txid = txid_match.group(1) if txid_match else "NOT_FOUND"
        
        amount = safe_int_extract(r"(?:received|transaction of|payment of|amt)[:\s]+(?:rwf)?\s*([0-9\s, ]+)", cleaned_sms)
        if amount == 0:
            amount = safe_int_extract(r"([0-9\s, ]+)\s*rwf\s+transferred", cleaned_sms)

        balance = safe_int_extract(r"(?:balance is|balance:|bal)[:\s]+(?:rwf)?\s*([0-9\s, ]+)", cleaned_sms)
        extracted_fee = safe_int_extract(r"fee[:\s]+(?:rwf)?\s*([0-9\s, ]+)", cleaned_sms)
        
        counterparty = "Ecosystem Internal"
        cp_match = re.search(r"(?:from|to|by|sent to)\s+([A-Za-z\s\.0-9]+)(?:\(|at|was|in\s|via|\d|$)", cleaned_sms, re.IGNORECASE)
        if cp_match:
            counterparty = cp_match.group(1).replace("Ltd", "").strip()

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
            "Counterparty": counterparty if counterparty else "Ecosystem Internal",
            "Amount": amount,
            "SMS_Stated_Fee": extracted_fee,
            "Applied_Transfer_Fee": transfer_fee,
            "Balance": balance
        }

# --- TRACKING DE LA BASE DE DONNÉES EN MÉMOIRE ---
if "extracted_tx_logs" not in st.session_state:
    st.session_state.extracted_tx_logs = []

# --- EN-TÊTE IMMERSIF (CONSOL FINTECH) ---
st.markdown("""
    <div class="main-header">
        <div class="system-title">🛡️ MAFIS Architectural Terminal — Version 2.4</div>
        <span class="compliance-badge">🇷🇼 Production Engine — Kigali Mobile Networks Calibrated</span>
    </div>
    """, unsafe_allow_html=True)

# --- BLOC KPI ANALYTICS DYNAMIQUE ---
# Calcule les données agrégées en arrière-plan pour rendre l'interface ultra-efficace
logs = st.session_state.extracted_tx_logs
total_tx = len(logs)
total_volume = sum(item['Amount'] for item in logs)
last_balance = logs[-1]['Balance'] if logs else 0

kpi1, kpi2, kpi3 = st.columns(3)
with kpi1:
    st.metric(label="Total Ingested Volume", value=f"{total_volume:,} RWF", delta=f"{total_tx} Extracted Blocks")
with kpi2:
    st.metric(label="Simulated Account Balance", value=f"{last_balance:,} RWF")
with kpi3:
    st.metric(label="Ecosystem Infrastructure", value="Multi-Agent Core", delta="Active Gateway", delta_color="normal")

st.markdown("<br>", unsafe_allow_html=True)

# --- ZONE DE TRAVAIL PRINCIPALE ---
col_sms, col_ledger = st.columns([1, 1.3])

with col_sms:
    st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
    st.subheader("📥 Data Stream Ingestion")
    
    sample_type = st.selectbox(
        "Select Live Network Stream Template :",
        [
            "Custom Feed / Paste Text",
            "Airtel 1: Réception Felix (500 RWF)",
            "Airtel 2: Envoi Fransine (2 000 RWF)",
            "MTN 1: FUTURE DYNAMIC (Marchand)",
            "MTN 2: Honorine ABIJURU (Réception)",
            "MTN 3: Enock TWIRINGIRIMANA (Transfert Sortant)",
            "MTN 4: BK Techouse (UrubutoPay)"
        ]
    )
    
    templates = {
        "Airtel 1: Réception Felix (500 RWF)": "151*Txn ID CI260629.0959.B00815*R You have received RWF 500 from 727937980 niyoyandinze felix.Your NEW BALANCE is RWF 500. *EN#",
        "Airtel 2: Envoi Fransine (2 000 RWF)": "*165* TID MP260531.0040.B02157*S* sent to Fransine NIWEMUGENI in MTN. Amt RWF 2000. Fee RWF 0. BAL RWF 2250. *EN#",
        "MTN 1: FUTURE DYNAMIC (Marchand)": "*164*S*Y'ello, A transaction of 500 RWF by FUTURE DYNAMIC INNOVATIONS (FDI) FUTURE DYNAMIC INLtd was completed at 2026-06-28 20:13:21. Balance:135963 RWF. Fee  0 RWF. FT Id: 28845768783.*EN#",
        "MTN 2: Honorine ABIJURU (Réception)": "You have received 10000 RWF from Honorine ABIJURU (*********510) at 2026-06-26 15:15:54 . Balance:172403 RWF. FT Id: 28794607448",
        "MTN 3: Enock TWIRINGIRIMANA (Transfert Sortant)": "*165*S*3000 RWF transferred to Enock TWIRINGIRIMANA (250782993500) at 2026-06-26 19:44:12 .Fee: 100RWF.Balance: 168283RWF.*EN#",
        "MTN 4: BK Techouse (UrubutoPay)": "*164*S*Y'ello, A transaction of 150000 RWF by BK Techouse   via UrubutoPay was completed at 2026-06-08 09:15:18. Balance:250473 RWF. Fee  600 RWF. FT Id: 28411778641.*EN#"
    }
    
    current_sms = templates.get(sample_type, "")
    sms_input = st.text_area("Paste Raw Mobile Money SMS Payload:", value=current_sms, height=130)
    
    if sms_input:
        parsed = SemanticExtractor.parse_sms(sms_input)
        
        # Affichage sous forme de reçu de transaction ultra-élégant
        st.markdown(f"""
        <div class="invoice-box">
            <div style="font-weight:700; color:#F8FAFC; margin-bottom:12px; font-size:13px; text-transform:uppercase; letter-spacing:0.05em;">⚡ TELECOM EXTRACTOR OUTPUT</div>
            <div class="invoice-row"><span class="inv-label">Transaction ID</span><span class="inv-val" style="color:#F59E0B;">{parsed['TxID']}</span></div>
            <div class="invoice-row"><span class="inv-label">Network Carrier</span><span class="status-badge">{parsed['Operator']}</span></div>
            <div class="invoice-row"><span class="inv-label">Inferred Category</span><span class="inv-val">{parsed['Type']}</span></div>
            <div class="invoice-row"><span class="inv-label">Counterparty Entity</span><span class="inv-val" style="color:#38BDF8;">{parsed['Counterparty']}</span></div>
            <div class="invoice-row"><span class="inv-label">Captured Volume</span><span class="inv-val regex-success">{parsed['Amount']:,} RWF</span></div>
            <div class="invoice-row"><span class="inv-label">Operator Stated Fee</span><span class="inv-val">{parsed['SMS_Stated_Fee']:,} RWF</span></div>
            <div class="invoice-row"><span class="inv-label">Shadow Transfer Cost</span><span class="inv-val fee-alert">{parsed['Applied_Transfer_Fee']:,} RWF</span></div>
            <div class="invoice-row"><span class="inv-label">Post-Tx Balance</span><span class="inv-val" style="color:#A7F3D0;">{parsed['Balance']:,} RWF</span></div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🚀 Commit To Normalized Accounting Ledger"):
            if parsed["Amount"] == 0:
                st.error("Normalization Error: Target attributes unreached.")
            else:
                st.session_state.extracted_tx_logs.append(parsed)
                st.rerun()
                
    st.markdown('</div>', unsafe_allow_html=True)

with col_ledger:
    st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
    st.subheader("📊 Structured Alternative Accounting Ledger")
    st.markdown("Ce registre simule la base de données propre compilée pour l'analyse alternative du risque de crédit.")
    
    if st.session_state.extracted_tx_logs:
        df = pd.DataFrame(st.session_state.extracted_tx_logs)
        # Tri des colonnes pour un rendu parfait dans le tableau
        df_display = df[["TxID", "Operator", "Type", "Counterparty", "Amount", "SMS_Stated_Fee", "Applied_Transfer_Fee", "Balance"]]
        st.dataframe(df_display, use_container_width=True, hide_index=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🗑️ Reset Internal Ledger"):
            st.session_state.extracted_tx_logs = []
            st.rerun()
    else:
        st.info("Aucune donnée enregistrée. Injectez un flux réseau à gauche pour alimenter l'architecture de scoring.")
    st.markdown('</div>', unsafe_allow_html=True)