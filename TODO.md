# Kickbox Email Verification Integration Plan

## Information Gathered:
- Two main banking system files: `school_no_blockchain.py` and `school.py`
- Current ACCOUNTS table structure: account_no, name, phone_num, pin, balance, account_type, created_at
- No email field currently exists in the database
- Systems use MySQL for data storage with proper connection handling
- Both systems have similar account management functionality

## Plan:

### Phase 1: Database Schema Updates ✅
1. Add email column to ACCOUNTS table in both files
2. Add email_verified column to track verification status
3. Update init_database() functions in both files

### Phase 2: Kickbox API Integration ✅
1. Create kickbox_email_verification.py module with:
   - Email validation using Kickbox API
   - Handle API responses (valid, invalid, risky, etc.)
   - Rate limiting and error handling
2. Install required dependencies (requests library)

### Phase 3: Account Opening Enhancement
1. Modify account_open() function to:
   - Accept email parameter
   - Verify email through Kickbox API
   - Store email and verification status
   - Make email optional or required based on user choice

### Phase 4: User Interface Updates
1. Add email input during account opening
2. Add email verification option in login menu
3. Add email management options (update email, re-verify)
4. Display email verification status in account details

### Phase 5: Testing and Validation
1. Test email verification with valid/invalid emails
2. Test database operations with new email fields
3. Test user flow with email verification

## Dependent Files to be Edited:
- school_no_blockchain.py (main file without blockchain)
- school.py (blockchain version)
- kickbox_email_verification.py (new module)
- requirements.txt (new file for dependencies)

## Follow-up Steps:
1. Install requests library for API calls
2. Test the integration with various email formats
3. Handle Kickbox API rate limits and errors gracefully
4. Update documentation with new features
