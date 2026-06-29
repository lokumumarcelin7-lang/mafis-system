# Collection_Agent_Parser.py
import re

class CollectionAgentParser:
    """
    MAFIS Core Component: Collection_Agent_Parser.py
    Agent autonome responsable de l'ingestion sémantique, de la validation réglementaire
    des taxes RRA et de l'activation des portes de qualité anti-fraude.
    """
    
    @staticmethod
    def validate_quality_gate(sms_text: str) -> bool:
        """
        🛑 PORTE DE QUALITÉ : Test de robustesse validé.
        Filtre et rejette immédiatement les injections de faux formats, les SMS tronqués,
        ou les flux de texte n'ayant pas les préfixes télécoms validés de Kigali (MTN/Airtel).
        """
        cleaned = sms_text.strip()
        
        # 1. Liste des signatures de confiance indispensables au démarrage ou au cœur du payload
        trusted_prefixes = [
            r"^\*16[45]\*",               # Préfixes USSD MTN MoMo / Airtel (*165*, *164*)
            r"^151\*Txn ID",              # Signature de reçu de paiement Airtel Money
            r"^You have received",         # Notification standard d'entrée MTN MoMo
            r"^TxId:",                    # Structure historique MTN Corporate
        ]
        
        # Validation de l'authenticité structurelle
        is_authentic = any(re.search(pattern, cleaned, re.IGNORECASE) for pattern in trusted_prefixes)
        
        # 2. Sécurité supplémentaire : rejeter si le flux contient des anomalies évidentes (trop court ou suspect)
        if len(cleaned) < 35 or "anti-fraud-trigger" in cleaned.lower():
            return False
            
        return is_authentic

    @staticmethod
    def calculate_rra_tax(amount: int, tx_type: str, operator_fee: int) -> float:
        """
        ⚖️ RÉGLEMENTATION RRA (Rwanda Revenue Authority) :
        Intégration des règles de calcul de la taxe sur l'argent mobile pour l'analyse MSME :
        - 15% de taxe sur la valeur des commissions ou frais financiers facturés (Excise Duty / Financial Services Tax).
        - 0.2% de prélèvement de conformité fiscale sur le volume des transactions commerciales (Merchant Payments) pour le scoring.
        """
        if amount <= 0:
            return 0.0
            
        rra_tax = 0.0
        
        # Règle A : Taxe sur les frais de service financiers de transaction
        if operator_fee > 0:
            rra_tax += operator_fee * 0.15
            
        # Règle B : Taxe de formalisation de l'activité commerciale (Pivot MAFIS de scoring alternatif)
        if "Merchant Payment" in tx_type:
            rra_tax += amount * 0.002
            
        return round(rra_tax, 2)

    @staticmethod
    def parse_sms(sms_text: str):
        """
        Pipeline principal d'extraction sémantique avec barrière de sécurité intégrée.
        """
        # Exécution de la porte de qualité avant tout traitement
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
                "Status": "🚨 REJETÉ : Préfixe ou Format Invalide"
            }

        # Normalisation contre le bug des espaces insécables (\xa0)
        cleaned_sms = re.sub(r'\s+', ' ', sms_text).strip()
        sms_lower = cleaned_sms.lower()
        
        is_airtel = any(x in sms_lower for x in ["txn id", "tid", "new balance", "bal rwf"])

        def safe_int_extract(regex_pattern, text):
            match = re.search(regex_pattern, text, re.IGNORECASE)
            if match and match.group(1):
                digits = re.sub(r'\D', '', match.group(1))
                return int(digits) if digits else 0
            return 0

        # Extraction de l'identifiant unique
        txid_match = re.search(r"(?:FT\s*Id|TxId|Txn\s*ID|TID)[:\s]+([A-Za-z0-9\.\-]+)", cleaned_sms, re.IGNORECASE)
        txid = txid_match.group(1) if txid_match else "NOT_FOUND"
        
        # Extraction du montant
        amount = safe_int_extract(r"(?:received|transaction of|payment of|amt)[:\s]+(?:rwf)?\s*([0-9\s, ]+)", cleaned_sms)
        if amount == 0:
            amount = safe_int_extract(r"([0-9\s, ]+)\s*rwf\s+transferred", cleaned_sms)

        # Extraction du solde et des frais déclarés
        balance = safe_int_extract(r"(?:balance is|balance:|bal)[:\s]+(?:rwf)?\s*([0-9\s, ]+)", cleaned_sms)
        extracted_fee = safe_int_extract(r"fee[:\s]+(?:rwf)?\s*([0-9\s, ]+)", cleaned_sms)
        
        # Extraction du tiers (Contrepartie)
        counterparty = "Ecosystem Internal"
        cp_match = re.search(r"(?:from|to|by|sent to)\s+([A-Za-z\s\.0-9]+)(?:\(|at|was|in\s|via|\d|$)", cleaned_sms, re.IGNORECASE)
        if cp_match:
            counterparty = cp_match.group(1).replace("Ltd", "").strip()

        # Qualification du type de flux
        if "received" in sms_lower:
            tx_type = "Cash In (Réception)"
            transfer_fee = 0
        elif "payment of" in sms_lower or "by" in sms_lower:
            tx_type = "Merchant Payment (Achat)"
            transfer_fee = 0
        else:
            tx_type = "P2P Transfer (Envoi)"
            if is_airtel:
                transfer_fee = 0
            else:
                if amount < 10000: transfer_fee = 100
                elif amount < 150000: transfer_fee = 250
                else: transfer_fee = 1500

        # Application de la règle de calcul de la taxe RRA
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
            "Status": "✅ Validé par Porte de Qualité"
        }