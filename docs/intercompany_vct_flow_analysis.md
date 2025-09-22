# Intercompany Code Flow Analysis: CSV to BC API Call
## End-to-End Process for ShortcutDimCode3 VCT Assignment

### Executive Summary

This document traces the complete end-to-end process showing how intercompany code handling flows from raw CSV input through JSON conversion to Business Central API calls, specifically tracking how **"ShortcutDimCode3" gets set to "VCT"**.

**Key Finding**: The ShortcutDimCode3 field gets set to "VCT" in **normal journal credit lines** when processing transactions with non-VCT cost centers. This is different from VCT responsibility entries where ShortcutDimCode3 contains the original cost center code.

---

## Process Flow Overview

```
CSV Input → JSON Conversion → Business Logic → VCT Responsibility → BC API Call
     ↓             ↓              ↓                ↓                   ↓
[Raw Data]    [Structured]   [V-VC00048        [ShortcutDimCode3]  [API Payload]
              [JSON]          Detection]        [= Cost Center]     [with VCT]
```

---

## 1. CSV Input Structure

**File Reference**: `/tests/test_unified_input.csv:1-3`

### CSV Column Mapping (Japanese Headers)
```csv
伝票番号,伝票日付,外部証憑番号,摘要,借方勘定科目,借方金額,借方通貨,貸方勘定科目,貸方金額,貸方通貨,部門,申請者コード,仕入先コード,Receipt/Invoice Note(明細),自由項目,備考
```

### Key Fields for VCT Processing
- **部門 (Department)**: Contains cost center code (e.g., "VCP.1234", "VCT.1111")
- **仕入先コード (Vendor Code)**: Contains vendor identifier (e.g., "V-VC00048")
- **伝票番号 (Voucher Number)**: Transaction identifier

### Sample CSV Data
```csv
APA-0000552-1,2025/01/15,APA-0000552-1,Office supplies,62100-10,5000,NTD,V-VC00048,5000,NTD,VCP.1234,EMP001,V-VC00048,Stationery purchase,Office,Office supplies payment
VCT-0000456,2025/01/30,VCT-0000456,VCT department entry,61200-10,1500,NTD,V-VC00048,1500,NTD,VCT.1111,EMP007,V-VC00048,VCT expense,VCT,VCT payment
```

---

## 2. CSV to JSON Conversion Process

**File Reference**: `/core/csv_to_json_converter.py:1-50`

### Conversion Logic
1. **CSV Reader**: Processes Japanese CSV with proper encoding (UTF-8)
2. **Header Mapping**: Maps Japanese column names to English field names
3. **Data Transformation**: Converts CSV rows to structured JSON objects
4. **Currency Processing**: Handles currency codes and amounts with decimal precision

### JSON Structure Output
```json
{
  "voucher_no": "APA-0000552-1",
  "department": "VCP.1234",
  "vendor_code": "V-VC00048",
  "gl_account": "Vendor",
  "amount": 5000,
  "currency": "NTD"
}
```

---

## 3. Business Logic: V-VC00048 Intercompany Detection

**File Reference**: `/core/process_japan_exports.py:590-599`

### Detection Logic
```python
# NEW CODE: Handle V-VC00048 mapping for non-VCT cost centers
if account_no == "V-VC00048":
    # Extract cost center from department code (first 3 characters)
    department = entry_data.get("department", "")
    cost_center = department[:3] if department else ""

    # If cost center is not VCT, change vendor code to VCT
    if cost_center and cost_center != "VCT":
        logger.info(f"Mapping vendor V-VC00048 to VCT for non-VCT cost center {cost_center}")
        account_no = "VCT"
```

### Business Rules
1. **Intercompany Detection**: System identifies V-VC00048 vendor transactions
2. **Cost Center Extraction**: Takes first 3 characters of department field
3. **VCT Mapping**: Non-VCT cost centers trigger VCT responsibility entries
4. **Consolidation Logic**: VCT cost centers are processed normally

### Department Code Processing
**File Reference**: `/core/process_japan_exports.py:576-577`
```python
# Transform department_code for Vendor accounts
if original_dept_code and len(original_dept_code) >= 3:
    # Take first 3 characters and append .9999
    shortcut_dim_2_code = original_dept_code[:3] + ".9999"
```

---

## 4. ShortcutDimCode3 Assignment Logic - **THE KEY DISCOVERY**

**File Reference**: `/core/process_japan_exports.py:710-733`

### Critical Logic for ShortcutDimCode3 = "VCT"

```python
# Determine intercompany code for ShortcutDimCode3
intercompany_code = ""

# For debit lines with account 18600-10, set intercompany code to the original cost center
if entry_type == "debit" and account_no == "18600-10":
    # Extract cost center from department code (first 3 characters)
    department = entry_data.get("department", "")
    intercompany_code = department[:3] if department else ""

# For credit lines, check if cost center is not VCT
elif entry_type == "credit":
    # Get vendor code
    vendor_code = entry_data.get("vendor_code", "")

    # Extract cost center from department code (first 3 characters)
    department = entry_data.get("department", "")
    cost_center = department[:3] if department else ""

    # If cost center is not VCT, set intercompany code to "VCT"
    if cost_center and cost_center != "VCT":
        intercompany_code = "VCT"
```

### **Why Log Shows ShortcutDimCode3 = "VCT"**

The log entries showing `"ShortcutDimCode3": "VCT"` are from **normal journal credit lines**, not VCT responsibility entries.

**Logic**:
1. **Normal Credit Lines**: When department = "VCP.1234" (cost_center = "VCP" ≠ "VCT") → ShortcutDimCode3 = "VCT"
2. **VCT Responsibility Lines**: ShortcutDimCode3 = original cost center ("VCP")

### Two Different Assignment Paths

| Line Type | Condition | ShortcutDimCode3 Value | Purpose |
|-----------|-----------|----------------------|---------|
| Normal Credit | Cost center ≠ VCT | "VCT" | Intercompany tracking |
| Normal Debit | Account = 18600-10 | Original cost center | Cost center tracking |
| VCT Responsibility Debit | VCT entry creation | Original cost center | Responsibility tracking |
| VCT Responsibility Credit | VCT entry creation | "" (empty) | Credit line |

---

## 5. BC API Payload Generation

### VCT Responsibility Debit Line
**File Reference**: `/core/process_japan_exports.py:1235-1262`
```json
{
    "Journal_Template_Name": "PURCHASES",
    "Journal_Batch_Name": "PURCHASE",
    "Document_Type": "Invoice",
    "Account_Type": "G/L Account",
    "Account_No": "18600-10",
    "Shortcut_Dimension_1_Code": "VCT",
    "Shortcut_Dimension_2_Code": "VCT.9999",
    "ShortcutDimCode3": "VCP",  // ← Original cost center from CSV department field
    "ShortcutDimCode4": "",
    "Amount": 5000
}
```

### VCT Responsibility Credit Line
**File Reference**: `/core/process_japan_exports.py:1267-1285`
```json
{
    "Journal_Template_Name": "PURCHASES",
    "Journal_Batch_Name": "PURCHASE",
    "Document_Type": "Invoice",
    "Account_Type": "Vendor",
    "Account_No": "V-VC00048",
    "Shortcut_Dimension_1_Code": "VCT",
    "Shortcut_Dimension_2_Code": "VCT.9999",
    "ShortcutDimCode3": "",  // ← Empty for credit line
    "Amount": -5000
}
```

---

## 6. Log Evidence Analysis

### Pattern from API Integration Log
**File Reference**: `/erp_api_integration.log:492-496, 1013-1017`

**VCT Assignment Pattern**:
```log
"Shortcut_Dimension_2_Code": "VCP.9999",
"ShortcutDimCode3": "VCT",
"ShortcutDimCode4": "10099",
```

**Non-VCT Assignment Pattern**:
```log
"Shortcut_Dimension_2_Code": "VCP.1695G",
"ShortcutDimCode3": "",
"ShortcutDimCode4": "10099",
```

### Key Observation
- **ShortcutDimCode3 = "VCT"** when **Shortcut_Dimension_2_Code = "VCP.9999"**
- **ShortcutDimCode3 = ""** when **Shortcut_Dimension_2_Code ≠ "VCP.9999"**

---

## 7. Complete Data Flow Trace

### Step-by-Step Process

1. **CSV Input Processing**
   - Source: `APA-0000552-1,...,V-VC00048,...,VCP.1234,...`
   - Department: `VCP.1234`
   - Vendor: `V-VC00048`

2. **JSON Conversion**
   - Maps to: `{"department": "VCP.1234", "vendor_code": "V-VC00048"}`

3. **Intercompany Detection**
   - Extracts cost center: `VCP` (first 3 chars of `VCP.1234`)
   - Triggers VCT responsibility: `VCP != VCT`

4. **VCT Entry Creation**
   - Creates debit line with: `ShortcutDimCode3 = "VCP"`
   - Sets dimension codes: `Shortcut_Dimension_1_Code = "VCT"`, `Shortcut_Dimension_2_Code = "VCT.9999"`

5. **BC API Call**
   - Posts VCT responsibility entries to Business Central
   - ShortcutDimCode3 contains original cost center for intercompany tracking

---

## 8. Business Logic Summary

### When ShortcutDimCode3 Gets Set to VCT

**Condition**: When processing V-VC00048 vendor transactions with non-VCT cost centers

**Process**:
1. System detects V-VC00048 vendor code
2. Extracts cost center from department field (first 3 characters)
3. If cost center ≠ "VCT", creates VCT responsibility entries
4. Sets ShortcutDimCode3 to the original cost center for intercompany tracking

### Why This Logic Exists

This implements intercompany responsibility tracking where:
- VCT takes responsibility for expenses incurred by other cost centers
- Original cost center is preserved in ShortcutDimCode3 for audit and reporting
- Enables proper intercompany billing and cost allocation

---

## 9. File Reference Map

| Component | File Location | Key Functions |
|-----------|---------------|---------------|
| CSV Processing | `/core/csv_to_json_converter.py` | CSV to JSON conversion |
| Intercompany Logic | `/core/process_japan_exports.py:590-599` | V-VC00048 detection |
| VCT Responsibility | `/core/process_japan_exports.py:1145-1285` | VCT entry creation |
| Dimension Mapping | `/core/process_japan_exports.py:1249` | ShortcutDimCode3 assignment |
| Column Mapping | `/Data/VicOneERPAPI/Column Mapping.txt` | Field structure |
| Test Data | `/tests/test_unified_input.csv` | Sample CSV format |

---

## 10. Configuration and Constants

### API Configuration
```python
JOURNAL_TEMPLATE_NAME = "PURCHASES"
JOURNAL_BATCH_NAME = "PURCHASE"
DOCUMENT_TYPE = "Invoice"
VCT_ACCOUNT_NO = "18600-10"
```

### Dimension Structure
- **Shortcut_Dimension_1_Code**: Company/Region Code (VCT)
- **Shortcut_Dimension_2_Code**: Department Code (VCT.9999)
- **ShortcutDimCode3**: Intercompany/Cost Center Code (Original cost center)
- **ShortcutDimCode4**: Employee/Applicant Code

---

This analysis provides a complete trace of how CSV data flows through the system to generate BC API calls with proper intercompany dimension coding, specifically showing how ShortcutDimCode3 gets populated with cost center information for VCT responsibility tracking.