"""
Dynamic processor system for different reconciliation types.
Each processor handles a specific reconciliation workflow.
"""

import os
import re
import pandas as pd
from typing import Dict, List, Any, Tuple
from config import ReconciliationConfig
from reconcile import extract_values, extract_from_txt, reconcile

class ReconciliationProcessor:
    """Base class for all reconciliation processors"""
    
    def __init__(self):
        self.config = ReconciliationConfig()
    
    def normalize_columns(self, df: pd.DataFrame, context: str = "general") -> pd.DataFrame:
        """Dynamically normalize column names based on configuration"""
        col_map = {}
        
        for col in df.columns:
            clean_col = str(col).strip().lower().replace(" ", "").replace("_", "")
            
            # Check each column mapping pattern
            for col_type, mapping in self.config.COLUMN_MAPPINGS.items():
                if any(pattern in clean_col for pattern in mapping["patterns"]):
                    col_map[col] = mapping["target"]
                    break
        
        return df.rename(columns=col_map)
    
    def load_excel_with_autodetect(self, filepath: str, detection_type: str = "transaction_excel") -> pd.DataFrame:
        """Auto-detect header row based on configuration patterns"""
        df_raw = pd.read_excel(filepath, header=None)
        header_row = None
        
        detection_patterns = self.config.HEADER_DETECTION.get(detection_type, [])
        
        for i, row in df_raw.iterrows():
            row_values = row.astype(str).str.strip().str.lower().tolist()
            if all(any(pattern in val for val in row_values) for pattern in detection_patterns):
                header_row = i
                break
        
        if header_row is None:
            raise ValueError(f"Could not detect header in {filepath} using patterns: {detection_patterns}")
        
        return pd.read_excel(filepath, header=header_row)
    
    def extract_from_text(self, filepath: str, pattern_set: str = "visa_settlement") -> Dict[str, Any]:
        """Extract data from text file using configurable patterns"""
        # Try different encodings
        text = None
        for encoding in self.config.FILE_SETTINGS["supported_encodings"]:
            try:
                with open(filepath, "r", encoding=encoding) as f:
                    text = f.read()
                break
            except UnicodeDecodeError:
                continue
        
        if text is None:
            raise ValueError(f"Could not read file {filepath} with any supported encoding")
        
        patterns = self.config.get_text_patterns(pattern_set)
        extracted_data = {}
        
        for field_name, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = match.group(1)
                # Process based on field type
                if "count" in field_name:
                    extracted_data[self._format_field_name(field_name)] = int(value)
                elif "amount" in field_name or "credit" in field_name:
                    extracted_data[self._format_field_name(field_name)] = float(value.replace(",", ""))
                else:
                    extracted_data[self._format_field_name(field_name)] = value
            else:
                extracted_data[self._format_field_name(field_name)] = None
        
        return extracted_data
    
    def _format_field_name(self, field_name: str) -> str:
        """Convert field names to display format"""
        return " ".join(word.capitalize() for word in field_name.split("_"))
    
    def validate_files(self, files: Dict[str, Any], recon_type: str) -> Tuple[bool, str]:
        """Validate uploaded files against configuration"""
        config = self.config.get_reconciliation_type(recon_type)
        
        if not config:
            return False, f"Unknown reconciliation type: {recon_type}"
        
        required_fields = [f["field_name"] for f in config["files"] if f["required"]]
        
        for field_name in required_fields:
            file_obj = files.get(field_name)
            if not file_obj or file_obj.filename == '':
                file_config = next(f for f in config["files"] if f["field_name"] == field_name)
                return False, f"Please upload {file_config['label']}"
        
        return True, ""
    
    def process(self, recon_type: str, files: Dict[str, Any]) -> Tuple[List[Dict], str]:
        """Main processing method - routes to specific processor"""
        config = self.config.get_reconciliation_type(recon_type)
        
        if not config:
            raise ValueError(f"Unknown reconciliation type: {recon_type}")
        
        # Validate files
        is_valid, error_msg = self.validate_files(files, recon_type)
        if not is_valid:
            raise ValueError(error_msg)
        
        # Get processor method name
        processor_name = config["processor"]
        
        if not hasattr(self, processor_name):
            raise ValueError(f"Processor {processor_name} not implemented")
        
        # Call the specific processor
        processor_method = getattr(self, processor_name)
        return processor_method(files)
    
    def process_bank_vs_visa(self, files: Dict[str, Any]) -> List[Dict]:
        """Process Bank Statement vs VISA Settlement reconciliation"""
        excel_file = files["excel_file"]
        txt_file = files["txt_file_bank"]
        
        # Save files temporarily
        excel_path = f"temp_{excel_file.filename}"
        txt_path = f"temp_{txt_file.filename}"
        
        excel_file.save(excel_path)
        txt_file.save(txt_path)
        
        try:
            # Use existing functions but with validation
            bank_data = extract_values(excel_path)
            visa_data = extract_from_txt(txt_path)
            df = reconcile(bank_data, visa_data)
            
            return df.to_dict(orient="records")
        finally:
            # Cleanup temp files
            if os.path.exists(excel_path):
                os.remove(excel_path)
            if os.path.exists(txt_path):
                os.remove(txt_path)
    
    def process_visa_vs_summary(self, files: Dict[str, Any]) -> List[Dict]:
        """Process VISA Detailed vs Summary Report reconciliation"""
        visa_file = files["visa_file"]
        txt_file = files["txt_file_summary"]
        
        # Save files temporarily
        visa_path = f"temp_{visa_file.filename}"
        txt_path = f"temp_{txt_file.filename}"
        
        visa_file.save(visa_path)
        txt_file.save(txt_path)
        
        try:
            # Extract data using dynamic methods
            txt_data = self.extract_from_text(txt_path, "visa_settlement")
            
            # Load and process VISA Excel file
            df = self.load_excel_with_autodetect(visa_path, "transaction_excel")
            df = self.normalize_columns(df, "visa")
            df = df.dropna(how="all")
            
            # Filter valid transactions
            if "Transaction ID" in df.columns:
                df = df[pd.to_numeric(df["Transaction ID"], errors="coerce").notnull()]
            
            # Calculate summary from detailed data
            visa_summary = {
                "Report Date": "N/A (from Excel)",
                "Transaction Count": df.shape[0],
                "Debit Amount": df["Amount"].sum() if "Amount" in df.columns else 0,
                "Fee Credit": df["Interchange"].sum() if "Interchange" in df.columns else 0
            }
            
            # Compare summaries
            checks = []
            for key in txt_data:
                val1 = visa_summary.get(key, "N/A")
                val2 = txt_data[key]
                status = "Match" if val1 == val2 else "Mismatch"
                checks.append({
                    "Check": key,
                    "Detailed Report": str(val1),
                    "Summary Report": str(val2),
                    "Status": status
                })
            
            return checks
        finally:
            # Cleanup temp files
            if os.path.exists(visa_path):
                os.remove(visa_path)
            if os.path.exists(txt_path):
                os.remove(txt_path)
    
    def process_cms_vs_visa(self, files: Dict[str, Any]) -> List[Dict]:
        """Process CMS vs VISA Comparison reconciliation"""
        cms_file = files["cms_file"]
        visa_file = files["visa_file_cms"]
        
        # Save files temporarily
        cms_path = f"temp_{cms_file.filename}"
        visa_path = f"temp_{visa_file.filename}"
        
        cms_file.save(cms_path)
        visa_file.save(visa_path)
        
        try:
            # Load both files with auto-detection
            cms_df = self.load_excel_with_autodetect(cms_path, "transaction_excel")
            visa_df = self.load_excel_with_autodetect(visa_path, "transaction_excel")
            
            # Normalize columns
            cms_df = self.normalize_columns(cms_df, "cms")
            visa_df = self.normalize_columns(visa_df, "visa")
            
            # Clean data
            cms_df = cms_df.dropna(how="all")
            visa_df = visa_df.dropna(how="all")
            
            # Filter valid transactions
            required_cols = ["Transaction ID", "RRN No"]
            cms_cols = [col for col in required_cols if col in cms_df.columns]
            visa_cols = [col for col in required_cols if col in visa_df.columns]
            
            if not cms_cols or not visa_cols:
                raise ValueError("Required columns (Transaction ID, RRN No) not found in files")
            
            # Filter numeric transaction IDs
            if "Transaction ID" in cms_df.columns:
                cms_df = cms_df[pd.to_numeric(cms_df["Transaction ID"], errors="coerce").notnull()]
            if "Transaction ID" in visa_df.columns:
                visa_df = visa_df[pd.to_numeric(visa_df["Transaction ID"], errors="coerce").notnull()]
            
            # Merge and compare
            merged = pd.merge(
                cms_df[cms_cols],
                visa_df[visa_cols],
                on=cms_cols,
                how="outer",
                indicator=True
            )
            
            merged["Match Status"] = merged["_merge"].map({
                "both": "Match",
                "left_only": "Missing in VISA",
                "right_only": "Missing in CMS"
            })
            
            result_cols = cms_cols + ["Match Status"]
            merged = merged[result_cols]
            
            return merged.astype(str).to_dict(orient="records")
        finally:
            # Cleanup temp files
            if os.path.exists(cms_path):
                os.remove(cms_path)
            if os.path.exists(visa_path):
                os.remove(visa_path)