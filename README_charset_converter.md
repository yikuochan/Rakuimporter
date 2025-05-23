# Charset Converter

A Python utility to convert files from various charsets to UTF-8.

## Overview

This script is designed to solve the problem of processing files that use non-UTF-8 encodings (such as "unknown-8bit", Windows-1254, SHIFT_JIS, and other encodings). It automatically detects the source encoding and converts the file to UTF-8 for proper processing.

## Features

- Automatic encoding detection using the `chardet` library
- Option to specify source encoding directly
- Fallback to common encodings if detection confidence is low
- Handles various encodings:
  - Japanese encodings (Shift-JIS, EUC-JP, ISO-2022-JP, CP932)
  - Turkish encodings (Windows-1254, ISO-8859-9)
  - Other common encodings (Windows-1252, ISO-8859-1, UTF-16, GB2312, GBK, Big5)
- Creates a new file with UTF-8 encoding, preserving the original file
- Shows a sample of the converted text to verify correct conversion
- Validates conversion quality and selects the best encoding
- Option to list all available encodings
- Japanese mode to prioritize Japanese encodings
- Force mode to override validation checks

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
python charset_converter.py input_file [output_file] [options]
```

### Arguments

- `input_file`: Path to the file you want to convert
- `output_file` (optional): Path where the converted file will be saved. If not specified, the script will create a file with the same name as the input file but with "_utf8" appended before the extension.

### Options

- `-e, --encoding ENCODING`: Source encoding to try first. Use this when you know the encoding of the file.
- `-f, --force`: Force conversion even if validation fails. Use this when you want to use a specific encoding regardless of validation results.
- `--japanese`: Optimize for Japanese text by trying Japanese encodings first.
- `--list-encodings`: List all available encodings and exit.

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

Convert a file with a known encoding (Windows-1254):
```
python charset_converter.py "turkish_file.csv" --encoding windows-1254
```

Convert a file with a known encoding (SHIFT_JIS):
```
python charset_converter.py "japanese_file.csv" --encoding shift_jis
```

Force conversion with a specific encoding even if validation fails:
```
python charset_converter.py "problem_file.csv" --encoding windows-1254 --force
```

Optimize for Japanese text:
```
python charset_converter.py "japanese_file.csv" --japanese
```

List all available encodings:
```
python charset_converter.py --list-encodings
```

## How It Works

1. If a source encoding is specified with `--encoding`, the script tries that encoding first.
2. The script attempts to detect the encoding of the input file using the `chardet` library.
3. If the detection confidence is high (>70%), it uses the detected encoding.
4. If the confidence is low, it tries a comprehensive list of common encodings:
   - Japanese encodings (Shift-JIS, EUC-JP, ISO-2022-JP, CP932)
   - Turkish encodings (Windows-1254, ISO-8859-9)
   - Other common encodings (Windows-1252, ISO-8859-1, UTF-16, GB2312, GBK, Big5)
5. For each encoding, it:
   - Reads the file and converts it to UTF-8
   - Validates the conversion quality by checking for problematic characters
   - Calculates a quality score based on the percentage of valid characters
6. It selects the encoding that produces the highest quality conversion.
7. It displays a sample of the converted text to help verify the conversion was successful.

## Troubleshooting

If the script fails to convert a file:

1. Try specifying the encoding manually if you know it:
   - Use the `--encoding` option to specify the encoding directly
   - Example: `python charset_converter.py input_file --encoding windows-1254`

2. If you know the encoding but the script rejects it due to validation:
   - Use the `--force` option to override validation checks
   - Example: `python charset_converter.py input_file --encoding windows-1254 --force`

3. For Japanese files:
   - Use the `--japanese` option to prioritize Japanese encodings
   - Example: `python charset_converter.py input_file --japanese`

4. Check if the file is already in UTF-8 format

5. Ensure the file is not corrupted or binary

6. Use the `--list-encodings` option to see all available encodings that you can try

## License

This script is provided as-is for internal use.
