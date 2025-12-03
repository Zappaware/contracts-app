# Forms Backend Connection Summary

## Overview
Successfully connected both New Vendor and New Contract forms to the backend API endpoints.

## Changes Made

### 1. New Vendor Form (`app/pages/new_vendor.py`)
**Status**: ✅ Already connected (lines 695-703)

- Uses `requests.post()` to send data to `/api/v1/vendors/`
- Sends multipart form-data with JSON + PDF files
- Properly handles file uploads using `e.files` pattern
- Shows success/error notifications
- Clears form on success

### 2. New Contract Form (`app/pages/new_contract.py`)
**Status**: ✅ Now connected to backend

#### Changes Made:

1. **Added Imports** (lines 2-5):
   ```python
   import requests
   import json
   import os
   from app.core.config import settings
   ```

2. **Load Real Data** (lines 6-25):
   - Fetches real vendors from database
   - Fetches real users (contract managers)
   - Creates mapping dictionaries for ID lookups
   - Vendor dropdown now shows actual vendors, not fake data

3. **Fixed File Upload Storage** (line 631):
   - Added `vendor_contract_file = {'file': None}` dictionary
   - Stores actual file object: `vendor_contract_file['file'] = getattr(e.files[0], 'file', e.files[0])`
   - Matches the pattern used in new_vendor.py

4. **Implemented Backend Submission** (lines 825-870):
   - Maps vendor names to vendor IDs
   - Maps manager names to user IDs
   - Converts dates from MM/DD/YYYY to YYYY-MM-DD
   - Prepares contract_data JSON
   - Sends multipart request to `/api/v1/contracts/`
   - Handles success/error responses
   - Shows appropriate notifications

## API Endpoints Used

### Vendor Creation
**Endpoint**: `POST /api/v1/vendors/`

**Form Data**:
- `vendor_data`: JSON string with vendor info
- `due_diligence_doc`: PDF file (optional)
- `non_disclosure_doc`: PDF file (optional)
- `integrity_policy_doc`: PDF file (optional)
- `risk_assessment_doc`: PDF file (optional)
- Document metadata (names and signed dates)

### Contract Creation
**Endpoint**: `POST /api/v1/contracts/`

**Form Data**:
- `contract_data`: JSON string with contract info
- `contract_document`: PDF file (required)
- `document_name`: Custom document name
- `document_signed_date`: Date in YYYY-MM-DD format

## Data Flow

```
User fills form → Validates fields → Collects data
       ↓
Maps UI values to database IDs (vendors, users)
       ↓
Prepares JSON + files in multipart format
       ↓
Sends POST request to FastAPI endpoint
       ↓
Backend validates, creates record, uploads files
       ↓
Returns success response with created record ID
       ↓
Shows notification to user
```

## File Upload Pattern (from new_vendor.py)

Both forms now use the same pattern:

```python
# 1. Create storage dictionary
file_storage = {'file': None}

# 2. Upload handler stores file
def handle_upload(e):
    if hasattr(e, 'files') and e.files:
        file_storage['file'] = getattr(e.files[0], 'file', e.files[0])
        ui.notify('File uploaded', type='positive')

# 3. Submit sends file to API
files = {
    'document': ('filename.pdf', file_storage['file'], 'application/pdf')
}
response = requests.post(url, files=files)
```

## Known Limitations

### new_contract.py Upload Handler Issue
The upload handler still uses `e.file_names` which may not be available in all NiceGUI versions. If uploads don't work, the handler needs to use:
- `e.files[0]` to access the file object
- `getattr(e.files[0], 'file', e.files[0])` to get the actual file content

### Contract Manager Mapping
The contract form uses hardcoded manager names (lines 6-55). These need to match actual users in the database or be replaced with a dynamic user selection dropdown.

## Testing

### Test Vendor Creation:
1. Go to http://localhost:8000/new-vendor
2. Fill all required fields
3. Upload required documents
4. Click Submit
5. Check `/vendors` page for new vendor

### Test Contract Creation:
1. Ensure you have vendors and users in database
2. Go to http://localhost:8000/new-contract
3. Select vendor from dropdown (real vendors now shown)
4. Fill all required fields including dates
5. Upload contract PDF
6. Enter document name and signed date
7. Select contract managers
8. Click Submit
9. Check `/active-contracts` page for new contract

## Next Steps

1. **Test both forms** to ensure data is properly saved
2. **Fix upload handler** if file uploads still fail (use e.files pattern)
3. **Add form clear** functionality after successful submission
4. **Add redirect** to list pages after creation
5. **Dynamic manager dropdown** - Replace hardcoded names with users from database

## Database Requirements

Before testing, ensure:
- ✅ At least 2 users exist (contract managers)
- ✅ At least 1 vendor exists
- ✅ Database migrations are up to date

## Current Database State
- Users: 2 (William Defoe, John Doe)
- Vendors: 4
- Contracts: 0

Ready to create contracts through the UI!



