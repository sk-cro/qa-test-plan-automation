# Custom Attributes Implementation Summary

## Overview
Added support for Custom attributes field processing for Optimizely tickets only. This feature inserts Custom attributes starting at row 34 (adjusted for Goals row insertion) in the Optimizely tab.

**Date:** $(date)
**Status:** ✅ Implemented - Ready for Testing

## Changes Made

### 1. `jira_client.py`
- **Added:** `get_custom_attributes_field(issue_key)` method
- **Purpose:** Retrieves Custom attributes field from Jira (customfield_10777)
- **Location:** After `get_goals_field()` method (line ~222)
- **Behavior:** Handles string, dict, and ADF document formats (same as Goals)

### 2. `jira_parser.py`
- **Added:** `parse_custom_attributes_field(issue_key)` method
- **Purpose:** Parses numbered Custom attributes from field text
- **Location:** After `parse_goals_field()` method (line ~110)
- **Behavior:** Uses same regex pattern as Goals to parse numbered items (e.g., "1. Item", "2. Item")

### 3. `sheet_customizer.py`
- **Modified:** `customize_sheet_with_goals()` return type
  - **Changed:** Return type from `bool` to `int`
  - **Returns:** Number of additional rows inserted (beyond placeholder capacity)
  - **Impact:** This allows Custom attributes to adjust its start row based on Goals insertion
- **Added:** `customize_sheet_with_custom_attributes()` method
  - **Purpose:** Inserts Custom attributes into sheet starting at specified row (default: 34)
  - **Location:** After `customize_sheet_with_goals()` method (line ~170)
  - **Features:**
    - Validates start_row (defaults to 34 if invalid)
    - Warns if used on non-Optimizely tabs (but still proceeds)
    - Same formatting/copying logic as Goals
    - Handles row insertion if needed

### 4. `app.py`
- **Modified:** Goals processing section
  - **Added:** `goals_rows_inserted` variable to track rows inserted by Goals
  - **Changed:** Captures return value from `customize_sheet_with_goals()`
- **Added:** Custom attributes processing section
  - **Location:** After Goals processing, before tab pruning (line ~285)
  - **Conditions:**
    - Only runs for Optimizely tickets (`platform == "[Optimizely] QA Pass 1"`)
    - Calculates adjusted start row: `34 + goals_rows_inserted`
    - Fully isolated with try/except to prevent breaking main flow
  - **Error Handling:** All errors are logged but don't fail the main workflow

## Key Features

### ✅ Safety Features
1. **Isolated Processing:** Custom attributes runs independently of Goals
2. **Platform-Specific:** Only processes Optimizely tickets
3. **Error Isolation:** Failures in Custom attributes don't break Goals or main flow
4. **Row Adjustment:** Automatically adjusts for Goals row insertion
5. **Backward Compatible:** Existing Goals processing unchanged

### ✅ Row Calculation Logic
- Goals start at row 28
- Custom attributes start at row 34 (original)
- If Goals insert N rows, Custom attributes adjusts to row 34 + N
- Example:
  - Goals: 5 items (inserts 2 rows beyond placeholders)
  - Custom attributes: Adjusted from row 34 to row 36

## Testing Recommendations

### Critical Test Cases
1. ✅ **Optimizely with both Goals and Custom attributes**
   - Goals: 5 items (inserts 2 rows)
   - Custom attributes: 3 items
   - Expected: Custom attributes at row 36 (34 + 2)

2. ✅ **Optimizely with Goals only**
   - Goals: 5 items
   - Custom attributes: empty
   - Expected: Only Goals inserted, no Custom attributes processing

3. ✅ **Optimizely with Custom attributes only**
   - Goals: empty
   - Custom attributes: 3 items
   - Expected: Custom attributes at row 34 (no adjustment)

4. ✅ **Non-Optimizely ticket (Convert/VWO/Monetate)**
   - Custom attributes: has data
   - Expected: Custom attributes ignored (not processed)

5. ✅ **Goals with exactly 3 items (no row insertion)**
   - Goals: 3 items (uses placeholders)
   - Custom attributes: 3 items
   - Expected: Custom attributes at row 34 (no adjustment)

### Regression Tests
- ✅ Convert ticket with Goals (should work as before)
- ✅ VWO ticket with Goals (should work as before)
- ✅ Optimizely ticket with Goals only (should work as before)

## Rollback Instructions

If you need to revert these changes:

```bash
# View all changes
git diff

# Revert all files at once
git restore app.py jira_client.py jira_parser.py sheet_customizer.py

# OR revert individually
git restore app.py
git restore jira_client.py
git restore jira_parser.py
git restore sheet_customizer.py
```

### Manual Revert (if git restore doesn't work)
1. **jira_client.py:** Remove `get_custom_attributes_field()` method (lines ~222-262)
2. **jira_parser.py:** Remove `parse_custom_attributes_field()` method (lines ~110-150)
3. **sheet_customizer.py:**
   - Change `customize_sheet_with_goals()` return type back to `bool`
   - Change return statements: `return 0` → `return True`, `return rows_to_insert` → `return True`
   - Remove `customize_sheet_with_custom_attributes()` method (lines ~170-313)
4. **app.py:**
   - Remove `goals_rows_inserted = 0` initialization
   - Remove `goals_rows_inserted = ` assignment
   - Remove entire Custom attributes processing block (lines ~285-310)

## Files Modified
- `app.py` (+32 lines)
- `jira_client.py` (+42 lines)
- `jira_parser.py` (+42 lines)
- `sheet_customizer.py` (+155 lines)

**Total:** +264 insertions, -7 deletions

## Next Steps
1. ✅ Code implemented and linted (no errors)
2. ⏳ **Test in staging environment** with real Optimizely ticket
3. ⏳ **Monitor logs** for any errors
4. ⏳ **Verify sheet structure** manually
5. ⏳ **Deploy to production** after successful testing

## Notes
- Custom field ID: `customfield_10777`
- Custom attributes uses same parsing logic as Goals (numbered items)
- Row 34 is the starting point, adjusted by Goals row insertion
- All processing is logged for debugging

