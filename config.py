"""
Configuration-driven architecture for the reconciliation tool.
All reconciliation types, file mappings, and processing logic are defined here.
"""

import re
from typing import Dict, List, Any, Callable

class ReconciliationConfig:
    """Central configuration for all reconciliation types and processing rules"""
    
    # Reconciliation type definitions
    RECONCILIATION_TYPES = {
        "bank_vs_visa": {
            "name": "Bank Statement vs VISA Settlement",
            "description": "Compare bank statement data with VISA settlement summary",
            "files": [
                {
                    "field_name": "excel_file",
                    "label": "Bank Statement (Excel)",
                    "accept": ".xlsx,.xls",
                    "required": True
                },
                {
                    "field_name": "txt_file_bank", 
                    "label": "VISA Settlement Summary (TXT)",
                    "accept": ".txt",
                    "required": True
                }
            ],
            "processor": "process_bank_vs_visa",
            "result_template": "bank_vs_visa"
        },
        "visa_vs_summary": {
            "name": "VISA Detailed vs Summary Report",
            "description": "Compare detailed VISA report with summary text file",
            "files": [
                {
                    "field_name": "visa_file",
                    "label": "VISA Detailed Report (Excel)",
                    "accept": ".xlsx,.xls",
                    "required": True
                },
                {
                    "field_name": "txt_file_summary",
                    "label": "VISA Settlement Summary (TXT)",
                    "accept": ".txt", 
                    "required": True
                }
            ],
            "processor": "process_visa_vs_summary",
            "result_template": "visa_vs_summary"
        },
        "cms_vs_visa": {
            "name": "CMS vs VISA Comparison",
            "description": "Compare CMS transaction data with VISA transaction data",
            "files": [
                {
                    "field_name": "cms_file",
                    "label": "CMS Report (Excel)",
                    "accept": ".xlsx,.xls",
                    "required": True
                },
                {
                    "field_name": "visa_file_cms",
                    "label": "VISA Report (Excel)", 
                    "accept": ".xlsx,.xls",
                    "required": True
                }
            ],
            "processor": "process_cms_vs_visa",
            "result_template": "cms_vs_visa"
        }
    }
    
    # Column mapping rules for dynamic column detection
    COLUMN_MAPPINGS = {
        "transaction_id": {
            "patterns": ["transaction", "transact", "txn", "trans_id", "id"],
            "target": "Transaction ID"
        },
        "rrn": {
            "patterns": ["rrn", "reference", "ref_no", "ref_number"],
            "target": "RRN No"
        },
        "merchant": {
            "patterns": ["merchant", "shop", "store", "business"],
            "target": "Merchant"
        },
        "mcc": {
            "patterns": ["mcc", "merchant_code", "category_code"],
            "target": "MCC Code"
        },
        "amount": {
            "patterns": ["amount", "value", "sum", "total", "amt"],
            "target": "Amount"
        },
        "interchange": {
            "patterns": ["interchange", "fee", "commission"],
            "target": "Interchange"
        },
        "dr": {
            "patterns": ["dr", "debit", "debit_amount"],
            "target": "DR"
        },
        "cr": {
            "patterns": ["cr", "credit", "credit_amount"],
            "target": "CR"
        },
        "net": {
            "patterns": ["net", "net_amount", "balance"],
            "target": "Net"
        }
    }
    
    # Text parsing patterns for different file formats
    TEXT_PATTERNS = {
        "visa_settlement": {
            "report_date": r"REPORT DATE:\s*([0-9]{2}[A-Z]{3}[0-9]{2})",
            "transaction_count": r"TOTAL INTERCHANGE VALUE\s+(\d+)",
            "fee_credit": r"TOTAL INTERCHANGE VALUE\s+\d+\s+([\d,]+\.\d{2})",
            "debit_amount": r"TOTAL INTERCHANGE VALUE\s+\d+\s+[\d,]+\.\d{2}\s+([\d,]+\.\d{2})"
        }
    }
    
    # Section name mappings for reconciliation
    SECTION_MAPPINGS = {
        "INTERCHANGE": "Interchange",
        "REIMBURSEMENT": "Reimbursement", 
        "REIMBURSEMENTFEES": "Reimbursement",
        "VISA CHARGES": "VisaCharges",
        "VISACHARGES": "VisaCharges",
        "TOTAL": "Total",
        "NETSETTLEMENT": "Total"
    }
    
    # Valid sections for processing
    VALID_SECTIONS = ["INTERCHANGE", "REIMBURSEMENT", "REIMBURSEMENTFEES", 
                     "VISACHARGES", "NETSETTLEMENT", "TOTAL"]
    
    # Header detection patterns
    HEADER_DETECTION = {
        "transaction_excel": ["transact", "rrn"],
        "bank_excel": ["dr", "cr", "net"]
    }
    
    # File processing settings
    FILE_SETTINGS = {
        "max_file_size": 50 * 1024 * 1024,  # 50MB
        "supported_encodings": ["utf-8", "latin1", "cp1252"],
        "excel_extensions": [".xlsx", ".xls"],
        "text_extensions": [".txt", ".csv"]
    }
    
    # Result table configurations
    RESULT_TABLES = {
        "bank_vs_visa": {
            "columns": ["Section", "Check", "Bank Statement", "Visa Summary", "Status", "Difference"],
            "status_column": "Status"
        },
        "visa_vs_summary": {
            "columns": ["Check", "Detailed Report", "Summary Report", "Status"],
            "status_column": "Status"
        },
        "cms_vs_visa": {
            "columns": ["Transaction ID", "RRN No", "Match Status"],
            "status_column": "Match Status"
        }
    }
    
    @classmethod
    def get_reconciliation_type(cls, recon_type: str) -> Dict[str, Any]:
        """Get configuration for a specific reconciliation type"""
        return cls.RECONCILIATION_TYPES.get(recon_type, {})
    
    @classmethod
    def get_all_types(cls) -> Dict[str, Dict[str, Any]]:
        """Get all available reconciliation types"""
        return cls.RECONCILIATION_TYPES
    
    @classmethod
    def get_column_mapping(cls, column_type: str) -> Dict[str, Any]:
        """Get column mapping for a specific column type"""
        return cls.COLUMN_MAPPINGS.get(column_type, {})
    
    @classmethod
    def get_text_patterns(cls, pattern_set: str) -> Dict[str, str]:
        """Get text parsing patterns for a specific format"""
        return cls.TEXT_PATTERNS.get(pattern_set, {})
    
    @classmethod
    def validate_reconciliation_type(cls, recon_type: str) -> bool:
        """Validate if reconciliation type exists"""
        return recon_type in cls.RECONCILIATION_TYPES