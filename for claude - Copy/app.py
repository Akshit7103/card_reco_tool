import os
import re
import pandas as pd
from flask import Flask, render_template, request, send_file
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "uploads"
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

last_output = None  # store last reconciliation DataFrame for download

# ----------------- Utility Functions ----------------- #

def normalize_columns(df, is_visa=False):
    """Normalize column names to standard ones"""
    col_map = {}
    for col in df.columns:
        clean = str(col).strip().lower().replace(" ", "").replace("_", "")
        if clean.startswith("transact"):
            col_map[col] = "Transaction ID"
        elif clean.startswith("rrn"):
            col_map[col] = "RRN No"
        elif "merchant" in clean:
            col_map[col] = "Merchant"
        elif "mcc" in clean:
            col_map[col] = "MCC Code"
        elif "amount" in clean:
            col_map[col] = "Amount"
        elif "interchange" in clean and is_visa:
            col_map[col] = "Interchange"
    df = df.rename(columns=col_map)
    return df

def load_excel_with_autodetect(filepath):
    """Auto-detect header row containing Transaction ID and RRN No"""
    df_raw = pd.read_excel(filepath, header=None)
    header_row = None
    for i, row in df_raw.iterrows():
        row_values = row.astype(str).str.strip().str.lower().tolist()
        if any("transact" in val for val in row_values) and any("rrn" in val for val in row_values):
            header_row = i
            break
    if header_row is None:
        raise ValueError(f"Could not detect header in {filepath}")
    return pd.read_excel(filepath, header=header_row)

def extract_visa(filepath):
    df = load_excel_with_autodetect(filepath)
    df = normalize_columns(df, is_visa=True)
    df = df.dropna(how="all")
    keep_cols = ["Transaction ID", "RRN No", "Merchant", "MCC Code", "Amount", "Interchange"]
    df = df[[col for col in keep_cols if col in df.columns]]
    df = df[pd.to_numeric(df["Transaction ID"], errors="coerce").notnull()]
    return df

def extract_cms(filepath):
    df = load_excel_with_autodetect(filepath)
    df = normalize_columns(df, is_visa=False)
    df = df.dropna(how="all")
    keep_cols = ["Transaction ID", "RRN No", "Merchant", "MCC Code", "Amount"]
    df = df[[col for col in keep_cols if col in df.columns]]
    df = df[pd.to_numeric(df["Transaction ID"], errors="coerce").notnull()]
    return df

def extract_from_txt(filepath):
    """Extract key fields from VISA Settlement Summary TXT"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read()
    except UnicodeDecodeError:
        with open(filepath, "r", encoding="latin1") as f:
            text = f.read()

    report_date = re.search(r"REPORT DATE:\s*([0-9]{2}[A-Z]{3}[0-9]{2})", text, re.IGNORECASE)
    txn_count = re.search(r"TOTAL INTERCHANGE VALUE\s+(\d+)", text)
    fee_credit = re.search(r"TOTAL INTERCHANGE VALUE\s+\d+\s+([\d,]+\.\d{2})", text)
    debit_amount = re.search(r"TOTAL INTERCHANGE VALUE\s+\d+\s+[\d,]+\.\d{2}\s+([\d,]+\.\d{2})", text)

    return {
        "Report Date": report_date.group(1) if report_date else None,
        "Transaction Count": int(txn_count.group(1)) if txn_count else None,
        "Debit Amount": float(debit_amount.group(1).replace(",", "")) if debit_amount else None,
        "Fee Credit": float(fee_credit.group(1).replace(",", "")) if fee_credit else None,
    }

# ----------------- Flask Routes ----------------- #

@app.route("/", methods=["GET", "POST"])
def index():
    global last_output
    result = None
    recon_type = request.form.get("recon_type")

    if request.method == "POST":
        if recon_type == "visa_vs_summary":
            txt_file = request.files.get("txt_file")
            visa_file = request.files.get("visa_file")

            if txt_file and visa_file:
                txt_path = os.path.join(app.config["UPLOAD_FOLDER"], secure_filename(txt_file.filename))
                visa_path = os.path.join(app.config["UPLOAD_FOLDER"], secure_filename(visa_file.filename))
                txt_file.save(txt_path)
                visa_file.save(visa_path)

                txt_data = extract_from_txt(txt_path)
                visa_df = extract_visa(visa_path)

                visa_summary = {
                    "Report Date": "N/A (from Excel)",
                    "Transaction Count": visa_df.shape[0],
                    "Debit Amount": visa_df["Amount"].sum(),
                    "Fee Credit": visa_df["Interchange"].sum() if "Interchange" in visa_df else 0
                }

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

                result = checks
                last_output = pd.DataFrame(checks)

        elif recon_type == "cms_vs_visa":
            cms_file = request.files.get("cms_file")
            visa_file = request.files.get("visa_file")

            if cms_file and visa_file:
                cms_path = os.path.join(app.config["UPLOAD_FOLDER"], secure_filename(cms_file.filename))
                visa_path = os.path.join(app.config["UPLOAD_FOLDER"], secure_filename(visa_file.filename))
                cms_file.save(cms_path)
                visa_file.save(visa_path)

                cms_df = extract_cms(cms_path)
                visa_df = extract_visa(visa_path)

                merged = pd.merge(
                    cms_df[["Transaction ID", "RRN No"]],
                    visa_df[["Transaction ID", "RRN No"]],
                    on=["Transaction ID", "RRN No"],
                    how="outer",
                    indicator=True
                )

                merged["Match Status"] = merged["_merge"].map({
                    "both": "Match",
                    "left_only": "Missing in VISA",
                    "right_only": "Missing in CMS"
                })

                merged = merged[["Transaction ID", "RRN No", "Match Status"]]
                result = merged.astype(str).to_dict(orient="records")
                last_output = merged

    return render_template("index.html", result=result, recon_type=recon_type)

@app.route("/download")
def download():
    global last_output
    if last_output is not None:
        path = "reconciliation_output.xlsx"
        last_output.to_excel(path, index=False)
        return send_file(path, as_attachment=True)
    return "No reconciliation results available to download."

if __name__ == "__main__":
    app.run(debug=True)
