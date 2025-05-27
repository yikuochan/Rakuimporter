#!/usr/bin/env python3
"""
Script to analyze Document_No discrepancies between request and response in BC API logs.
This script identifies cases where the Document_No in the request differs from the Document_No in the response.
"""

import re
import json
from datetime import datetime
import os
import sys
from collections import defaultdict

def extract_json_from_log_line(line):
    """Extract JSON content from a log line."""
    try:
        # Find the JSON part of the line (after the colon)
        json_start = line.find('{')
        if json_start == -1:
            return None
        
        json_str = line[json_start:]
        # Parse the JSON
        return json.loads(json_str)
    except json.JSONDecodeError:
        return None

def extract_json_from_log_section(lines, start_index):
    """
    Extract and parse JSON content from log lines starting at a specific index.
    
    Args:
        lines: List of log lines
        start_index: Starting index in the lines list
        
    Returns:
        Tuple of (parsed_json_object, end_index) or (None, start_index) if parsing fails
    """
    # Find the line with the opening brace
    json_start_idx = start_index
    while json_start_idx < len(lines) and '{' not in lines[json_start_idx]:
        json_start_idx += 1
    
    if json_start_idx >= len(lines):
        return None, start_index
    
    # Extract JSON content
    json_content = ""
    i = json_start_idx
    brace_count = 0
    started = False
    
    while i < len(lines):
        line = lines[i]
        
        # Count opening and closing braces to track JSON structure
        for char in line:
            if char == '{':
                brace_count += 1
                started = True
            elif char == '}':
                brace_count -= 1
        
        json_content += line
        
        # If we've found the end of the JSON object, break
        if started and brace_count <= 0:
            break
        
        i += 1
    
    # Try to extract just the JSON part
    try:
        # Find the first opening brace and last closing brace
        start_pos = json_content.find('{')
        end_pos = json_content.rfind('}') + 1
        
        if start_pos != -1 and end_pos > start_pos:
            json_str = json_content[start_pos:end_pos]
            json_obj = json.loads(json_str)
            return json_obj, i + 1
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        print(f"Problematic JSON: {json_content[:100]}...")
    
    return None, start_index

def analyze_document_no_discrepancies(log_file_path):
    """
    Analyze the log file to find Document_No discrepancies between requests and responses.
    
    Args:
        log_file_path: Path to the log file
        
    Returns:
        A tuple containing (discrepancies, statistics)
    """
    # Track request-response pairs
    requests = []
    responses = []
    discrepancies = []
    
    # Regular expressions to identify request and response lines
    request_pattern = re.compile(r'INFO - Request body for journal line:')
    response_pattern = re.compile(r'INFO - API response body:')
    
    # Parse log file to extract requests and responses
    current_timestamp = None
    with open(log_file_path, 'r', encoding='utf-8', errors='ignore') as file:
        lines = file.readlines()
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Extract timestamp
            timestamp_match = re.match(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})', line)
            if timestamp_match:
                current_timestamp = timestamp_match.group(1)
            
            # Check if this is a request line
            if request_pattern.search(line):
                json_obj, next_i = extract_json_from_log_section(lines, i)
                if json_obj and 'Document_No' in json_obj:
                    requests.append({
                        'timestamp': current_timestamp,
                        'Document_No': json_obj['Document_No'],
                        'External_Document_No': json_obj.get('External_Document_No', ''),
                        'full_data': json_obj
                    })
                i = next_i
            
            # Check if this is a response line
            elif response_pattern.search(line):
                json_obj, next_i = extract_json_from_log_section(lines, i)
                if json_obj and 'Document_No' in json_obj:
                    responses.append({
                        'timestamp': current_timestamp,
                        'Document_No': json_obj['Document_No'],
                        'External_Document_No': json_obj.get('External_Document_No', ''),
                        'full_data': json_obj
                    })
                i = next_i
            else:
                i += 1
    
    print(f"Found {len(requests)} requests and {len(responses)} responses")
    
    # Match requests with responses based on External_Document_No and proximity
    matched_pairs = []
    
    # If we have the same number of requests and responses, assume they match in order
    if len(requests) == len(responses):
        matched_pairs = list(zip(requests, responses))
    else:
        print(f"Warning: Number of requests ({len(requests)}) doesn't match number of responses ({len(responses)})")
        
        # Try to match based on External_Document_No and timestamps
        used_responses = set()
        
        for req in requests:
            best_match = None
            min_time_diff = float('inf')
            
            for i, resp in enumerate(responses):
                if i in used_responses:
                    continue
                
                # Check if External_Document_No matches
                if req['External_Document_No'] == resp['External_Document_No']:
                    # Calculate time difference if timestamps are available
                    if req['timestamp'] and resp['timestamp']:
                        req_time = datetime.strptime(req['timestamp'], '%Y-%m-%d %H:%M:%S,%f')
                        resp_time = datetime.strptime(resp['timestamp'], '%Y-%m-%d %H:%M:%S,%f')
                        time_diff = abs((resp_time - req_time).total_seconds())
                        
                        if time_diff < min_time_diff:
                            min_time_diff = time_diff
                            best_match = i
            
            if best_match is not None:
                matched_pairs.append((req, responses[best_match]))
                used_responses.add(best_match)
        
        # If we still have unmatched requests, try to match them by proximity
        if len(matched_pairs) < min(len(requests), len(responses)):
            remaining_requests = [req for req in requests if not any(pair[0] == req for pair in matched_pairs)]
            remaining_responses = [resp for i, resp in enumerate(responses) if i not in used_responses]
            
            # Match the remaining by order
            additional_pairs = list(zip(remaining_requests, remaining_responses))
            matched_pairs.extend(additional_pairs)
    
    # Identify discrepancies
    for req, resp in matched_pairs:
        if req['Document_No'] != resp['Document_No']:
            discrepancies.append({
                'timestamp': req['timestamp'],
                'request_doc_no': req['Document_No'],
                'response_doc_no': resp['Document_No'],
                'external_doc_no': req['External_Document_No'],
                'request_data': req['full_data'],
                'response_data': resp['full_data']
            })
    
    # Calculate statistics
    total_requests = len(matched_pairs)
    total_discrepancies = len(discrepancies)
    discrepancy_percentage = (total_discrepancies / total_requests * 100) if total_requests > 0 else 0
    
    # Analyze patterns in discrepancies
    doc_no_prefixes = defaultdict(int)
    for disc in discrepancies:
        prefix = re.match(r'([A-Za-z]+-\d+)', disc['request_doc_no'])
        if prefix:
            doc_no_prefixes[prefix.group(1)] += 1
    
    statistics = {
        'total_requests': total_requests,
        'total_discrepancies': total_discrepancies,
        'discrepancy_percentage': discrepancy_percentage,
        'affected_prefixes': dict(doc_no_prefixes)
    }
    
    return discrepancies, statistics

def generate_report(discrepancies, statistics, output_file=None):
    """
    Generate a report of the discrepancies found.
    
    Args:
        discrepancies: List of discrepancy dictionaries
        statistics: Dictionary of statistics
        output_file: Optional file path to write the report to
    """
    report = []
    
    # Add summary statistics
    report.append("# Document_No Discrepancy Analysis Report")
    report.append(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    report.append("## Summary Statistics")
    report.append(f"- Total API requests analyzed: {statistics['total_requests']}")
    report.append(f"- Total discrepancies found: {statistics['total_discrepancies']}")
    report.append(f"- Discrepancy percentage: {statistics['discrepancy_percentage']:.2f}%\n")
    
    # Add affected prefixes
    report.append("## Affected Document_No Prefixes")
    if statistics['affected_prefixes']:
        for prefix, count in sorted(statistics['affected_prefixes'].items(), key=lambda x: x[1], reverse=True):
            report.append(f"- {prefix}: {count} occurrences")
    else:
        report.append("- No specific prefix patterns identified")
    report.append("")
    
    # Add detailed discrepancies
    report.append("## Detailed Discrepancies")
    if discrepancies:
        for i, disc in enumerate(discrepancies, 1):
            report.append(f"### Discrepancy {i}")
            report.append(f"- Timestamp: {disc['timestamp']}")
            report.append(f"- External Document No: {disc['external_doc_no']}")
            report.append(f"- Request Document No: {disc['request_doc_no']}")
            report.append(f"- Response Document No: {disc['response_doc_no']}")
            report.append("")
    else:
        report.append("No discrepancies found.")
    
    # Print report to console
    print("\n".join(report))
    
    # Write report to file if specified
    if output_file:
        with open(output_file, 'w') as f:
            f.write("\n".join(report))
        print(f"\nReport written to {output_file}")
    
    # Also save the raw discrepancy data as JSON for further analysis
    if discrepancies and output_file:
        json_output = os.path.splitext(output_file)[0] + ".json"
        with open(json_output, 'w') as f:
            json.dump(discrepancies, f, indent=2)
        print(f"Raw discrepancy data written to {json_output}")

def main():
    """Main function to run the analysis."""
    if len(sys.argv) < 2:
        print("Usage: python analyze_document_no_discrepancies.py <log_file_path> [output_report_path]")
        sys.exit(1)
    
    log_file_path = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "document_no_discrepancy_report.md"
    
    if not os.path.exists(log_file_path):
        print(f"Error: Log file '{log_file_path}' not found.")
        sys.exit(1)
    
    print(f"Analyzing log file: {log_file_path}")
    discrepancies, statistics = analyze_document_no_discrepancies(log_file_path)
    generate_report(discrepancies, statistics, output_file)

if __name__ == "__main__":
    main()
