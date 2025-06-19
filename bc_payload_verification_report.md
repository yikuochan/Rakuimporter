# Business Central Payload Verification Report

**Total Tests:** 24
**Passed:** 23
**Failed:** 1
**Success Rate:** 95.8%

## Test Results

| Test Name | Status | Details |
|-----------|--------|----------|
| Basic Debit Line Creation | PASS | All required fields present |
| Basic Credit Line Creation | PASS | All required fields present |
| Currency Transform VCT-NTD | PASS | Expected: '', Got: '' |
| Currency Transform VCT-USD | PASS | Expected: 'R-USD', Got: 'R-USD' |
| Currency Transform VCP-PHP | PASS | Expected: '', Got: '' |
| Currency Transform VCP-USD | PASS | Expected: 'R-USD', Got: 'R-USD' |
| Currency Transform VCA-USD | PASS | Expected: '', Got: '' |
| Currency Transform VCA-NTD | PASS | Expected: 'R-NTD', Got: 'R-NTD' |
| Currency Transform VCG-EUR | PASS | Expected: '', Got: '' |
| Currency Transform VCG-XEU | PASS | Expected: 'R-EUR', Got: 'R-EUR' |
| Currency Transform VCJ-JPY | PASS | Expected: '', Got: '' |
| Currency Transform VCT-R-USD | PASS | Expected: 'R-USD', Got: 'R-USD' |
| Date Conversion '2024/12/19' | PASS | Expected: '2024-12-19', Got: '2024-12-19' |
| Date Conversion '2024/01/01' | PASS | Expected: '2024-01-01', Got: '2024-01-01' |
| Date Conversion '' | PASS | Expected: '', Got: '' |
| Date Conversion 'invalid' | PASS | Expected: 'invalid', Got: 'invalid' |
| V-VC00048 Mapping for VCP | PASS | Expected: 'VCT', Got: 'VCT' |
| Special Department VCT.1342G | PASS | Expected ShortcutDimCode14: 'VCT_TW0001', Got: 'VCT_TW0001' |
| Intercompany Code for VCP | PASS | Expected ShortcutDimCode3: 'VCT', Got: 'VCT' |
| Debit Description Content | FAIL | Expected to contain: 'Office supplies', Got: 'Test transaction' |
| Credit Description Content | PASS | Expected to contain remarks, Got: 'Payment to vendor' |
| Consolidated Credit Amount | PASS | Expected negative amount, Got: -3000.00 |
| Consolidated Description | PASS | Description: 'Consolidated payment' |
| Sample Payloads Report | PASS | Generated 5 samples |

## Failed Tests

### Debit Description Content
**Details:** Expected to contain: 'Office supplies', Got: 'Test transaction'

## Sample Payloads Generated

Generated 5 sample payloads for inspection.
See `bc_payload_samples.json` for detailed payload examples.
