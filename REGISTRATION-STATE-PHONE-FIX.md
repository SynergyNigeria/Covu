# Registration State & Phone Format Fix

## Date: October 22, 2025

## Issues Identified

### Backend Error Response:

```json
{
  "status": 400,
  "message": "Request failed",
  "errors": {
    "phone_number": [
      "Phone number must be in Nigerian format: +234XXXXXXXXXX or 0XXXXXXXXXX"
    ],
    "state": ["\"Cross River\" is not a valid choice."]
  }
}
```

## Root Causes

### 1. State Format Mismatch

**Frontend sends**: `"Cross River"` (display format with spaces and capitals)

**Backend expects**: `"cross_river"` (database format with lowercase and underscores)

**Backend State Choices** (from `users/models.py`):

```python
NIGERIAN_STATES = [
    ("abia", "Abia"),
    ("adamawa", "Adamawa"),
    ("akwa_ibom", "Akwa Ibom"),
    ("anambra", "Anambra"),
    ("bauchi", "Bauchi"),
    ("bayelsa", "Bayelsa"),
    ("benue", "Benue"),
    ("borno", "Borno"),
    ("cross_river", "Cross River"),  # ← Key is "cross_river", not "Cross River"
    ("delta", "Delta"),
    ("ebonyi", "Ebonyi"),
    ("edo", "Edo"),
    ("ekiti", "Ekiti"),
    ("enugu", "Enugu"),
    ("fct", "Federal Capital Territory"),
    ("gombe", "Gombe"),
    # ... etc
]
```

The first value in each tuple is the **database key**, the second is the **display name**.

### 2. Phone Number Format

**Backend Regex**: `r"^(\+234|0)[789][01]\d{8}$"`

This means:

- Start with `+234` OR `0`
- Followed by carrier prefix: `7`, `8`, or `9`
- Followed by network code: `0` or `1`
- Followed by exactly 8 more digits

**Valid Examples**:

- `08012345678` ✅ (0 + 8 + 0 + 12345678)
- `+2348012345678` ✅ (+234 + 8 + 0 + 12345678)
- `07012345678` ✅ (0 + 7 + 0 + 12345678)
- `09012345678` ✅ (0 + 9 + 0 + 12345678)

**Invalid Examples**:

- `08112345678` ❌ (8 + 1 is not valid, should be 8 + 0 or 8 + 1 with different pattern)
- `0123456789` ❌ (starts with 1, not 7/8/9)
- `234 801 234 5678` ❌ (has spaces)

## Solutions Applied

### Fix 1: State Mapping

Added state name conversion in `registration.js`:

```javascript
// Convert state name to backend format (lowercase with underscores)
const stateMapping = {
  Abia: "abia",
  Adamawa: "adamawa",
  "Akwa Ibom": "akwa_ibom",
  Anambra: "anambra",
  Bauchi: "bauchi",
  Bayelsa: "bayelsa",
  Benue: "benue",
  Borno: "borno",
  "Cross River": "cross_river", // ← This fixes your issue
  Delta: "delta",
  Ebonyi: "ebonyi",
  Edo: "edo",
  Ekiti: "ekiti",
  Enugu: "enugu",
  FCT: "fct",
  Gombe: "gombe",
  Imo: "imo",
  Jigawa: "jigawa",
  Kaduna: "kaduna",
  Kano: "kano",
  Katsina: "katsina",
  Kebbi: "kebbi",
  Kogi: "kogi",
  Kwara: "kwara",
  Lagos: "lagos",
  Nasarawa: "nasarawa",
  Niger: "niger",
  Ogun: "ogun",
  Ondo: "ondo",
  Osun: "osun",
  Oyo: "oyo",
  Plateau: "plateau",
  Rivers: "rivers",
  Sokoto: "sokoto",
  Taraba: "taraba",
  Yobe: "yobe",
  Zamfara: "zamfara",
};

// Convert state to backend format
userData.state =
  stateMapping[userData.state] ||
  userData.state.toLowerCase().replace(/\s+/g, "_");
```

### Fix 2: Phone Number Normalization

Added phone number conversion before sending to backend:

```javascript
// Normalize phone number for backend
// Backend expects: (\+234|0)[789][01]\d{8}
// Convert any format to 0XXXXXXXXXX format
let normalizedPhone = userData.phone.replace(/\s/g, ""); // Remove spaces

// Handle different input formats
if (normalizedPhone.startsWith("+234")) {
  normalizedPhone = "0" + normalizedPhone.substring(4); // +2348012345678 -> 08012345678
} else if (normalizedPhone.startsWith("234")) {
  normalizedPhone = "0" + normalizedPhone.substring(3); // 2348012345678 -> 08012345678
}
// If it already starts with 0, keep it as is

console.log("Sending phone number:", normalizedPhone); // Debug log
```

**Conversion Examples**:

- Input: `+234 801 234 5678` → Output: `08012345678` ✅
- Input: `234 801 234 5678` → Output: `08012345678` ✅
- Input: `0801 234 5678` → Output: `08012345678` ✅

## Files Modified

### `frontend/assets/js/registration.js`

1. **Lines 240-295**: Added state mapping dictionary and conversion logic
2. **Lines 360-376**: Added phone number normalization before API call

## Testing Instructions

1. **Refresh Registration Page**

   ```
   Press Ctrl + Shift + R
   ```

2. **Test with Cross River State**

   ```
   Full Name: Test User
   Email: crossriver@test.com
   Phone: 08012345678
   State: Cross River  ← This should work now!
   LGA: [Any LGA]
   Password: TestPass123
   Confirm: TestPass123
   ✓ Terms
   ```

3. **Test with Different Phone Formats**

   - `08012345678` ✅
   - `+2348012345678` ✅
   - `234 801 234 5678` ✅
   - `0801 234 5678` ✅

4. **Check Console**
   - Look for: `Sending phone number: 08012345678`
   - This confirms normalization is working

## Expected Result

✅ **Success Modal Appears**:

- "Welcome to Covu! 🎉"
- "Nigeria's Greatest & Safest Suburban Marketplace"
- 5-second countdown
- Auto-redirect to shop-list.html

## Valid Nigerian Phone Numbers

The backend accepts these carrier prefixes:

- **MTN**: 0803, 0806, 0810, 0813, 0814, 0816, 0903, 0906
- **Glo**: 0805, 0807, 0811, 0815, 0905
- **Airtel**: 0802, 0808, 0812, 0901, 0907
- **9mobile**: 0809, 0817, 0818, 0909

All must follow format: `0[789][01]XXXXXXXX`

## Debugging

If you still get errors:

1. **Check Console Log**:

   ```
   Sending phone number: 08012345678
   ```

   Verify the phone format is correct

2. **Check Network Tab**:

   - Go to Network → register/ request
   - Check "Payload" tab
   - Verify `state: "cross_river"` (not "Cross River")
   - Verify `phone_number: "08012345678"` (no spaces)

3. **Common Issues**:
   - Phone missing [0/1] after carrier: Use 0801, not 0831
   - State has spaces: Should be "cross_river", not "Cross River"
   - Email already exists: Use unique email
   - Phone already exists: Use unique phone

## Next Steps

- [ ] Test registration with Cross River state
- [ ] Test with other multi-word states (Akwa Ibom, FCT, etc.)
- [ ] Verify success modal appears
- [ ] Confirm auto-redirect works
- [ ] Move to Phase 3 implementation

## Related Files

- `Backend/users/models.py` - State choices and phone regex
- `frontend/assets/js/registration.js` - Form handling
- `frontend/templates/register.html` - Success modal HTML
- `CORS-AND-REGISTRATION-FIX.md` - Previous fixes
