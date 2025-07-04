# CSV Header Fix Functionality

## Overview

The `charset_converter.py` script has been enhanced with functionality to automatically detect and fix problematic CSV headers that contain corrupted characters due to encoding issues. This is particularly useful for Raku export CSV files where Japanese characters may be corrupted during the export process.

## Problem Description

When CSV files are exported from systems like Raku with improper encoding handling, Japanese characters in headers may be corrupted and replaced with "?" characters. For example:

**Problematic Headers:**
```
勘定奉行：伝票区切,G/L Account,仕訳日,申請日,仕訳データ生成日,伝票No.,借方：勘定科目：会計連携?目,借方：補?科目：会計連携?目,...
,Vendor,仕訳日,申請日,仕訳データ生成日,伝票No.,,,貸方：勘定科目：会計連携?目,貸方：補?科目：会計連携?目,...
```

**Fixed Headers:**
```
勘定奉行：伝票区切,G/L Account,仕訳日,申請日,仕訳データ生成日,伝票No.,借方：勘定科目：会計連携項目,借方：補助科目：会計連携項目,...
,Vendor,仕訳日,申請日,仕訳データ生成日,伝票No.,,,貸方：勘定科目：会計連携項目,貸方：補助科目：会計連携項目,...
```

## Usage

### Option 1: Fix headers only (file already UTF-8)
```bash
python charset_converter.py input.utf8.csv --headers-only --verbose
```

### Option 2: Convert charset and fix headers in one step
```bash
python charset_converter.py input.csv --fix-headers --verbose
```

### Option 3: Convert with specific encoding and fix headers
```bash
python charset_converter.py input.csv output.csv -e shift_jis --fix-headers --verbose
```

## Command Line Options

- `--fix-headers`: Fix problematic CSV headers after charset conversion
- `--headers-only`: Only fix headers without charset conversion (file must be UTF-8)
- `-v, --verbose`: Print detailed information about header replacement

## Supported Patterns

Currently supports the following problematic header patterns:

### Pattern: raku_export_pattern_1
**Description:** Raku export CSV with corrupted Japanese characters in headers

**Detection Criteria:**
- Contains "?" characters in header context with Japanese characters
- Contains specific patterns like "勘定奉行：伝票区切", "G/L Account", "会計連携?目", "フ?ー２"

**Replacements:**
- `会計連携?目` → `会計連携項目` (accounting linkage item)
- `補?科目` → `補助科目` (auxiliary account)
- `?担?門` → `負担部門` (cost center)
- `フ?ー２` → `フリー２` (free field 2)

## Output Files

When using `--headers-only` mode without specifying an output file, the script creates a new file with `_headers_fixed` appended to the filename:

```
input: TEO.utf8.csv
output: TEO.utf8_headers_fixed.csv
```

When using `--fix-headers` mode, headers are fixed in the converted UTF-8 file.

## Example Output

```bash
$ python charset_converter.py examples/0623/TEO.utf8.csv --headers-only --verbose

Headers-only mode: Fixing CSV headers without charset conversion
Detected problematic header pattern: raku_export_pattern_1
Description: Raku export CSV with corrupted Japanese characters in headers
Original headers:
  Line 1: 勘定奉行：伝票区切,G/L Account,仕訳日,申請日,仕訳データ生成日,伝票No.,借方：勘定科目：会計連携?目,借方：補?科目：会計連携?目,...
  Line 2: ,Vendor,仕訳日,申請日,仕訳データ生成日,伝票No.,,,貸方：勘定科目：会計連携?目,貸方：補?科目：会計連携?目,...
Replaced with correct headers:
  Line 1: 勘定奉行：伝票区切,G/L Account,仕訳日,申請日,仕訳データ生成日,伝票No.,借方：勘定科目：会計連携項目,借方：補助科目：会計連携項目,...
  Line 2: ,Vendor,仕訳日,申請日,仕訳データ生成日,伝票No.,,,貸方：勘定科目：会計連携項目,貸方：補助科目：会計連携項目,...
Headers fixed and saved to: examples/0623/TEO.utf8_headers_fixed.csv
Headers successfully fixed and saved to: examples/0623/TEO.utf8_headers_fixed.csv
```

## Integration with JSON Conversion

After fixing the headers, the CSV file can be successfully converted to JSON format without issues:

```bash
# Fix headers first
python charset_converter.py problematic.csv --headers-only --verbose

# Then convert to JSON
python core/csv_to_json_converter.py problematic_headers_fixed.csv
```

## Adding New Patterns

To add support for new problematic header patterns, update the `KNOWN_HEADER_REPLACEMENTS` dictionary in `charset_converter.py`:

```python
KNOWN_HEADER_REPLACEMENTS = {
    'new_pattern_name': {
        'description': 'Description of the pattern',
        'header_lines': [
            'Correct first header line',
            'Correct second header line'
        ]
    }
}
```

Then update the `detect_problematic_headers()` function to detect the new pattern.

## Technical Details

- The script reads the first two lines of the CSV file to detect problematic patterns
- Pattern detection is based on the presence of "?" characters combined with Japanese characters and specific text patterns
- When a pattern is detected, the entire first two lines are replaced with the correct headers
- The rest of the file content remains unchanged
- All operations preserve the UTF-8 encoding of the file
