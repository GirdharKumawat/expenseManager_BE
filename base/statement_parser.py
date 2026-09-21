import re
import io
from datetime import datetime
import pandas as pd

def parse_date(date_str):
    """Attempt to parse various date formats into YYYY-MM-DD string using regex and strptime."""
    if not date_str or pd.isna(date_str):
        return datetime.now().strftime("%Y-%m-%d")
    date_str = str(date_str).strip()
    
    formats = [
        "%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d",
        "%d-%b-%Y", "%d %b %Y", "%b %d, %Y", "%d/%m/%y", "%d-%m-%y",
        "%Y-%m-%d %H:%M:%S", "%d-%m-%Y %H:%M:%S"
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue
    
    # Extract date using regex pattern
    match = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})', date_str)
    if match:
        d, m, y = match.groups()
        if len(y) == 2:
            y = "20" + y
        try:
            return f"{int(y):04d}-{int(m):02d}-{int(d):02d}"
        except ValueError:
            pass
            
    return datetime.now().strftime("%Y-%m-%d")


def extract_transaction_details(description):
    """
    Deterministically extracts payee/merchant name, UTR/Reference ID, and payment mode
    from transaction text using regex patterns and string manipulation.
    """
    if not description or pd.isna(description):
        return "Statement Transaction", "General Merchant", "", "Bank"
        
    desc_str = str(description).strip()
    reference_id = ""
    merchant_payee = ""
    
    # Detect Payment Mode via hardcoded keyword matching
    desc_upper = desc_str.upper()
    if any(k in desc_upper for k in ["UPI", "GPAY", "PHONEPE", "PAYTM", "BHIM"]):
        payment_type = "Mobile"
    elif any(k in desc_upper for k in ["POS", "ECOM", "CARD", "VISA", "MASTERCARD", "AMEX"]):
        payment_type = "Card"
    elif any(k in desc_upper for k in ["ATM", "CASH"]):
        payment_type = "Cash"
    else:
        payment_type = "Bank"

    # Regex 1: Standard UPI format: UPI/DR/123456789012/MERCHANT_NAME/BANK/... or UPI/CR/123456789012/PAYEE/...
    upi_match1 = re.search(r'UPI/(?:DR|CR)/(\d{10,18})/([^/]+)', desc_str, re.IGNORECASE)
    if upi_match1:
        reference_id = upi_match1.group(1).strip()
        merchant_payee = upi_match1.group(2).strip()

    # Regex 2: Alternate UPI format: UPI/MERCHANT_NAME/123456789012/...
    if not merchant_payee:
        upi_match2 = re.search(r'UPI/([^/]+)/(\d{10,18})', desc_str, re.IGNORECASE)
        if upi_match2:
            merchant_payee = upi_match2.group(1).strip()
            reference_id = upi_match2.group(2).strip()

    # Regex 3: IMPS format: IMPS/P2A/123456789012/PAYEE_NAME/...
    if not merchant_payee:
        imps_match = re.search(r'IMPS/(?:P2A/|P2P/)?(\d{10,18})/([^/]+)', desc_str, re.IGNORECASE)
        if imps_match:
            reference_id = imps_match.group(1).strip()
            merchant_payee = imps_match.group(2).strip()

    # Regex 4: POS / Card format: POS 123456 MERCHANT NAME
    if not merchant_payee:
        pos_match = re.search(r'(?:POS|ECOM)\s+\d+\s+([^/]+)', desc_str, re.IGNORECASE)
        if pos_match:
            merchant_payee = pos_match.group(1).strip()

    # Regex 5: Payment gateway prefixes: PAYTM*MERCHANT or RAZORPAY*MERCHANT
    if not merchant_payee:
        gw_match = re.search(r'(?:PAYTM|RAZORPAY|CCAVENUE|PAYU)\*([^\s/]+)', desc_str, re.IGNORECASE)
        if gw_match:
            merchant_payee = gw_match.group(1).strip()

    # Standalone reference ID / UTR extraction
    if not reference_id:
        ref_match = re.search(r'\b(\d{12})\b', desc_str) or re.search(r'(?:UTR|REF|TXN|ID)[\s:-]*([A-Z0-9]{8,18})', desc_str, re.IGNORECASE)
        if ref_match:
            reference_id = ref_match.group(1).strip()

    # Fallback merchant name cleaning
    if not merchant_payee:
        sub_desc = re.sub(r'^(?:UPI|NEFT|IMPS|RTGS|ATM|POS|INB)[/-]?', '', desc_str, flags=re.IGNORECASE).strip()
        merchant_payee = re.sub(r'[/_\-\*]+', ' ', sub_desc).strip()
        
    merchant_payee = re.sub(r'\s+', ' ', merchant_payee).strip().title()
    if not merchant_payee:
        merchant_payee = "General Merchant"

    return desc_str, merchant_payee, reference_id, payment_type


def infer_category_and_type(description, original_type=None, amount=0):
    """Determines category and DEBIT/CREDIT type deterministically via hardcoded keyword rules."""
    desc_lower = (description or "").lower()
    
    tx_type = original_type or "DEBIT"
    if not original_type:
        credit_keywords = ["credited", "received", "refund", "cashback", "salary", "deposit", "cr.", " cr", "added"]
        if any(kw in desc_lower for kw in credit_keywords):
            tx_type = "CREDIT"
        else:
            tx_type = "DEBIT"
            
    if tx_type == "CREDIT":
        if any(kw in desc_lower for kw in ["salary", "payroll", "stipend"]):
            category = "Salary"
        elif any(kw in desc_lower for kw in ["refund", "cashback", "reversal"]):
            category = "Refund"
        elif any(kw in desc_lower for kw in ["freelance", "upwork", "fiverr", "invoice"]):
            category = "Freelance"
        elif any(kw in desc_lower for kw in ["dividend", "interest", "zerodha", "groww", "stock"]):
            category = "Investment"
        elif any(kw in desc_lower for kw in ["gift", "bonus"]):
            category = "Gift"
        else:
            category = "Other"
    else:
        if any(kw in desc_lower for kw in ["swiggy", "zomato", "restaurant", "cafe", "dominos", "pizza", "kfc", "mcdonald", "food", "diner"]):
            category = "Food"
        elif any(kw in desc_lower for kw in ["uber", "ola", "irctc", "metro", "fuel", "petrol", "hpcl", "bpcl", "flight", "rapido", "rail", "cab"]):
            category = "Transport"
        elif any(kw in desc_lower for kw in ["netflix", "bookmyshow", "spotify", "prime", "cinema", "movie", "game", "steam"]):
            category = "Entertainment"
        elif any(kw in desc_lower for kw in ["bill", "electricity", "water", "recharge", "jio", "airtel", "vi", "bescom", "gas"]):
            category = "Utilities"
        elif any(kw in desc_lower for kw in ["amazon", "flipkart", "myntra", "meesho", "zara", "ajio", "decathlon", "shopping", "store"]):
            category = "Shopping"
        elif any(kw in desc_lower for kw in ["pharmacy", "hospital", "apollo", "practo", "clinic", "lab", "medicine", "health", "doctor"]):
            category = "Health"
        elif any(kw in desc_lower for kw in ["rent", "landlord", "pg rent"]):
            category = "Rent"
        else:
            category = "Other"
            
    return category, tx_type


def parse_statement_file(file_obj, filename):
    """
    Parses CSV, XLSX, XLS, or PDF bank/UPI statement files using rule-based regex patterns.
    Returns a structured list of uniform transaction dictionaries.
    """
    ext = filename.split('.')[-1].lower()
    transactions = []
    
    if hasattr(file_obj, 'seek'):
        file_obj.seek(0)
        
    if ext in ['csv', 'xlsx', 'xls']:
        df = None
        if ext == 'csv':
            content = file_obj.read()
            if isinstance(content, bytes):
                try:
                    content_str = content.decode('utf-8')
                except UnicodeDecodeError:
                    content_str = content.decode('latin1')
            else:
                content_str = str(content)
            df = pd.read_csv(io.StringIO(content_str))
        else:
            df = pd.read_excel(file_obj)
            
        if df is None or df.empty:
            return transactions
            
        # Clean column names
        df.columns = [str(c).strip().lower() for c in df.columns]
        
        # Word-boundary column matcher
        def is_match(col_name, keywords):
            for kw in keywords:
                if re.search(r'\b' + re.escape(kw) + r'\b', col_name):
                    return True
            return False

        date_col = next((c for c in df.columns if is_match(c, ['date', 'txn date', 'transaction date', 'val date', 'time'])), None)
        desc_col = next((c for c in df.columns if is_match(c, ['description', 'narration', 'particulars', 'remarks', 'merchant', 'details', 'payee'])), None)
        amt_col = next((c for c in df.columns if is_match(c, ['amount', 'txn amount', 'sum', 'total']) and not any(k in c for k in ['debit', 'credit', 'balance'])), None)
        debit_col = next((c for c in df.columns if is_match(c, ['debit', 'withdrawal', 'dr', 'withdrawals', 'debits'])), None)
        credit_col = next((c for c in df.columns if is_match(c, ['credit', 'deposit', 'cr', 'deposits', 'credits'])), None)
        type_col = next((c for c in df.columns if is_match(c, ['type', 'cr/dr', 'd/c', 'transaction type'])), None)
        ref_col = next((c for c in df.columns if is_match(c, ['ref', 'chq', 'utr', 'transaction id', 'id'])), None)
        bal_col = next((c for c in df.columns if is_match(c, ['balance', 'closing balance', 'bal', 'running balance', 'avail bal'])), None)

        def to_float(val):
            if pd.isna(val):
                return None
            s = str(val).replace(',', '').strip()
            if not s or s == '-' or s.lower() == 'nan':
                return None
            try:
                return float(s)
            except ValueError:
                return None

        for idx, row in df.iterrows():
            try:
                date_val = str(row[date_col]) if date_col and pd.notna(row[date_col]) else datetime.now().strftime("%Y-%m-%d")
                parsed_date = parse_date(date_val)
                
                raw_desc = str(row[desc_col]).strip() if desc_col and pd.notna(row[desc_col]) else "Statement Transaction"
                if raw_desc.lower() == 'nan' or not raw_desc:
                    raw_desc = "Statement Transaction"
                    
                clean_desc, payee_merchant, extracted_ref, detected_payment_type = extract_transaction_details(raw_desc)
                
                row_ref = str(row[ref_col]).strip() if ref_col and pd.notna(row[ref_col]) else ""
                final_ref = row_ref if row_ref and row_ref.lower() != 'nan' else extracted_ref
                
                balance_val = to_float(row[bal_col]) if bal_col else None
                
                amount = 0.0
                tx_type = "DEBIT"
                
                if debit_col and credit_col:
                    d_amt = to_float(row[debit_col]) or 0.0
                    c_amt = to_float(row[credit_col]) or 0.0
                    
                    if d_amt > 0:
                        amount = d_amt
                        tx_type = "DEBIT"
                    elif c_amt > 0:
                        amount = c_amt
                        tx_type = "CREDIT"
                    else:
                        continue
                elif amt_col:
                    parsed_amt = to_float(row[amt_col])
                    if parsed_amt is None:
                        continue
                        
                    amount = abs(parsed_amt)
                    
                    if type_col and pd.notna(row[type_col]):
                        t_str = str(row[type_col]).upper()
                        if 'CR' in t_str or 'CREDIT' in t_str:
                            tx_type = "CREDIT"
                        else:
                            tx_type = "DEBIT"
                    else:
                        if parsed_amt < 0:
                            tx_type = "DEBIT"
                        else:
                            _, tx_type = infer_category_and_type(raw_desc, None, amount)
                else:
                    continue
                    
                if amount <= 0:
                    continue
                    
                category, tx_type = infer_category_and_type(raw_desc, tx_type, amount)
                
                transactions.append({
                    "date": parsed_date,
                    "amount": round(amount, 2),
                    "description": clean_desc,
                    "payee_merchant": payee_merchant,
                    "reference_id": final_ref,
                    "balance": round(balance_val, 2) if balance_val is not None else None,
                    "paymentType": detected_payment_type,
                    "transaction_type": tx_type,
                    "category": category
                })
            except Exception:
                continue

    elif ext == 'pdf':
        try:
            import pdfplumber
            with pdfplumber.open(file_obj) as pdf:
                full_text = ""
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        full_text += text + "\n"
                        
            lines = full_text.split('\n')
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                date_match = re.search(r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{1,2}\s+[A-Za-z]{3}\s+\d{2,4})', line)
                amt_matches = re.findall(r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', line)
                
                if date_match and amt_matches:
                    p_date = parse_date(date_match.group(1))
                    amounts = []
                    for a in amt_matches:
                        try:
                            val = float(a.replace(',', ''))
                            if val > 0:
                                amounts.append(val)
                        except ValueError:
                            pass
                    if not amounts:
                        continue
                    
                    amount = max(amounts)
                    
                    desc = line
                    desc = re.sub(r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{1,2}\s+[A-Za-z]{3}\s+\d{2,4})', '', desc)
                    desc = re.sub(r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', '', desc).strip()
                    if len(desc) < 3:
                        desc = "PDF Transaction"
                        
                    clean_desc, payee_merchant, extracted_ref, detected_payment_type = extract_transaction_details(desc)
                    
                    is_credit = any(kw in line.lower() for kw in ['cr', 'credit', 'received', 'credited', 'deposit'])
                    tx_type = "CREDIT" if is_credit else "DEBIT"
                    category, tx_type = infer_category_and_type(desc, tx_type, amount)
                    
                    transactions.append({
                        "date": p_date,
                        "amount": round(amount, 2),
                        "description": clean_desc,
                        "payee_merchant": payee_merchant,
                        "reference_id": extracted_ref,
                        "balance": None,
                        "paymentType": detected_payment_type,
                        "transaction_type": tx_type,
                        "category": category
                    })
        except Exception:
            pass

    return transactions
