---
title: Product Context - Business Requirements and User Experience
version: 1.0
created: 2025-01-14
last_updated: 2025-01-14
---

# Product Context

## Business Problem
Financial teams at Japanese subsidiaries need to import transaction data from local systems into Microsoft Dynamics 365 Business Central. The process involves complex challenges:

1. **Character Encoding Complexity**: Japanese financial systems export data in various encodings (Shift-JIS, EUC-JP) that cause data corruption when processed by standard tools
2. **Manual Data Entry**: Finance teams spend significant time manually entering journal entries, prone to human error
3. **Currency Conversion**: Multi-currency transactions require accurate exchange rate calculations and proper currency code handling
4. **Data Validation**: Need to ensure debit/credit balance and proper account mapping before posting to ERP
5. **Audit Trail**: Requirement for comprehensive logging and error reporting for financial compliance

## Target Users

### Primary Users
- **Finance Managers**: Need reliable, automated import process with proper validation
- **Accounting Staff**: Require detailed error reports and balance verification
- **Japanese Subsidiary Teams**: Source data providers who need encoding support

### Secondary Users
- **IT Operations**: Deploy and maintain the system
- **Business Central Administrators**: Monitor API integration and system health
- **Auditors**: Review transaction logs and error reports

## User Journey

### Current Manual Process (Before)
1. Export CSV from Japanese financial system
2. Manually convert encoding to avoid mojibake (character corruption)
3. Open CSV and manually create journal entries in Business Central
4. Manually verify debit/credit balance
5. Handle currency conversion calculations manually
6. Post entries one by one to Business Central

**Pain Points**: Time-consuming, error-prone, no audit trail, encoding issues

### Automated Process (After)
1. Place CSV file in designated folder
2. Run Power Importer command
3. System automatically:
   - Detects and converts character encoding
   - Transforms CSV to structured JSON
   - Validates data and balances
   - Converts currencies using current rates
   - Posts journal entries to Business Central
   - Generates comprehensive reports
4. Review success/error reports
5. Handle any exceptions flagged by the system

**Benefits**: 90% time reduction, error elimination, complete audit trail, automatic validation

## Business Rules

### Data Processing Rules
- **Encoding Detection**: Automatically detect Japanese encodings with confidence scoring
- **Currency Normalization**: Convert "台湾ドル" to "NTD", "円" to "JPY"
- **Account Mapping**: Different logic for G/L accounts vs. vendor accounts
- **Description Truncation**: Limit descriptions to 50 characters for API compatibility
- **Balance Verification**: Ensure debit/credit amounts balance within 0.01 tolerance

### Consolidation Rules
- **VCT Responsibility Entries**: Consolidate V-VC00048 vendor entries per voucher
- **Document Numbering**: Single document number per consolidated voucher
- **Individual Debits**: Preserve original amounts and cost centers
- **Consolidated Credits**: Single credit line with total amount

### Error Handling Rules
- **Unbalanced Entries**: Generate report but allow posting with user confirmation
- **Encoding Failures**: Retry with different encodings, force conversion if needed
- **API Failures**: Implement exponential backoff, retry up to 3 times
- **Rate Limiting**: Respect Business Central API limits with intelligent delays

## Success Metrics

### Operational Metrics
- **Processing Time**: Target <5 minutes for typical 100-entry file
- **Error Rate**: <1% of entries require manual intervention
- **API Success Rate**: >99% successful posts to Business Central
- **Encoding Success**: >95% automatic encoding detection accuracy

### Business Impact
- **Time Savings**: 90% reduction in manual data entry time
- **Error Reduction**: Eliminate manual calculation and entry errors
- **Audit Compliance**: Complete transaction trail with timestamps
- **Cost Savings**: Reduce finance team manual processing hours

## Integration Requirements

### Business Central Integration
- **Authentication**: OAuth 2.0 client credentials flow
- **API Endpoints**: General Journal Lines API
- **Rate Limiting**: Respect 5-second intervals between calls
- **Error Handling**: Handle 429 (rate limit) and 5xx (server) errors

### Exchange Rate Integration
- **Source**: Business Central Exchange Rate API
- **Caching**: Cache rates to minimize API calls
- **Cross-Currency**: Calculate cross-rates when direct rates unavailable
- **Fallback**: Use most recent rate if specific date unavailable

## Compliance and Security
- **Data Privacy**: No sensitive data stored locally after processing
- **Audit Trail**: Complete logging of all operations and decisions
- **Error Reporting**: Detailed reports for compliance review
- **Access Control**: Environment-based configuration for production/staging
