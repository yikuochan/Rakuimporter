---
title: Power Importer - ERP Integration System
version: 1.0
created: 2025-01-14
last_updated: 2025-01-14
status: Production Ready
---

# Power Importer Project Brief

## Project Overview
Power Importer is a Python-based financial data integration system designed to streamline the import of financial data from various sources into Microsoft Dynamics 365 Business Central. The system specializes in processing CSV files from Japanese sources, handling complex character encoding, currency conversion, and API integration challenges.

## Core Purpose
Transform raw CSV financial data (particularly from Japanese systems) into structured journal entries within Microsoft Dynamics 365 Business Central, ensuring data integrity, proper encoding, and accurate currency conversion throughout the process.

## Key Problems Solved
1. **Character Encoding Issues**: Handles Japanese text encoding (Shift-JIS, EUC-JP) conversion to UTF-8
2. **Data Structure Transformation**: Converts flat CSV data to structured JSON for API consumption
3. **Currency Conversion**: Manages multi-currency transactions with real-time exchange rates
4. **ERP Integration**: Automates journal entry creation in Business Central via API
5. **Error Handling**: Provides robust error recovery and detailed logging
6. **Performance Optimization**: Implements rate limiting and entry consolidation

## Primary Stakeholders
- **Finance Teams**: Primary users who need to import financial data
- **IT Operations**: Responsible for system deployment and maintenance
- **Business Central Administrators**: Manage ERP system integration
- **Japanese Subsidiaries**: Source of financial data requiring special handling

## Success Criteria
- ✅ Accurate conversion of Japanese-encoded CSV files
- ✅ Successful posting of journal entries to Business Central
- ✅ Balanced debit/credit entries with proper currency conversion
- ✅ Reduced manual data entry and processing time
- ✅ Comprehensive audit trail and error reporting
- ✅ Production-ready performance and reliability

## Project Scope
**In Scope:**
- CSV file processing and encoding conversion
- JSON transformation and data validation
- Currency conversion and exchange rate management
- Business Central API integration
- Error handling and reporting
- Rate limiting and performance optimization

**Out of Scope:**
- Direct database integration (API-only approach)
- Real-time data synchronization
- User interface development
- Custom Business Central modifications

## Current Status
**Production Ready** - The system has successfully completed multiple phases of development and optimization, including production endpoint configuration, VCT responsibility consolidation, and comprehensive bug fixes.
