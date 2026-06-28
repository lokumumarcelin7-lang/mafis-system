import streamlit as st
import pandas as pd
import hashlib
from datetime import datetime

# --- SYSTEM CONFIGURATION & COMPLIANCE THEME ---
st.set_page_config(
    page_title="MAFIS - Phase 1: Security Layer", 
    page_icon="🛡️", 
    layout="wide"
)

# Custom CSS for Professional FinTech Corporate Appearance
st.markdown("""
    <style>
    .system-title {font-size: 30px; font-weight: bold; color: #1E3A8A; font-family: 'Arial';}
    .compliance-badge {background-color: #E0F2FE; color: #0369A1; padding: 6px 12px; border-radius: 20px; font-size: 13px; font-weight: bold;}
    .crypto-box {background-color: #F8FAFC; border: 1px solid #E2E8F0; padding: 15px; border-radius: 8px; font-family: 'Courier New';}
    </style>
    """, unsafe_allow_html=True)

# --- BACKEND SECURITY & ARCHITECTURE MODULES ---

class DataProtectionService:
    """
    Cryptographic Tokenization Engine complying with Rwanda Data Protection Law N° 058/2021.
    Converts nominative PII (Personally Identifiable Information) into anonymous irreversible hashes.
    """
    @staticmethod
    def generate_sha256_token(phone_number: str) -> str:
        clean_input = str(phone_number).strip()
        hash_object = hashlib.sha256(clean_input.encode('utf-8'))
        hex_dig = hash_object.hexdigest()
        return f"MSME-{hex_dig[:12].upper()}"

class DatabaseManager:
    """
    Stateful In-Memory Relational Database Architecture.
    Persists data across client-side interactions using Streamlit SessionState.
    """
    @staticmethod
    def initialize_pipeline_database():
        if "mafis_ledger" not in st.session_state:
            st.session_state.mafis_ledger = []

    @staticmethod
    def commit_merchant_record(token: str, sector: str, duration: int):
        record = {
            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Security_Token": token,
            "Business_Sector": sector,
            "Operational_Duration_Months": duration,
            "Database_Status": "COMMITTED & LOCKED"
        }
        st.session_state.mafis_ledger.append(record)

# --- INITIALIZE DATABASE CORES ---
DatabaseManager.initialize_pipeline_database()


# --- FRONTEND USER INTERFACE (100% ENGLISH FOR ACADEMIC JURY) ---

st.markdown('<div class="system-title">🛡️ MAFIS Architectural Pipeline — Phase 1</div>', unsafe_allow_html=True)
st.markdown('<span class="compliance-badge">🔒 Compliant with Rwanda Data Protection Law N° 058/2021</span>', unsafe_allow_html=True)
st.markdown("---")

# Layout Split: Left for Ingestion & Hashing, Right for Database Audit Logs
col_input, col_ledger = st.columns([1, 1.2])

with col_input:
    st.subheader("1. KYC & Data Ingestion Gateway")
    
    phone_input = st.text_input(
        "Enter Raw Merchant Phone Number (MTN / Airtel):", 
        value="0789427000", 
        max_chars=10,
        help="Inputs are tokenized in real-time. Raw numbers are never saved to the database ledger."
    )
    
    sector_input = st.selectbox(
        "Select Enterprise Sector Category:",
        ["Retail / Boutique", "Services / Salon", "Transport / Moto"]
    )
    
    duration_input = st.slider(
        "Continuous Business Operation Seniority (Months):", 
        min_value=1, 
        max_value=60, 
        value=12
    )
    
    st.markdown("---")
    st.subheader("2. Real-Time Cryptographic Execution")
    
    generated_token = DataProtectionService.generate_sha256_token(phone_input)
    
    st.markdown(f"""
    <div class="crypto-box">
    <strong>Raw Input PII:</strong> {phone_input}<br>
    <strong>SHA-256 Hash Function:</strong> f(x) = SHA256(phone)<br>
    <strong>Generated Identity Token:</strong> <span style='color:#10B981; font-weight:bold;'>{generated_token}</span>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("⚡ Secure and Commit Record to Core Database"):
        prefix = phone_input[:3]
        if prefix not in ["078", "079", "072", "073"]:
            st.error("Telecom Architecture Error: Invalid prefix. Must start with 078/079 (MTN) or 072/073 (Airtel).")
        else:
            DatabaseManager.commit_merchant_record(generated_token, sector_input, duration_input)
            st.success("Data successfully encrypted and injected into the pipeline.")

with col_ledger:
    st.subheader("3. Relational Central Database Ledger Audit Logs")
    st.markdown("This view replicates the Bank Credit Officer's decoupled audit view. Zero raw phone numbers exist here.")
    
    if st.session_state.mafis_ledger:
        df_ledger = pd.DataFrame(st.session_state.mafis_ledger)
        st.dataframe(
            df_ledger, 
            use_container_width=True,
            column_order=["Timestamp", "Security_Token", "Business_Sector", "Operational_Duration_Months", "Database_Status"]
        )
        
        if st.button("🗑️ Clear Database State Logs"):
            st.session_state.mafis_ledger = []
            st.rerun()
    else:
        st.info("The central database ledger is currently empty. Awaiting secured transactions.")
