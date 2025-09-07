import pandas as pd
import re

# Excel extraction function (from phase3_test.py)
def extract_values(file_path):
    # Read Excel file
    df = pd.read_excel(file_path)

    # Clean column names
    df.columns = [col.strip() for col in df.columns]

    # Clean row labels (first column)
    df.iloc[:, 0] = df.iloc[:, 0].astype(str).str.strip()

    extracted = {}

    # Iterate over all rows
    for idx, row in df.iterrows():
        label = row.iloc[0]   # first column = label (e.g., Interchange, Reimbursement, etc.)
        
        # Replace NaN or "nan" with "Total"
        if pd.isna(label) or label.lower() == "nan":
            label = "Total"
        
        dr = row["DR"]
        cr = row["CR"]
        net = row["Net"]

        extracted[label] = {
            "DR": dr,
            "CR": cr,
            "Net": net
        }

    return extracted

# TXT extraction functions (from txt.py)
def parse_amount(value: str) -> float:
    """Convert amounts like '1,540,000.00DB' or '1,500.00CR' into signed floats."""
    if not value or value.strip() == "":
        return 0.0
    value = value.replace(",", "").strip()

    sign = 1
    if value.endswith("DB"):
        value = value[:-2]
        sign = 1
    elif value.endswith("CR"):
        value = value[:-2]
        sign = -1

    try:
        return float(value) * sign
    except ValueError:
        return 0.0

def extract_from_txt(file_path: str):
    with open(file_path, "r") as f:
        lines = f.readlines()

    data = {}
    valid_sections = ["INTERCHANGE", "REIMBURSEMENT", "REIMBURSEMENTFEES", "VISACHARGES", "NETSETTLEMENT", "TOTAL"]

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if line.upper().startswith("TOTAL") or "NET SETTLEMENT AMOUNT" in line.upper():
            section_name = re.sub(r"[\d,\.]+.*", "", line).strip()
            section_name = section_name.replace("TOTAL", "").replace("AMOUNT", "").replace("VALUE", "").strip()
            if not section_name:
                section_name = "TOTAL"
        else:
            # Section name = remove numbers and keep only text
            section_name = re.sub(r"[\d,\.]+.*", "", line).strip()

        section_name = section_name.replace(" ", "").upper()

        if section_name not in valid_sections:
            continue  # skip ACQUIRER, ISSUER, OTHER, etc.

        numbers = re.findall(r"[\d,]+\.\d{2}(?:DB|CR)?", line)
        if numbers:
            cr = parse_amount(numbers[0]) if len(numbers) > 0 else 0.0
            dr = parse_amount(numbers[1]) if len(numbers) > 1 else 0.0
            net = parse_amount(numbers[2]) if len(numbers) > 2 else dr - cr

            data[section_name] = {"CR": cr, "DR": dr, "Net": net}

    return data

# Normalize section names
SECTION_MAP = {
    "INTERCHANGE": "Interchange",
    "REIMBURSEMENT": "Reimbursement",
    "REIMBURSEMENTFEES": "Reimbursement",
    "VISA CHARGES": "VisaCharges",
    "VISACHARGES": "VisaCharges",
    "TOTAL": "Total",
    "NETSETTLEMENT": "Total"
}

def normalize_sections(data):
    normalized = {}
    for section, values in data.items():
        key = SECTION_MAP.get(section.upper().replace(" ", ""), section)
        normalized[key] = values
    return normalized

def reconcile(bank_data, visa_data):
    bank_data = normalize_sections(bank_data)
    visa_data = normalize_sections(visa_data)

    records = []
    sections = set(bank_data.keys()).union(set(visa_data.keys()))

    for section in sections:
        bank_vals = bank_data.get(section, {"DR": 0.0, "CR": 0.0, "Net": 0.0})
        visa_vals = visa_data.get(section, {"DR": 0.0, "CR": 0.0, "Net": 0.0})

        for field in ["DR", "CR", "Net"]:
            bank_val = bank_vals.get(field, 0.0)
            visa_val = visa_vals.get(field, 0.0)

            status = "Match" if bank_val == visa_val else "Mismatch"
            diff = bank_val - visa_val

            records.append({
                "Section": section,
                "Check": field,
                "Bank Statement": bank_val,
                "Visa Summary": visa_val,
                "Status": status,
                "Difference": diff
            })

    return pd.DataFrame(records)

if __name__ == "__main__":
    print("This module is designed to be imported and used by the web application.")
    print("To run the reconciliation tool, use: python app.py")
