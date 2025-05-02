# Charset Converter

A Python utility to convert files from unknown-8bit charset (or other encodings) to UTF-8.

## Overview

This script is designed to solve the problem of processing files exported by the Japan team that use non-UTF-8 encodings (often identified as "unknown-8bit" or other Japanese encodings like Shift-JIS). It automatically detects the source encoding and converts the file to UTF-8 for proper processing.

## Features

- Automatic encoding detection using the `chardet` library
- Fallback to common Japanese encodings if detection confidence is low
- Handles various Japanese encodings (Shift-JIS, EUC-JP, ISO-2022-JP, CP932)
- Creates a new file with UTF-8 encoding, preserving the original file

## Requirements

- Python 3.x
- `chardet` library

## Installation

1. Create a virtual environment (recommended):
   ```
   python3 -m venv charset_converter_env
   source charset_converter_env/bin/activate  # On Windows: charset_converter_env\Scripts\activate
   ```

2. Install the required package:
   ```
   pip install chardet
   ```

## Usage

```
python charset_converter.py input_file [output_file]
```

### Arguments

- `input_file`: Path to the file you want to convert
- `output_file` (optional): Path where the converted file will be saved. If not specified, the script will create a file with the same name as the input file but with "_utf8" appended before the extension.

### Examples

Convert a file and let the script name the output file:
```
python charset_converter.py "Evelyn Raku export.csv"
```
This will create a file named "Evelyn Raku export_utf8.csv"

Convert a file with a specific output name:
```
python charset_converter.py "Evelyn Raku export.csv" "converted_file.csv"
```

## How It Works

1. The script first attempts to detect the encoding of the input file using the `chardet` library.
2. If the detection confidence is high (>70%), it uses the detected encoding.
3. If the confidence is low, it tries a list of common Japanese encodings (Shift-JIS, EUC-JP, ISO-2022-JP, CP932).
4. It reads the file with the detected or specified encoding and writes the content to a new file with UTF-8 encoding.

## Troubleshooting

If the script fails to convert a file:

1. Try specifying the encoding manually if you know it:
   - Modify the script to add the known encoding to the beginning of the `encodings_to_try` list
2. Check if the file is already in UTF-8 format
3. Ensure the file is not corrupted or binary

## License

This script is provided as-is for internal use.