# Collection_Agent_Parser.py
import re

class CollectionAgentParser:
    """
    MAFIS Core Component: Collection_Agent_Parser.py
    Autonomous agent responsible for semantic ingestion, regulatory RRA tax compliance 
    calculations, and activating anti-fraud robustness quality gates.
    """
    
    @staticmethod
    def validate_quality_gate(sms_text: str) -> bool:
        """
        🛑 QUALITY GATE: Robustness Validation Test.
        Immediately filters and rejects format injections, truncated payloads,
        or unstructured text missing verified Kigali telecom network signatures (MTN/Airtel).
        """
        cleaned = sms_text.strip()
        
        # 1. Trusted structural signatures required at payload initiation or core segments
        trusted_prefixes = [
            r"^\*16[45]\*",               # USSD MTN MoMo / Airtel Network Gateways (*165*, *164*)
            r"^151\*Txn ID",              # Airtel Money Payment Receipt Signature
            r"^You have received",         # MTN MoMo Standard Inbound Notification
            r"^TxId:",                    # MTN Corporate Legacy Format Structure
        ]
        
        # Validate structural authenticity
        is_authentic = any(re.search(pattern, cleaned, re.IGNORECASE) for pattern in trusted_prefixes)
        
        # 2. Heuristic Check: Reject streams with anomaly flags (under minimum length or malicious strings)
        if len(cleaned) < 35 or "anti-fraud-trigger" in cleaned.lower():
            return False
            
        return is_authentic

    @staticmethod
    def calculate_rra_tax(amount: int, tx_type: str, operator_fee: int) -> float:
        """
        ⚖️ RRA REGULATION LAYER (Rwanda Revenue Authority):
        Implements mobile money regulatory tax evaluation rules tailored for alternative MSME credit scoring:
        - 15% Excise Duty / Financial Services Tax applied on the transaction service commissions.
        - 0.2% Alternative Formalization Levy simulated on commercial trade volumes (Merchant Payments) for credit scoring context.
        """
        if amount <= 0:
            return 0.0
            
        rra_tax = 0.0
        
        # Rule A: Financial Services Excise Duty on transaction processing fees
        if operator_fee > 0:
            rra_tax += operator_fee * 0.15
            
        # Rule B: Informal Sector Formalization Levy (MAFIS Alternative Scoring Core Pivot)
        if "Merchant Payment" in tx_type:
            rra_tax += amount * 0.002
            
        return round(rra_tax, 2)

    @staticmethod
    def parse_sms(sms_text: str):
        """
        Main semantic extraction pipeline wrapped inside the system's security perimeter.
        """
        # Execute security gate check before resource allocation
        if not CollectionAgentParser.validate_quality_gate(sms_text):
            return {
                "TxID": "FAILED_QUAL_GATE",
                "Operator": "REJECTED_STREAM",
                "Type": "CRITICAL_INVALID",
                "Counterparty": "MALICIOUS / UNKNOWN",
                "Amount": 0,
                "SMS_Stated_Fee": 0,
                "Applied_Transfer_Fee": 0,
                "RRA_Tax": 0.0,
                "Balance": 0,
                "Status": "🚨 REJECTED: Invalid Stream Pattern or Network Signature"
            }

        # Normalize stream against non-breaking space variants (\xa0)
        cleaned_sms = re.sub(r'\s+', ' ', sms_text).strip()
        sms_lower = cleaned_sms.lower()
        
        is_airtel = any(x in sms_lower for x in ["txn id", "tid", "new balance", "bal rwf"])

        def safe_int_extract(regex_pattern, text):
            match = re.search(regex_pattern, text, re.IGNORECASE)
            if match and match.group(1):
                digits = re.sub(r'\D', '', match.group(1))
                return int(digits) if digits else 0
            return 0

        # Extract unique Transaction Identifier
        txid_match = re.search(r"(?:FT\s*Id|TxId|Txn\s*ID|TID)[:\s]+([A-Za-z0-9\.\-]+)", cleaned_sms, re.IGNORECASE)
        txid = txid_match.group(1) if txid_match else "NOT_FOUND"
        
        # Extract transactional financial volume
        amount = safe_int_extract(r"(?:received|transaction of|payment of|amt)[:\s]+(?:rwf)?\s*([0-9\s, ]+)", cleaned_sms)
        if amount == 0:
            amount = safe_int_extract(r"([0-9\s, ]+)\s*rwf\s+transferred", cleaned_sms)

        # Extract post-transaction balance and operator fees
        balance = safe_int_extract(r"(?:balance is|balance:|bal)[:\s]+(?:rwf)?\s*([0-9\s, ]+)", cleaned_sms)
        extracted_fee = safe_int_extract(r"fee[:\s]+(?:rwf)?\s*([0-9\s, ]+)", cleaned_sms)
        
        # Extract counterparty entity name
        counterparty = "Ecosystem Internal"
        cp_match = re.search(r"(?:from|to|by|sent to)\s+([A-Za-z\s\.0-9]+)(?:\(|at|was|in\s|via|\d|$)", cleaned_sms, re.IGNORECASE)
        if cp_match:
            counterparty = cp_match.group(1).replace("Ltd", "").strip()

        # Categorize financial data stream context
        if "received" in sms_lower:
            tx_type = "Cash In (Receipt)"
            transfer_fee = 0
        elif "payment of" in sms_lower or "by" in sms_lower:
            tx_type = "Merchant Payment (Purchase)"
            transfer_fee = 0
        else:
            tx_type = "P2P Transfer (Sent)"
            if is_airtel:
                transfer_fee = 0
            else:
                if amount < 10000: transfer_fee = 100
                elif amount < 150000: transfer_fee = 250
                else: transfer_fee = 1500

        # Calculate regulatory RRA obligations
        active_fee = extracted_fee if extracted_fee > 0 else transfer_fee
        rra_tax = CollectionAgentParser.calculate_rra_tax(amount, tx_type, active_fee)

        return {
            "TxID": txid,
            "Operator": "Airtel Money" if is_airtel else "MTN MoMo",
            "Type": tx_type,
            "Counterparty": counterparty if counterparty else "Ecosystem Internal",
            "Amount": amount,
            "SMS_Stated_Fee": extracted_fee,
            "Applied_Transfer_Fee": transfer_fee,
            "RRA_Tax": rra_tax,
            "Balance": balance,
            "Status": "✅ Verified by Quality Gate"
        }