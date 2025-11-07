# Session Validation Before Payment - Implementation

## Problem Solved

Users were being logged out after completing Paystack payment because their JWT tokens expired while they were on the Paystack payment page (2-5 minutes).

## Solution: Pre-Payment Session Validation

Instead of dealing with expired sessions after payment, we now **validate the session BEFORE** allowing users to initiate payment. If the session is expired or about to expire, users are prompted to re-login first.

---

## How It Works

### 1. Session Validation on Page Load

When user opens the purchase page:

```javascript
// Validates session immediately
const sessionValid = await api.ensureValidSession(false);

if (!sessionValid) {
  // Redirects to login if session expired
  return;
}
```

**User Experience:**

- Opens purchase page
- If session expired: Auto-redirected to login page
- If session valid: Can browse products and initiate payment

### 2. Session Validation Before Payment

When user clicks "Top Up" button:

```javascript
async function processTopUp(amount) {
  // Validate session first
  showToast("Validating session...", "info");

  const sessionValid = await api.ensureValidSession(true);

  if (!sessionValid) {
    // Shows alert: "Your session has expired. Please login again."
    // Redirects to login
    return;
  }

  // Session valid - proceed with payment
  showToast("Initializing payment with Paystack...", "info");
  // ... initialize Paystack payment
}
```

**User Experience:**

- Clicks "Top Up Wallet"
- Sees "Validating session..." message
- If expired: Alert shown → Redirected to login
- If valid: Redirected to Paystack payment page

### 3. Token Auto-Refresh

The `validateSession()` method calls `/api/profile/` which:

- Attempts to use current access token
- If expired, auto-refreshes using refresh token
- If refresh succeeds: Session valid ✅
- If refresh fails: Session invalid, requires re-login ❌

---

## New API Methods

### `api.validateSession()`

Tests if session is valid by making API call:

```javascript
const result = await api.validateSession();
// Returns: { valid: true, user: {...} }
// Or:      { valid: false, reason: 'Token expired', requiresLogin: true }
```

### `api.ensureValidSession(showAlert = true)`

Validates session and handles errors:

```javascript
const valid = await api.ensureValidSession(true);
// Returns: true if session valid
// Returns: false if session invalid (auto-redirects to login)
// Shows alert if showAlert = true
```

---

## User Flow Examples

### Scenario 1: Fresh Session (Token Valid)

```
User → Purchase Page
  ↓
Page loads → Session validation
  ↓
✅ Session valid
  ↓
User clicks "Top Up"
  ↓
Pre-payment validation
  ↓
✅ Session still valid
  ↓
Redirect to Paystack ✅
  ↓
User completes payment
  ↓
Returns to app ✅
  ↓
Verification credits wallet ✅
```

### Scenario 2: Expired Session (Token Expired)

```
User → Purchase Page
  ↓
Page loads → Session validation
  ↓
❌ Session expired (token refresh also failed)
  ↓
Auto-redirect to login page
  ↓
User must login again
  ↓
After login → Fresh session
  ↓
Can now proceed with payment ✅
```

### Scenario 3: Token About to Expire

```
User → Purchase Page
  ↓
Session valid (token still alive)
  ↓
User browses for 10 minutes
  ↓
User clicks "Top Up"
  ↓
Pre-payment validation
  ↓
Token expired, but refresh token still valid
  ↓
✅ Token auto-refreshed
  ↓
✅ Session valid
  ↓
Redirect to Paystack ✅
```

### Scenario 4: Session Expires During Browsing

```
User → Purchase Page (11:00 AM)
  ↓
Session valid
  ↓
User browses products for 20 minutes
  ↓
User clicks "Top Up" (11:20 AM)
  ↓
Pre-payment validation
  ↓
❌ Both access & refresh tokens expired
  ↓
Alert: "Your session has expired. Please login again."
  ↓
Redirect to login page
  ↓
User logs in → Fresh session
  ↓
Can now proceed with payment ✅
```

---

## Benefits

### 1. **No More Post-Payment Logout** ✅

- Users validate session BEFORE going to Paystack
- If session is going to expire, they re-login FIRST
- When they return from Paystack, session is still valid

### 2. **Better User Experience** ✅

- Clear messaging: "Validating session..."
- Immediate feedback if login required
- No surprise logouts after payment

### 3. **Token Auto-Refresh** ✅

- If access token expired but refresh token valid
- Session auto-refreshes transparently
- User doesn't even know it happened

### 4. **Early Detection** ✅

- Catches expired sessions on page load
- Catches expired sessions before payment
- Prevents wasted time on Paystack with expired session

### 5. **Idempotent & Safe** ✅

- Verification endpoint still works without auth (fallback)
- Session validation is non-destructive
- Multiple calls to `ensureValidSession()` are safe

---

## Testing Instructions

### Test 1: Normal Flow (Session Valid)

1. Login to your account
2. Go to purchase page
3. Click "Top Up Wallet"
4. **Expected**: See "Validating session..." → "Initializing payment..."
5. Complete payment on Paystack
6. **Expected**: Return to app, wallet credited, still logged in ✅

### Test 2: Expired Session on Page Load

1. Login to your account
2. Open DevTools → Application → Local Storage
3. Delete `access_token` and `refresh_token`
4. Refresh purchase page
5. **Expected**: Auto-redirected to login page ✅

### Test 3: Expired Session on Payment Click

1. Login to your account
2. Go to purchase page (page loads fine)
3. Open DevTools → Application → Local Storage
4. Delete `access_token` and `refresh_token`
5. Click "Top Up Wallet"
6. **Expected**:
   - See "Validating session..."
   - Alert: "Your session has expired. Please login again."
   - Redirected to login page ✅

### Test 4: Token Auto-Refresh

1. Login to your account
2. Wait for access token to expire (or manually delete it)
3. Keep refresh token intact
4. Click "Top Up Wallet"
5. **Expected**:
   - See "Validating session..."
   - Token auto-refreshes
   - Proceed to Paystack payment ✅

---

## Console Logs

You'll see these logs:

**On page load (session valid):**

```
Validating session on page load...
✅ Session valid on page load
```

**On page load (session expired):**

```
Validating session on page load...
Session validation failed: {status: 401, ...}
Session invalid on page load - redirecting to login
```

**Before payment (session valid):**

```
✅ Session validated - proceeding with payment
Initializing payment with Paystack...
```

**Before payment (session expired):**

```
Session validation failed: {status: 401, ...}
Session validation failed - aborting payment
```

**After payment return:**

```
✅ Payment verified: {status: "success", amount: 5000, ...}
✅ Wallet balance updated: 124000
```

---

## Files Modified

1. **`frontend/assets/js/api.js`**

   - Added `validateSession()` method
   - Added `ensureValidSession()` method

2. **`frontend/assets/js/purchase.js`**
   - Added session validation on page load
   - Added session validation before payment initialization

---

## Summary

**Before:**

```
User → Top Up → Paystack → Return → 💥 Logged Out (token expired)
```

**After:**

```
User → Top Up → ✅ Validate Session → Paystack → Return → ✅ Still Logged In
```

**If Session Expired:**

```
User → Top Up → ❌ Session Expired → Login → Top Up → Paystack → Return → ✅ Logged In
```

---

## Next Steps

1. **Test the fix**: Try topping up your wallet
2. **Test edge cases**: Try with expired tokens (manually delete from localStorage)
3. **Monitor logs**: Check browser console for validation messages
4. **Production**: Works even better in production (webhooks also work)

The session validation ensures users never waste time on Paystack only to find out their session expired when they return! 🎉
